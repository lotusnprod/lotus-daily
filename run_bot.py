import argparse
import json
import secrets

from daily_lotus.formatter import MessageTooLongError, compose_message
from daily_lotus.log import record_post_extended, was_posted
from daily_lotus.mastodon_client import post_to_mastodon
from daily_lotus.wikidata_query import get_candidate_qids, get_molecule_details


def run(dry_run: bool = False, use_cache: bool = False):
    if use_cache:
        print("📦 Loading candidate compound QIDs from cache (candidates.json)...")
        with open("candidates.json") as f:
            qids = json.load(f)
    else:
        print("📡 Fetching candidate compound QIDs from Wikidata...")
        qids = get_candidate_qids()

    secrets.SystemRandom().shuffle(qids)

    for qid in qids:
        print(f"🔍 Trying compound {qid}...")
        details = get_molecule_details(qid)

        if not details:
            continue

        compound_qid = details["compound_qid"]
        taxon_qid = details["taxon_qid"]

        if was_posted(compound_qid, taxon_qid):
            print(f"⏩ Already posted {compound_qid} + {taxon_qid}, skipping.")
            continue

        try:
            message = compose_message(
                compound=details["compound"],
                compound_qid=compound_qid,
                taxon=details["taxon"],
                taxon_qid=taxon_qid,
                reference=details["reference"],
                reference_qid=details["reference_qid"],
                taxon_emoji=details["taxon_emoji"],
                kingdom_label=details["kingdom_label"],
            )
        except MessageTooLongError as e:
            print(str(e))
            print("⏭️ Skipping this compound-taxon pair due to length constraints.")
            continue

        # Set alt-text for both images
        image_alt_text = f"2D structure of {details['compound']} displaying molecular bonds."
        taxon_image_alt_text = f"Image of {details['taxon']}, the taxon in which the compound is found."

        if dry_run:
            print("🧪 Dry run mode — not posting to Mastodon.")
            print("------ Message ------")
            print(message)
            print("🖼 Molecule image URL:", details.get("image_url"))
            print("🖼 Taxon image URL:", details.get("taxon_image_url"))
            print("🖼 Molecule Alt-Text:", image_alt_text)
            print("🖼 Taxon Alt-Text:", taxon_image_alt_text)
        else:
            print("🟢 Posting:")
            print(message)
            status = post_to_mastodon(
                message,
                image_url=details.get("image_url"),
                taxon_image_url=details.get("taxon_image_url"),
                image_alt_text=image_alt_text,  # Pass alt-text for the molecule image
                taxon_image_alt_text=taxon_image_alt_text,  # Pass alt-text for the taxon image
            )
            toot_id = str(status["id"]) if status else None

            record_post_extended(
                compound_qid=compound_qid,
                taxon_qid=taxon_qid,
                reference_qid=details["reference_qid"],
                compound_label=details["compound"],
                taxon_label=details["taxon"],
                reference_label=details["reference"],
                toot_id=toot_id,
            )
            print("✅ Posted and logged.")
        break
    else:
        print("❌ No new unique compound-taxon pair found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Daily LOTUS bot.")
    parser.add_argument("--dry-run", action="store_true", help="Run the bot without posting to Mastodon.")
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Load candidate QIDs from candidates.json instead of querying Wikidata.",
    )
    args = parser.parse_args()

    run(dry_run=args.dry_run, use_cache=args.use_cache)
