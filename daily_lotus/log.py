import json
import os
from datetime import datetime
from typing import Optional, TypedDict, cast

LOG_FILE = "posted_log.json"
EXTENDED_LOG_FILE = "posted_log_extended.json"


def load_log() -> list[tuple[str, str]]:
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE) as f:
        data = json.load(f)
        return [tuple(item) for item in data]  # Convert list[list[str]] → list[tuple[str, str]]


def was_posted(compound_qid: str, taxon_qid: str) -> bool:
    posted = load_log()
    return (compound_qid, taxon_qid) in posted


def record_post(compound_qid: str, taxon_qid: str) -> None:
    posted = load_log()
    posted.append((compound_qid, taxon_qid))  # Use tuple

    with open(LOG_FILE, "w") as f:
        json.dump(posted, f, indent=2)


class PostRecord(TypedDict):
    compound_qid: str
    taxon_qid: str
    reference_qid: str
    compound_label: str
    taxon_label: str
    reference_label: str
    toot_id: Optional[str]
    timestamp: str


class ExtendedPostRecord(PostRecord, total=False):  # optional keys go here
    last_reply_timestamp: Optional[str]
    compound_label_last_checked: Optional[str]
    taxon_label_last_checked: Optional[str]
    reference_label_last_checked: Optional[str]
    p703_exists_last_checked: Optional[bool]


def load_extended_log() -> list[PostRecord]:
    if not os.path.exists(EXTENDED_LOG_FILE):
        return []
    with open(EXTENDED_LOG_FILE) as f:
        return cast(list[PostRecord], json.load(f))


def record_post_extended(
    compound_qid: str,
    taxon_qid: str,
    reference_qid: str,
    compound_label: str,
    taxon_label: str,
    reference_label: str,
    toot_id: Optional[str],
) -> None:
    log = load_extended_log()
    log.append({
        "compound_qid": compound_qid,
        "taxon_qid": taxon_qid,
        "reference_qid": reference_qid,
        "compound_label": compound_label,
        "taxon_label": taxon_label,
        "reference_label": reference_label,
        "toot_id": toot_id,
        "timestamp": datetime.utcnow().isoformat(),
    })
    with open(EXTENDED_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)
