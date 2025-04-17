import random

from daily_lotus.formatter import compose_message
from daily_lotus.log import record_post, was_posted
from daily_lotus.mastodon_client import post_to_mastodon
from daily_lotus.wikidata_query import get_candidate_qids, get_molecule_details


def run():
    print("📡 Fetching candidate compound QIDs...")
    qids = get_candidate_qids(limit=1000)
    random.shuffle(qids)

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

        message = compose_message(
            compound=details["compound"],
            compound_qid=compound_qid,
            taxon=details["taxon"],
            taxon_qid=taxon_qid,
            reference=details["reference"],
            reference_qid=details["reference_qid"],
            taxon_emoji=details["taxon_emoji"],
            kingdom_label=details["kingdom_label"],
            # query_url=details["query_url"]
        )

        print("🟢 Posting:\n", message)
        post_to_mastodon(message, image_url=details.get("image_url"), taxon_image_url=details.get("taxon_image_url"))

        record_post(compound_qid, taxon_qid)
        print("✅ Posted and logged.")
        break
    else:
        print("❌ No new unique compound-taxon pair found.")


if __name__ == "__main__":
    run()
