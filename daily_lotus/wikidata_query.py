import secrets
import urllib.parse
from collections.abc import Callable
from datetime import datetime
from itertools import pairwise
from typing import Any, cast

import requests
from SPARQLWrapper import JSON, SPARQLWrapper

WD_ENDPOINT = "https://query.wikidata.org/sparql"


def get_candidate_qids() -> list[str]:
    query = """
    SELECT DISTINCT ?compound WHERE {
      ?compound wdt:P703 ?taxon ;
                wdt:P233 [] .
      ?taxon wdt:P18 ?image .
    }
    LIMIT 500000
    """
    sparql = SPARQLWrapper(WD_ENDPOINT)
    sparql.addCustomHttpHeader(
        "User-Agent",
        "DailyLotusBot/0.1 (https://www.earthmetabolome.org/; contact@earthmetabolome.org)",
    )
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    raw = cast(dict[str, Any], sparql.query().convert())
    results = raw["results"]["bindings"]
    return [row["compound"]["value"].split("/")[-1] for row in results]


def get_molecule_details(qid: str) -> dict[str, str] | None:
    query = f"""
    SELECT ?compoundLabel ?compound ?taxon ?taxonLabel ?reference ?referenceLabel ?smiles ?taxon_image ?kingdom ?kingdomLabel WHERE {{
      VALUES ?compound {{wd:{qid}}}
      ?compound wdt:P233 ?smiles_c .
      OPTIONAL {{ ?compound wdt:P2017 ?smiles_i . }}
      BIND(COALESCE(?smiles_i, ?smiles_c) AS ?smiles)
      FILTER(BOUND(?smiles))
      ?compound p:P703 ?statement .
      ?statement ps:P703 ?taxon ;
                 prov:wasDerivedFrom ?refnode .
      ?refnode pr:P248 ?reference .
      ?taxon wdt:P18 ?taxon_image .
      ?taxon wdt:P171* ?kingdom .
      FILTER(
        ?kingdom IN (
          wd:Q729,   # Animalia
          wd:Q756,   # Plantae
          wd:Q764,   # Fungi
          wd:Q10876  # Bacteria (domain, not kingdom)
        )
      )
      ?kingdom rdfs:label ?kingdomLabel . FILTER (lang(?kingdomLabel) = "en")
      ?compound rdfs:label ?compoundLabel . FILTER (lang(?compoundLabel) = "en")
      ?taxon rdfs:label ?taxonLabel . FILTER (lang(?taxonLabel) = "en")
      SERVICE <https://query-scholarly.wikidata.org/sparql> {{
        ?reference rdfs:label ?referenceLabel . FILTER (lang(?referenceLabel) = "en")
      }}
    }}
    LIMIT 10
    """
    sparql = SPARQLWrapper(WD_ENDPOINT)
    sparql.addCustomHttpHeader(
        "User-Agent",
        "DailyLotusBot/0.1 (https://www.earthmetabolome.org/; contact@earthmetabolome.org)",
    )
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    raw = cast(dict[str, Any], sparql.query().convert())
    results = raw["results"]["bindings"]
    if not results:
        return None

    row = secrets.choice(results)

    def extract_val(f: str) -> str:
        return str(row.get(f, {}).get("value", ""))

    def extract_qid(f: str) -> str:
        if "value" in row.get(f, {}):
            return str(row[f]["value"].split("/")[-1])
        return "unknown"

    smiles = extract_val("smiles")
    image_url = (
        f"https://dev.api.naturalproducts.net/latest/depict/2D?"
        f"smiles={urllib.parse.quote(smiles)}&width=300&height=200"
        f"&toolkit=cdk&rotate=0&CIP=false&unicolor=false"
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
        "taxon_emoji": {"Q756": "🌿", "Q764": "🍄", "Q729": "🐛", "Q10876": "🦠"}.get(extract_qid("kingdom"), "🧬"),
        "kingdom_label": extract_val("kingdomLabel"),
    }


def get_revisions(qid: str, since: datetime) -> list[dict[str, Any]]:
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": qid,
        "rvprop": "ids|timestamp|user",
        "rvlimit": "50",
        "rvdir": "newer",
        "formatversion": "2",
        "format": "json",
    }
    headers = {"User-Agent": "DailyLotusBot/0.1 (https://www.earthmetabolome.org/; contact@earthmetabolome.org)"}
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    pages = data.get("query", {}).get("pages", [])
    return cast(list[dict[str, Any]], pages[0]["revisions"]) if pages and "revisions" in pages[0] else []


def get_entity_data(qid: str, revid: int) -> dict[str, Any]:
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json?revision={revid}"
    headers = {"User-Agent": "DailyLotusBot/0.1 (https://www.earthmetabolome.org/; contact@earthmetabolome.org)"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return cast(dict[str, Any], r.json()["entities"][qid])


def get_label_from_revision(qid: str, revid: int) -> str | None:
    entity = get_entity_data(qid, revid)
    val = entity.get("labels", {}).get("en", {}).get("value")
    return val if isinstance(val, str) else None


def get_claim_ids_from_revision(qid: str, revid: int, prop: str) -> set[str]:
    claims = get_entity_data(qid, revid).get("claims", {}).get(prop, [])
    ids: set[str] = set()
    for claim in claims:
        val = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(val, dict) and "id" in val:
            ids.add(val["id"])
    return ids


def get_revision_pairs(qid: str, since: datetime) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    revs = get_revisions(qid, since)
    return list(pairwise(revs))


def compare_revisions_for_change(
    qid: str,
    revisions: list[dict[str, Any]],
    extractor: Callable[[dict[str, Any]], str | None],
    old_val: str,
) -> str | None:
    for i in range(1, len(revisions)):
        old_data: dict[str, Any] = get_entity_data(qid, revisions[i - 1]["revid"])
        new_data: dict[str, Any] = get_entity_data(qid, revisions[i]["revid"])
        old = extractor(old_data)
        new = extractor(new_data)
        if old == old_val and new and new != old:
            user = revisions[i].get("user")
            return str(user) if isinstance(user, str) else None
    return None


def find_p703_removal_editor(qid: str, taxon_qid: str, since: datetime) -> str | None:
    for old_rev, new_rev in get_revision_pairs(qid, since):
        if taxon_qid in get_claim_ids_from_revision(
            qid, old_rev["revid"], "P703"
        ) and taxon_qid not in get_claim_ids_from_revision(qid, new_rev["revid"], "P703"):
            return str(new_rev["user"])
    return None


def extract_label(data: dict[str, Any]) -> str | None:
    val = data.get("labels", {}).get("en", {}).get("value")
    return val if isinstance(val, str) else None


def get_label_change_editor(qid: str, old_label: str, since: datetime) -> str | None:
    return compare_revisions_for_change(qid, get_revisions(qid, since), extract_label, old_label)


def get_smiles_change_editor(qid: str, old_smiles: str, since: datetime) -> str | None:
    def extractor(data: dict[str, Any]) -> str | None:
        for claim in data.get("claims", {}).get("P2017", []):
            val = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
            if isinstance(val, str):
                return val
        return None

    return compare_revisions_for_change(qid, get_revisions(qid, since), extractor, old_smiles)


def get_reference_label_change_editor(qid: str, old_label: str, since: datetime) -> str | None:
    for old_rev, new_rev in get_revision_pairs(qid, since):
        if (
            (old_val := get_label_from_revision(qid, old_rev["revid"])) == old_label
            and (new_val := get_label_from_revision(qid, new_rev["revid"]))
            and new_val != old_val
        ):
            return str(new_rev["user"])
    return None


def occurrence_still_exists(compound_qid: str, taxon_qid: str) -> bool:
    sparql = SPARQLWrapper(WD_ENDPOINT)
    sparql.addCustomHttpHeader(
        "User-Agent",
        "DailyLotusBot/0.1 (https://www.earthmetabolome.org/; contact@earthmetabolome.org)",
    )
    sparql.setQuery(f"ASK {{ wd:{compound_qid} wdt:P703 wd:{taxon_qid} . }}")
    sparql.setReturnFormat(JSON)
    result = cast(dict[str, Any], sparql.query().convert())
    return cast(bool, result.get("boolean", False))


def fetch_current_labels(compound_qid: str, taxon_qid: str, reference_qid: str) -> dict[str, str]:
    sparql = SPARQLWrapper(WD_ENDPOINT)
    sparql.addCustomHttpHeader(
        "User-Agent",
        "DailyLotusBot/0.1 (https://www.earthmetabolome.org/; contact@earthmetabolome.org)",
    )
    sparql.setQuery(f"""
    SELECT ?compoundLabel ?taxonLabel ?referenceLabel WHERE {{
      VALUES ?compound_qid {{wd:{compound_qid}}}
      VALUES ?taxon_qid {{wd:{taxon_qid}}}
      VALUES ?reference_qid {{wd:{reference_qid}}}
      OPTIONAL {{ ?compound_qid rdfs:label ?compoundLabel . FILTER(LANG(?compoundLabel) = "en") }}
      OPTIONAL {{ ?taxon_qid rdfs:label ?taxonLabel . FILTER(LANG(?taxonLabel) = "en") }}
      SERVICE <https://query-scholarly.wikidata.org/sparql> {{
        OPTIONAL {{ ?reference_qid rdfs:label ?referenceLabel . FILTER(LANG(?referenceLabel) = "en") }}
        }}
    }}
    """)
    sparql.setReturnFormat(JSON)
    raw = cast(dict[str, Any], sparql.query().convert())
    bindings = raw.get("results", {}).get("bindings", [])
    if not bindings:
        return {"compound_label": "", "taxon_label": "", "reference_label": ""}
    row = bindings[0]
    return {
        "compound_label": str(row.get("compoundLabel", {}).get("value", "")),
        "taxon_label": str(row.get("taxonLabel", {}).get("value", "")),
        "reference_label": str(row.get("referenceLabel", {}).get("value", "")),
    }
