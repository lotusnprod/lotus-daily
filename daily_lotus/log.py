import json
import os

LOG_FILE = "posted_log.json"


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
