"""Wikidata channel for authoritative-fill (spec 017, T028/T029).

search_and_fetch(query, claim) -> list[FetchedSource]

Uses the Wikidata API:
  wbsearchentities  — find candidate Q-ids for the query
  wbgetentities     — fetch labels/descriptions/claims for each Q-id

``wbsearchentities`` matches entity NAMES/aliases, not full text — a
relation-phrase query like "capital of Australia" matches nothing even
though Q408 (Australia) carries the answer in its P36 statement. When the
phrase search comes back empty, we fall back to searching the proper-noun
terms in the query/claim ("Australia", "Sydney"), whose entity statements
then surface the fact for the present-in-source gate.

Returns FetchedSource per entity; [] on any HTTP failure.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from llmxive.claims.models import Claim
from llmxive.fill.channels import AUTHORITY
from llmxive.fill.models import FetchedSource
from llmxive.librarian.search import USER_AGENT, _retry_request

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.wikidata.org/w/api.php"
_MAX_ENTITIES = 3  # top-N entities to fetch per query

#: Fact-bearing properties walked FIRST when building an entity's text blob.
#: Rich entities (countries, people) carry hundreds of properties and the
#: walk is capped, so without prioritization canonical facts like P36
#: (capital) routinely fall outside the cap — Q408 (Australia) never
#: surfaced "Canberra" for the present-in-source gate.
_PRIORITY_PIDS: tuple[str, ...] = (
    "P31",    # instance of
    "P36",    # capital
    "P1376",  # capital of
    "P17",    # country
    "P30",    # continent
    "P361",   # part of
    "P527",   # has part
    "P1082",  # population
    "P2046",  # area
    "P6",     # head of government
    "P35",    # head of state
    "P112",   # founded by
    "P159",   # headquarters location
    "P50",    # author
    "P57",    # director
    "P19",    # place of birth
    "P20",    # place of death
    "P27",    # country of citizenship
    "P106",   # occupation
    "P569",   # date of birth
    "P570",   # date of death
)


def _ordered_claims(claims_data: dict[str, Any]) -> list[tuple[str, Any]]:
    """Property items with fact-bearing PIDs first, then response order."""
    priority = [
        (pid, claims_data[pid]) for pid in _PRIORITY_PIDS if pid in claims_data
    ]
    rest = [
        (pid, snaks) for pid, snaks in claims_data.items()
        if pid not in _PRIORITY_PIDS
    ]
    return priority + rest


# ---------------------------------------------------------------------------
# Pure parsers (testable offline with fixture dicts)
# ---------------------------------------------------------------------------

def _parse_search(data: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Parse wbsearchentities response → list[(qid, label, description)]."""
    results = []
    for item in data.get("search", []):
        qid = item.get("id", "")
        label = item.get("label", "")
        description = item.get("description", "")
        if qid:
            results.append((qid, label, description))
    return results


def _parse_entity(
    data: dict[str, Any],
    qid: str,
    ref_labels: dict[str, str] | None = None,
) -> tuple[str, str] | None:
    """Parse wbgetentities response for *qid* → (label, text_blob) or None.

    The text blob is built from:
    - English label
    - English description
    - String values of P-claims (up to 20) for keyword density
    - For wikibase-entityid values: the English label from *ref_labels* when
      available (so "P36: Q3114" becomes "capital: Canberra").
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

    # Extract string values from claims (snak mainvalue strings only),
    # fact-bearing properties first so the cap can't push them out.
    claim_snippets: list[str] = []
    ref_labels = ref_labels or {}
    claims_data = entity.get("claims", {})
    for pid, snak_list in _ordered_claims(claims_data)[:60]:
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
                    # Prefer the human-readable label if available
                    inner_label = ref_labels.get(inner_id, inner_id)
                    claim_snippets.append(f"{pid}: {inner_label}")
            elif dv_type == "monolingualtext":
                val = dv.get("value", {}).get("text", "")
                if val:
                    claim_snippets.append(f"{pid}: {val}")

    parts = [label, description, *claim_snippets]
    text_blob = "\n".join(p for p in parts if p)
    if not text_blob:
        return None
    return label, text_blob


def _collect_ref_qids(entity_data: dict[str, Any], qids: list[str]) -> list[str]:
    """Collect all wikibase-entityid Q-ids referenced in the claims of *qids*.

    These are used for a secondary label-resolution call so that entity
    values appear as human-readable names in the text blob (e.g. "Canberra"
    instead of "Q3114").
    """
    ref_qids: list[str] = []
    seen: set[str] = set(qids)
    entities = entity_data.get("entities", {})
    for qid in qids:
        entity = entities.get(qid, {})
        # Same prioritized walk as _parse_entity, so the Q-ids whose labels
        # we resolve are the ones that will actually appear in the blob.
        for _pid, snak_list in _ordered_claims(entity.get("claims", {}))[:60]:
            for snak in snak_list[:3]:
                ms = snak.get("mainsnak", {})
                dv = ms.get("datavalue", {})
                if dv.get("type") == "wikibase-entityid":
                    inner_id = dv.get("value", {}).get("id", "")
                    if inner_id and inner_id not in seen:
                        ref_qids.append(inner_id)
                        seen.add(inner_id)
    return ref_qids[:30]  # cap to avoid very large secondary fetches


def _proper_noun_terms(query: str, claim: Claim) -> list[str]:
    """Capitalized multi-word/single-word terms from the query + claim text.

    Fallback search terms for when the phrase query matches no entity NAME:
    "The capital of Australia is Sydney" → ["Australia", "Sydney"]. Adjacent
    capitalized words group into one term ("New Zealand"). Sentence-initial
    capitalization is handled by dropping terms shorter than 3 chars and
    common sentence starters rather than positional tricks.
    """
    text = f"{query} {claim.raw_text}"
    terms: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"\b([A-Z][a-zA-Z0-9'-]+(?:\s+[A-Z][a-zA-Z0-9'-]+)*)", text):
        term = match.group(1).strip()
        if len(term) < 3 or term.lower() in {"the", "this", "that", "these", "those"}:
            continue
        if term.lower() not in seen:
            seen.add(term.lower())
            terms.append(term)
    return terms[:4]  # bounded fan-out


def _search_entities(query: str, *, timeout: float) -> list[tuple[str, str, str]]:
    """One wbsearchentities call → parsed candidates ([] on any failure)."""
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
        return _parse_search(r.json())
    except Exception as exc:
        logger.debug("wikidata: search failed: %s", exc)
        return []


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

    # Step 1: search for entity Q-ids. wbsearchentities matches entity
    # names/aliases only, so a relation phrase ("capital of Australia")
    # often returns nothing — fall back to the proper-noun terms, whose
    # entity statements carry the fact (e.g. Q408's P36 → Canberra).
    candidates = _search_entities(query, timeout=timeout)
    if not candidates:
        merged: list[tuple[str, str, str]] = []
        seen_qids: set[str] = set()
        for term in _proper_noun_terms(query, claim):
            for cand in _search_entities(term, timeout=timeout):
                if cand[0] not in seen_qids:
                    seen_qids.add(cand[0])
                    merged.append(cand)
            if len(merged) >= _MAX_ENTITIES:
                break
        candidates = merged
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

    # Step 3: resolve referenced Q-ids to human-readable labels so the text
    # blob contains names like "Canberra" instead of "Q3114" — essential for
    # the present-in-source gate to find the filled value.
    ref_qids = _collect_ref_qids(entity_data, qids)
    ref_labels: dict[str, str] = {}
    if ref_qids:
        try:
            r3 = _retry_request(
                "GET",
                _SEARCH_URL,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                params={
                    "action": "wbgetentities",
                    "ids": "|".join(ref_qids),
                    "format": "json",
                    "props": "labels",
                },
                timeout=timeout,
            )
            if r3.status_code == 200:
                ref_data = r3.json()
                for rqid, rent in ref_data.get("entities", {}).items():
                    rlabels = rent.get("labels", {})
                    en_label = rlabels.get("en", {}).get("value", "")
                    if en_label:
                        ref_labels[rqid] = en_label
        except Exception as exc:
            logger.debug("wikidata: ref label fetch failed: %s", exc)

    sources: list[FetchedSource] = []
    for qid, label, _description in candidates:
        parsed = _parse_entity(entity_data, qid, ref_labels=ref_labels)
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


__all__ = ["_parse_entity", "_parse_search", "search_and_fetch"]
