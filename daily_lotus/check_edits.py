import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, cast

from daily_lotus.log import ExtendedPostRecord, load_extended_log
from daily_lotus.mastodon_client import post_to_mastodon
from daily_lotus.wikidata_query import (
    fetch_current_labels,
    find_p703_removal_editor,
    get_label_change_editor,
    get_reference_label_change_editor,
    occurrence_still_exists,
)

LOG_FILE = Path("posted_log_extended.json")
DEBUG_LOG_FILE = Path("posted_log_extended.dryrun.json")


def format_unified_summary(
    changes: list[tuple[str, str, str]],
    editors: list[str],
    deleted: bool,
    compound_label: str,
    taxon_label: str,
    compound_qid: str,
) -> str:
    lines = []

    if deleted:
        lines.append("💀 This occurrence is no longer listed on Wikidata.\n")
        lines.append(f"The claim that **{compound_label}** was found in **{taxon_label}** has been removed.\n")
    else:
        lines.append("🛠️ This occurrence was edited on Wikidata:")

    for field, old, new in changes:
        label = {"compound": "compound", "taxon": "taxon", "reference": "reference"}[field]
        lines.append(f"• {label} label changed: “{old}” → “{new}”")

    if editors:
        mentions = ", ".join(f"[{e}](https://www.wikidata.org/wiki/User:{e})" for e in sorted(set(editors)))
        lines.append(f"\n🧑‍🔧 Edited by: {mentions}")

    lines.append(f"\n✏️ [Improve it on Wikidata](https://www.wikidata.org/wiki/{compound_qid}#P703)")
    return "\n".join(lines)


def initialize_last_checked_labels(entry: ExtendedPostRecord) -> None:
    """Ensure the entry has the *_label_last_checked fields initialized."""
    if "compound_label_last_checked" not in entry:
        entry["compound_label_last_checked"] = entry.get("compound_label", "")
    if "taxon_label_last_checked" not in entry:
        entry["taxon_label_last_checked"] = entry.get("taxon_label", "")
    if "reference_label_last_checked" not in entry:
        entry["reference_label_last_checked"] = entry.get("reference_label", "")


def was_occurrence_deleted(entry: ExtendedPostRecord, since: datetime) -> Optional[str]:
    if not occurrence_still_exists(entry["compound_qid"], entry["taxon_qid"]):
        print("❌ Occurrence was deleted from Wikidata!")
        editor = find_p703_removal_editor(entry["compound_qid"], entry["taxon_qid"], since)
        if editor:
            print(f"👤 P703 deleted by: {editor}")
        return editor
    return None


def get_label_changes(entry: ExtendedPostRecord, since: datetime) -> tuple[list[tuple[str, str, str]], list[str]]:
    changes = []
    editors = []
    result = fetch_current_labels(entry["compound_qid"], entry["taxon_qid"], entry["reference_qid"])

    # Compare live labels with stored last checked labels
    for field, qid, last_checked_label, new_label_fn, editor_fn in [
        (
            "compound",
            entry["compound_qid"],
            entry["compound_label_last_checked"],
            lambda r: r["compound_label"],
            get_label_change_editor,
        ),
        (
            "taxon",
            entry["taxon_qid"],
            entry["taxon_label_last_checked"],
            lambda r: r["taxon_label"],
            get_label_change_editor,
        ),
        (
            "reference",
            entry["reference_qid"],
            entry["reference_label_last_checked"],
            lambda r: r["reference_label"],
            get_reference_label_change_editor,
        ),
    ]:
        # Handle None for last_checked_label
        if last_checked_label is None:
            last_checked_label = ""

        new_label = new_label_fn(result)

        # Skip change if no actual change in label
        if new_label == last_checked_label:
            continue

        # Otherwise, it's a detected change
        changes.append((field, last_checked_label, new_label))
        editor = editor_fn(qid, last_checked_label, since)
        if editor:
            editors.append(editor)

        # Update the 'last_checked' label after detecting a change
        if field == "compound":
            entry["compound_label_last_checked"] = new_label
        elif field == "taxon":
            entry["taxon_label_last_checked"] = new_label
        elif field == "reference":
            entry["reference_label_last_checked"] = new_label

    return changes, editors


def process_entry(entry: ExtendedPostRecord, dry_run: bool) -> bool:
    print(f"\n🔎 Checking {entry['compound_qid']} + {entry['taxon_qid']} + {entry['reference_qid']}")

    if not entry.get("toot_id"):
        print("⚠️ No toot_id available, skipping.")
        return False

    # Initialize missing fields for the first run
    initialize_last_checked_labels(entry)

    since_str = cast(str, entry.get("last_reply_timestamp", entry["timestamp"]))
    since = datetime.fromisoformat(since_str).replace(tzinfo=timezone.utc)

    editors: list[str] = []
    changes: list[tuple[str, str, str]] = []

    deleted_by = was_occurrence_deleted(entry, since)
    deleted = deleted_by is not None
    if deleted_by is not None:
        editors.append(deleted_by)

    label_changes, label_editors = get_label_changes(entry, since)
    changes.extend(label_changes)
    editors.extend(label_editors)

    if not deleted and not changes:
        print("✅ No changes found.")
        return False

    if changes:
        print(f"✏️ Detected edits: {changes}")
    if editors:
        print(f"👤 Edited by: {', '.join(editors)}")

    reply = format_unified_summary(
        changes,
        editors,
        deleted,
        compound_label=entry["compound_label"],
        taxon_label=entry["taxon_label"],
        compound_qid=entry["compound_qid"],
    )
    print("📣 Replying with:\n", reply)

    if not dry_run:
        post_to_mastodon(reply, in_reply_to_id=entry["toot_id"])
        entry["last_reply_timestamp"] = datetime.now(tz=timezone.utc).isoformat()
    else:
        print("💤 Dry run: not posting to Mastodon.")

    return True


def check_edits(dry_run: bool = False) -> None:
    print("🔍 Checking for edits to previously posted occurrences...")
    log = load_extended_log()
    changed = False

    for raw_entry in log:
        entry = cast(ExtendedPostRecord, raw_entry)
        if process_entry(entry, dry_run=dry_run):
            changed = True

    if changed:
        if dry_run:
            print("📝 Dry run mode: would update log with:")
            print(json.dumps(log, indent=2))
            DEBUG_LOG_FILE.write_text(json.dumps(log, indent=2))
            print(f"🐛 Debug log written to: {DEBUG_LOG_FILE}")
        else:
            LOG_FILE.write_text(json.dumps(log, indent=2))
            print("📝 Updated log with new reply timestamps.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check for Wikidata edits and reply on Mastodon.")
    parser.add_argument("--dry-run", action="store_true", help="Print reply messages without posting to Mastodon.")
    args = parser.parse_args()
    check_edits(dry_run=args.dry_run)
