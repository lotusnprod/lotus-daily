class MessageTooLongError(ValueError):
    def __init__(self) -> None:
        super().__init__("🧨 Message too long even after all shortening steps.")


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
        return "an" if word and word[0].lower() in "aeiou" else "a"

    article = choose_article(kingdom_label)

    full_reference = f"{reference} [https://www.wikidata.org/wiki/{reference_qid}]"
    short_reference = f"[https://www.wikidata.org/wiki/{reference_qid}]"

    # Footer and hashtags defined separately
    footer = (
        f"✏️ This occurrence is available for curation on Wikidata "
        f"[https://www.wikidata.org/wiki/{compound_qid}#P703]. If you spot an error, feel free to improve it!"
    )
    hashtags = "#LOTUS #Wikidata #LinkedOpenData"

    # Full message with everything
    message = (
        "📣 Natural Product Occurrence of the Day\n\n"
        f"🧪 {compound} [https://www.wikidata.org/wiki/{compound_qid}] is a molecule\n"
        f"found in {article} {taxon_emoji} {kingdom_label}, {taxon} [https://www.wikidata.org/wiki/{taxon_qid}]\n"
        f"📚 according to: {full_reference}\n\n"
        f"{footer}\n\n"
        f"#DailyNP #OpenScience {hashtags}"
    )

    if len(message) <= 500:
        return message

    # Fallback 1 — Remove hashtags
    message_no_hashtags = message.replace(f" {hashtags}", "")
    if len(message_no_hashtags) <= 500:
        print("🧪 Removed hashtags")
        print(f"Length: {len(message_no_hashtags)}")
        return message_no_hashtags

    # Fallback 2 — Shorten reference
    message_short_ref = message_no_hashtags.replace(full_reference, short_reference)
    if len(message_short_ref) <= 500:
        print(f"🧪 Removed # and shortened reference to {short_reference}")
        print(f"Length: {len(message_short_ref)}")
        return message_short_ref

    raise MessageTooLongError()
