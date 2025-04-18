import json
import time
from pathlib import Path

from daily_lotus.wikidata_query import get_candidate_qids, get_molecule_details

OUTPUT_PATH = Path("gallery.json")
MAX_ENTRIES = 5  # Change or set to None to fetch all
SLEEP_SECONDS = 1.0  # Respectful pause between queries


def main():
    qids = get_candidate_qids()
    print(f"✅ Found {len(qids)} candidate QIDs")

    gallery_data = []
    for i, qid in enumerate(qids[:MAX_ENTRIES] if MAX_ENTRIES else qids):
        print(f"🔄 [{i + 1}/{len(qids)}] Processing {qid}")
        try:
            details = get_molecule_details(qid)
            if details:
                gallery_data.append(details)
                print(f"✔️ Added {details['compound']} from {details['taxon']}")
            else:
                print(f"⚠️ No valid data for {qid}")
        except Exception as e:
            print(f"❌ Error processing {qid}: {e}")
        time.sleep(SLEEP_SECONDS)

    print(f"💾 Writing {len(gallery_data)} entries to {OUTPUT_PATH}")
    OUTPUT_PATH.write_text(json.dumps(gallery_data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
