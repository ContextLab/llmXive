"""Wikidata channel for authoritative-fill (spec 017, T028/T029).

search_and_fetch(query, claim) -> list[FetchedSource]

Uses the Wikidata API:
  wbsearchentities  — find candidate Q-ids for the query
  wbgetentities     — fetch labels/descriptions/claims for each Q-id

Returns FetchedSource per entity; [] on any HTTP failure.
"""

from __future__ import annotations

import logging
from typing import Any

from llmxive.claims.models import Claim
from llmxive.fill.channels import AUTHORITY
from llmxive.fill.models import FetchedSource
from llmxive.librarian.search import USER_AGENT, _retry_request

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.wikidata.org/w/api.php"
_MAX_ENTITIES = 3  # top-N entities to fetch per query


# ---------------------------------------------------------------------------
# Pure parsers (testable offline with fixture dicts)
# ---------------------------------------------------------------------------

def _parse_search(data: dict) -> list[tuple[str, str, str]]:
    """Parse wbsearchentities response → list[(qid, label, description)]."""
    results = []
    for item in data.get("search", []):
        qid = item.get("id", "")
        label = item.get("label", "")
        description = item.get("description", "")
        if qid:
            results.append((qid, label, description))
    return results


def _parse_entity(data: dict, qid: str) -> tuple[str, str] | None:
    """Parse wbgetentities response for *qid* → (label, text_blob) or None.

    The text blob is built from:
    - English label
    - English description
    - String values of P-claims (up to 20) for keyword density
    """
    entities = data.get("entities", {})
    entity = entities.get(qid)
    if entity is None or entity.get("missing") is not None:
        return None

    # Extract English label
    labels = entity.get("labels", {})
    label = labels.get("en", {}).get("value", "")
    if not label:
        # Try any available label
        for lang_data in labels.values():
            label = lang_data.get("value", "")
            if label:
                break

    # Extract English description
    descriptions = entity.get("descriptions", {})
    description = descriptions.get("en", {}).get("value", "")

    # Extract string values from claims (snak mainvalue strings only)
    claim_snippets: list[str] = []
    claims_data = entity.get("claims", {})
    for pid, snak_list in list(claims_data.items())[:20]:
        for snak in snak_list[:3]:
            ms = snak.get("mainsnak", {})
            dv = ms.get("datavalue", {})
            dv_type = dv.get("type", "")
            if dv_type == "string":
                val = dv.get("value", "")
                if val:
                    claim_snippets.append(f"{pid}: {val}")
            elif dv_type == "wikibase-entityid":
                inner = dv.get("value", {})
                inner_id = inner.get("id", "")
                if inner_id:
                    claim_snippets.append(f"{pid}: {inner_id}")
            elif dv_type == "monolingualtext":
                val = dv.get("value", {}).get("text", "")
                if val:
                    claim_snippets.append(f"{pid}: {val}")

    parts = [label, description] + claim_snippets
    text_blob = "\n".join(p for p in parts if p)
    if not text_blob:
        return None
    return label, text_blob


# ---------------------------------------------------------------------------
# Real HTTP fetch
# ---------------------------------------------------------------------------

def search_and_fetch(
    query: str,
    claim: Claim,
    *,
    timeout: float = 30.0,
) -> list[FetchedSource]:
    """Real Wikidata search + entity fetch → list[FetchedSource].

    Returns [] on any failure (network, parse, no results).
    """
    if not query.strip():
        return []

    # Step 1: search for entity Q-ids
    try:
        r = _retry_request(
            "GET",
            _SEARCH_URL,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            params={
                "action": "wbsearchentities",
                "search": query,
                "language": "en",
                "format": "json",
                "limit": str(_MAX_ENTITIES),
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            logger.debug("wikidata: search returned HTTP %s", r.status_code)
            return []
        search_data = r.json()
    except Exception as exc:
        logger.debug("wikidata: search failed: %s", exc)
        return []

    candidates = _parse_search(search_data)
    if not candidates:
        return []

    # Limit to top-N
    candidates = candidates[:_MAX_ENTITIES]

    # Step 2: fetch entities
    qids = [qid for qid, _, _ in candidates]
    try:
        r2 = _retry_request(
            "GET",
            _SEARCH_URL,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            params={
                "action": "wbgetentities",
                "ids": "|".join(qids),
                "format": "json",
                "props": "labels|descriptions|claims",
            },
            timeout=timeout,
        )
        if r2.status_code != 200:
            logger.debug("wikidata: entity fetch returned HTTP %s", r2.status_code)
            return []
        entity_data = r2.json()
    except Exception as exc:
        logger.debug("wikidata: entity fetch failed: %s", exc)
        return []

    sources: list[FetchedSource] = []
    for qid, label, description in candidates:
        parsed = _parse_entity(entity_data, qid)
        if parsed is None:
            continue
        ent_label, text_blob = parsed
        try:
            src = FetchedSource(
                channel="wikidata",
                source_id=qid,
                url=f"https://www.wikidata.org/wiki/{qid}",
                title=ent_label or label,
                text=text_blob,
                authority=AUTHORITY["wikidata"],
            )
            sources.append(src)
        except ValueError:
            # text was empty — skip
            logger.debug("wikidata: empty text for %s, skipping", qid)

    return sources


__all__ = ["search_and_fetch", "_parse_search", "_parse_entity"]
