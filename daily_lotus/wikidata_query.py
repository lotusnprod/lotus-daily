import secrets
import urllib.parse
from typing import Optional, cast

from SPARQLWrapper import JSON, SPARQLWrapper

WD_ENDPOINT = "https://query.wikidata.org/sparql"


def get_candidate_qids(limit: int = 1000) -> list[str]:
    query = f"""
    SELECT DISTINCT ?compound WHERE {{
      ?compound wdt:P703 ?taxon ;
                wdt:P233 ?smiles .
      ?taxon wdt:P18 ?image .
    }}
    LIMIT {limit}
    """
    sparql = SPARQLWrapper(WD_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    raw = sparql.query().convert()
    data = cast(dict, raw)
    results = data["results"]["bindings"]
    return [row["compound"]["value"].split("/")[-1] for row in results]


def get_molecule_details(qid: str) -> Optional[dict]:
    query = f"""
    SELECT ?compoundLabel ?compound ?taxon ?taxonLabel ?reference ?referenceLabel ?smiles ?taxon_image ?kingdom ?kingdomLabel WHERE {{
    BIND(wd:{qid} AS ?compound)

    ?compound wdt:P233 ?smiles .

    ?compound p:P703 ?statement .
    ?statement ps:P703 ?taxon ;
                prov:wasDerivedFrom ?refnode .
    ?refnode pr:P248 ?reference .

    ?taxon wdt:P18 ?taxon_image .

    ?taxon wdt:P171* ?kingdom .
    FILTER(?kingdom IN (
        wd:Q756,         # Plantae
        wd:Q764,    # Fungi
        wd:Q729,          # Animalia
        wd:Q10876      # Bacteria
    ))

    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 10
    """

    sparql = SPARQLWrapper(WD_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    raw = sparql.query().convert()
    data = cast(dict, raw)
    results = data["results"]["bindings"]
    if not results:
        return None

    row = secrets.choice(results)  # support multiple taxon hits

    kingdom_label = row.get("kingdomLabel", {}).get("value", "")
    kingdom_qid = row.get("kingdom", {}).get("value", "").split("/")[-1]
    print(f"🔎 Found kingdom: {kingdom_label}")
    print(f"🔎 Found kingdom QID: {kingdom_qid}")

    taxon_emoji = {
        "Q756": "🌿",
        "Q764": "🍄",
        "Q729": "🐛",
        "Q10876": "🦠",
    }.get(kingdom_qid, "🧬")  # default emoji

    def extract_val(field: str) -> str:
        val = row.get(field, {})
        if isinstance(val, dict):
            value = val.get("value")
            return str(value) if value is not None else ""
        return ""

    def extract_qid(field: str) -> str:
        val = row.get(field, {})
        if isinstance(val, dict):
            uri = val.get("value")
            if isinstance(uri, str):
                return uri.split("/")[-1]
        return "unknown"

    smiles = extract_val("smiles")
    image_url = (
        f"https://dev.api.naturalproducts.net/latest/depict/2D?"
        f"smiles={urllib.parse.quote(smiles)}&width=300&height=200"
        f"&toolkit=rdkit&rotate=0&CIP=false&unicolor=false"
    )

    return {
        "compound": extract_val("compoundLabel"),
        "compound_qid": extract_qid("compound"),
        "taxon": extract_val("taxonLabel"),
        "taxon_qid": extract_qid("taxon"),
        "reference": extract_val("referenceLabel") or "an unknown reference",
        "reference_qid": extract_qid("reference"),
        "smiles": smiles,
        "image_url": image_url,
        "taxon_image_url": extract_val("taxon_image"),
        "taxon_emoji": taxon_emoji,
        "kingdom_label": kingdom_label,
        # "query_url": f"https://www.wikidata.org/wiki/{qid}"
    }
