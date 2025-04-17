def compose_message(
    compound: str,
    compound_qid: str,
    taxon: str,
    taxon_qid: str,
    reference: str,
    reference_qid: str,
    taxon_emoji: str,
    kingdom_label: str,
) -> str:
    def choose_article(word: str) -> str:
        return "an" if word[0] in "aeiou" else "a"

    article = choose_article(kingdom_label)
    wikidata_edit_link = f"https://www.wikidata.org/wiki/{compound_qid}#P703"

    return (
        "📣 Natural Product Occurrence of the Day\n\n"
        f"🧪 {compound} [https://www.wikidata.org/wiki/{compound_qid}] is a molecule\n"
        f"found in {article} {taxon_emoji} {kingdom_label}, "
        f"{taxon} [https://www.wikidata.org/wiki/{taxon_qid}]\n"
        f"📚 according to: {reference} [https://www.wikidata.org/wiki/{reference_qid}]"
        "\n\n"
        f"✏️ This occurrence is curated in the frame of the LOTUS Initiative and is available on Wikidata [{wikidata_edit_link}]. "
        f"If you spot an error, feel free to improve it!"
        "\n\n"
        "#DailyNP #NaturalProducts #LOTUS #Wikidata #OpenScience #LinkedOpenData\n"
    )
