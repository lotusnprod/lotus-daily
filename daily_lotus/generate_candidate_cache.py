import json

from daily_lotus.wikidata_query import get_candidate_qids


def main() -> None:
    print("🧠 Fetching all candidate compound QIDs from Wikidata...")
    qids = get_candidate_qids()
    print(f"✅ Retrieved {len(qids)} candidates.")

    with open("candidates.json", "w") as f:
        json.dump(qids, f, indent=2)

    print("💾 Saved to candidates.json")


if __name__ == "__main__":
    main()
