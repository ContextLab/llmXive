"""T031 — Non-numeric claim resolvers: triple parsing, ordering, relational, superlative.

Pure helpers:
  decompose_triple(text)           -> (subject, relation, object)
  check_ordering(candidates, claim) -> bool

IO-backed resolvers:
  resolve_relational(claim, *, backend, model, repo_root) -> Verdict
  resolve_superlative(claim, *, backend, model, repo_root) -> Verdict
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from llmxive.claims.models import ClaimStatus, Verdict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Relation keyword patterns (ordered longest-first for greedy match)
# ---------------------------------------------------------------------------

_RELATION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bis\s+the\s+capital\s+of\b", re.IGNORECASE), "is the capital of"),
    (re.compile(r"\bcapital\s+of\b", re.IGNORECASE), "capital of"),
    (re.compile(r"\bauthor\s+of\b", re.IGNORECASE), "author of"),
    (re.compile(r"\bwrote\b", re.IGNORECASE), "wrote"),
    (re.compile(r"\binvented\s+by\b", re.IGNORECASE), "invented by"),
    (re.compile(r"\bfounded\s+by\b", re.IGNORECASE), "founded by"),
    (re.compile(r"\bdiscovered\s+by\b", re.IGNORECASE), "discovered by"),
    (re.compile(r"\bpublished\s+in\b", re.IGNORECASE), "published in"),
    (re.compile(r"\blocated\s+in\b", re.IGNORECASE), "located in"),
    (re.compile(r"\bpart\s+of\b", re.IGNORECASE), "part of"),
    (re.compile(r"\bmember\s+of\b", re.IGNORECASE), "member of"),
    (re.compile(r"\bbelongs?\s+to\b", re.IGNORECASE), "belongs to"),
]

# Superlative / comparative direction words
_LARGEST_RE = re.compile(
    r"\b(largest?|greatest?|highest?|biggest?|most|maximum|max)\b", re.IGNORECASE
)
_SMALLEST_RE = re.compile(
    r"\b(smallest?|lowest?|fewest?|minimum|min|least)\b", re.IGNORECASE
)
_EARLIEST_RE = re.compile(r"\b(earliest?|first|oldest?)\b", re.IGNORECASE)
_LATEST_RE = re.compile(r"\b(latest?|last|newest?|most\s+recent)\b", re.IGNORECASE)
_FASTEST_RE = re.compile(r"\b(fastest?)\b", re.IGNORECASE)
_SLOWEST_RE = re.compile(r"\b(slowest?)\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# PURE: decompose_triple
# ---------------------------------------------------------------------------

def decompose_triple(text: str) -> tuple[str, str, str]:
    """Parse an SPO assertion into (subject, relation, object).

    Strategy:
    1. If the canonical triple separator " | " is present, split on it.
    2. Otherwise scan for a known relation keyword; split around it.
    3. If no relation found, split on " is " as a last resort.
    4. Returns best-effort; never raises.

    Examples::

        decompose_triple("Gauss is the author of Disquisitiones")
        # -> ("Gauss", "author of", "Disquisitiones")

        decompose_triple("Paris is the capital of France")
        # -> ("Paris", "is the capital of", "France")

        decompose_triple("Gauss | author of | Disquisitiones")
        # -> ("Gauss", "author of", "Disquisitiones")
    """
    text = (text or "").strip()

    # Canonical separator form "subject | relation | object"
    if "|" in text:
        parts = [p.strip() for p in text.split("|", 2)]
        if len(parts) == 3 and all(parts):
            return (parts[0], parts[1], parts[2])
        if len(parts) == 2 and all(parts):
            return (parts[0], "", parts[1])

    # Keyword scan — pick the earliest match
    best_match: re.Match[str] | None = None
    best_relation: str = ""
    for pattern, label in _RELATION_PATTERNS:
        m = pattern.search(text)
        if m and (best_match is None or m.start() < best_match.start()):
            best_match = m
            best_relation = label

    if best_match is not None:
        subj = text[: best_match.start()].strip().rstrip(",").strip()
        obj = text[best_match.end():].strip().lstrip(",").strip()
        return (subj, best_relation, obj)

    # Last-resort: split on " is "
    is_re = re.compile(r"\bis\b", re.IGNORECASE)
    m = is_re.search(text)
    if m:
        subj = text[: m.start()].strip()
        rest = text[m.end():].strip()
        return (subj, "is", rest)

    # Fallback: return the whole text as subject, empty relation/object
    return (text, "", "")


# ---------------------------------------------------------------------------
# PURE: check_ordering
# ---------------------------------------------------------------------------

def check_ordering(candidates: list[Any], claim: str) -> bool:
    """Check whether a superlative/ordering claim holds over a candidate set.

    ``candidates`` is a list of comparable items — either plain numbers
    (int/float/str-of-number) or 2-tuples ``(name, numeric_value)``.  The
    function extracts the numeric values, determines what the claim asserts
    (largest, smallest, earliest, fastest, …) and returns True iff the
    first element of the list (the asserted winner) is indeed at that
    extreme.

    Rules:
    - The asserted entity is the FIRST item in ``candidates``; the rest are
      the comparison set.  (Callers build the list so the claimed item is
      first.)
    - If the candidate set has fewer than 2 items the ordering is vacuously
      True (nothing to compare against).
    - On parse failure (no numeric value extractable) returns False.
    - Unknown direction keywords → False (conservative).

    Examples::

        check_ordering([("Jupiter", 1.898e27), ("Earth", 5.972e24)],
                       "Jupiter is the largest planet")  # True

        check_ordering([("Earth", 5.972e24), ("Jupiter", 1.898e27)],
                       "Earth is the largest planet")    # False (Earth < Jupiter)
    """
    claim = (claim or "").strip()

    if len(candidates) < 2:
        return True  # vacuously true — nothing to compare

    def _to_float(item: Any) -> float | None:
        if isinstance(item, (int, float)):
            return float(item)
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            return _to_float(item[1])
        if isinstance(item, str):
            cleaned = re.sub(r"[,_\s]", "", item)
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    values: list[float | None] = [_to_float(c) for c in candidates]
    if values[0] is None:
        return False
    non_none = [v for v in values if v is not None]
    if len(non_none) < 2:
        return True  # only one numeric value → vacuously true

    asserted = values[0]
    rest = [v for v in values[1:] if v is not None]
    if not rest:
        return True

    if _LARGEST_RE.search(claim) or _FASTEST_RE.search(claim):
        return asserted >= max(rest)

    if _SMALLEST_RE.search(claim) or _SLOWEST_RE.search(claim):
        return asserted <= min(rest)

    if _EARLIEST_RE.search(claim):
        return asserted <= min(rest)

    if _LATEST_RE.search(claim):
        return asserted >= max(rest)

    # Unknown direction → conservative False
    return False


# ---------------------------------------------------------------------------
# IO-backed: resolve_relational
# ---------------------------------------------------------------------------

def resolve_relational(
    claim: Any,
    *,
    backend: Any,
    model: str | None,
    repo_root: Path,
) -> Verdict:
    """Resolve a RELATIONAL claim: decompose → retrieve citable source → entailment.

    ``claim`` may be a :class:`~llmxive.claims.models.Claim` instance OR a
    plain string (to allow direct calls from triple.py tests and the
    dispatcher).

    Resolution steps:
    1. Extract the canonical text from the claim.
    2. Decompose into (subject, relation, object) via ``decompose_triple``.
    3. Search the librarian for a citable source mentioning subject + object.
    4. Retrieve full text via ``grounding.full_text.retrieve``.
    5. Run entailment via ``grounding.entailment.assess``.
    6. Map grounded→VERIFIED, contradicted→REFUTED, not_found→NOT_ENOUGH_INFO.
    NEVER infers VERIFIED from model text alone — requires a citable source.
    """
    from llmxive.grounding import cache as _cache
    from llmxive.grounding.entailment import assess
    from llmxive.grounding.full_text import retrieve

    # Normalise: accept Claim objects or raw strings
    if hasattr(claim, "canonical"):
        canonical = claim.canonical or claim.raw_text or ""
        claim_id = getattr(claim, "claim_id", None)
    else:
        canonical = str(claim)
        claim_id = None

    canonical = canonical.strip()
    if not canonical:
        return Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "empty canonical text"},
            resolver="resolve_relational",
        )

    subj, rel, obj = decompose_triple(canonical)

    # Build a query that targets subject + relation + object
    query_parts = [p for p in (subj, rel, obj) if p]
    search_query = " ".join(query_parts)

    # Try to find a citable source via Semantic Scholar / arXiv / web search
    doc = _search_for_source(search_query, backend=backend, model=model,
                              repo_root=repo_root)

    if doc is None or not doc.readable:
        return Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={
                "reason": "no citable source found for relational claim",
                "subject": subj,
                "relation": rel,
                "object": obj,
            },
            resolver="resolve_relational",
        )

    # Run entailment over the retrieved document
    verdict = assess(canonical, doc, backend=backend, model=model,
                     repo_root=repo_root)

    status_map = {
        "grounded": ClaimStatus.VERIFIED,
        "contradicted": ClaimStatus.REFUTED,
        "not_found": ClaimStatus.NOT_ENOUGH_INFO,
    }
    status = status_map.get(verdict.status, ClaimStatus.NOT_ENOUGH_INFO)

    return Verdict(
        status=status,
        value=canonical if status == ClaimStatus.VERIFIED else None,
        evidence={
            "source_url": doc.final_url,
            "source_kind": doc.kind,
            "source_value": doc.value,
            "subject": subj,
            "relation": rel,
            "object": obj,
            "entailment_status": verdict.status,
            "entailment_evidence": verdict.evidence,
        },
        resolver="resolve_relational",
    )


# ---------------------------------------------------------------------------
# IO-backed: resolve_superlative
# ---------------------------------------------------------------------------

def resolve_superlative(
    claim: Any,
    *,
    backend: Any,
    model: str | None,
    repo_root: Path,
) -> Verdict:
    """Resolve a MAGNITUDE/superlative claim: retrieve candidate set → check_ordering.

    ``claim`` may be a :class:`~llmxive.claims.models.Claim` or a string.

    Steps:
    1. Extract canonical text.
    2. Search the librarian for a source that lists the relevant candidate set.
    3. Parse numeric candidates from the retrieved text.
    4. Run ``check_ordering`` — if the asserted extremum is correct → VERIFIED,
       else → REFUTED.
    5. If no candidate set can be retrieved → NOT_ENOUGH_INFO.
    NEVER infers VERIFIED from model text alone.
    """
    from llmxive.grounding.entailment import assess
    from llmxive.grounding.full_text import retrieve

    if hasattr(claim, "canonical"):
        canonical = claim.canonical or claim.raw_text or ""
    else:
        canonical = str(claim)

    canonical = canonical.strip()
    if not canonical:
        return Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "empty canonical text"},
            resolver="resolve_superlative",
        )

    # Search for a source that discusses the superlative claim
    doc = _search_for_source(canonical, backend=backend, model=model,
                              repo_root=repo_root)

    if doc is None or not doc.readable:
        return Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "no source found to validate superlative claim"},
            resolver="resolve_superlative",
        )

    # Try entailment first (the retrieved text may directly state the answer)
    entailment = assess(canonical, doc, backend=backend, model=model,
                        repo_root=repo_root)

    if entailment.status == "grounded":
        return Verdict(
            status=ClaimStatus.VERIFIED,
            value=canonical,
            evidence={
                "source_url": doc.final_url,
                "entailment_status": entailment.status,
                "entailment_evidence": entailment.evidence,
            },
            resolver="resolve_superlative",
        )

    if entailment.status == "contradicted":
        return Verdict(
            status=ClaimStatus.REFUTED,
            value=None,
            evidence={
                "source_url": doc.final_url,
                "entailment_status": entailment.status,
                "entailment_evidence": entailment.evidence,
            },
            resolver="resolve_superlative",
        )

    # entailment said not_found — try numeric ordering over the retrieved text
    source_text = doc.full_text or doc.abstract or ""
    candidates = _extract_numeric_candidates(source_text, claim=canonical)

    if len(candidates) < 2:
        return Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={
                "reason": "candidate set too small to verify ordering",
                "source_url": doc.final_url,
                "candidates_found": len(candidates),
            },
            resolver="resolve_superlative",
        )

    correct = check_ordering(candidates, canonical)
    status = ClaimStatus.VERIFIED if correct else ClaimStatus.REFUTED

    return Verdict(
        status=status,
        value=canonical if correct else None,
        evidence={
            "source_url": doc.final_url,
            "candidates": candidates[:10],  # cap evidence size
            "ordering_correct": correct,
        },
        resolver="resolve_superlative",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _search_for_source(
    query: str,
    *,
    backend: Any,
    model: str | None,
    repo_root: Path,
) -> Any:
    """Best-effort search for a citable source for the given query.

    Tries (in order):
    1. Semantic Scholar via librarian.search
    2. arXiv via librarian.search
    3. Web URL fetch via grounding.full_text.retrieve(kind="url", ...)
    Returns the first RetrievedDoc with readable content, or None.
    """
    from llmxive.grounding.full_text import RetrievedDoc, retrieve
    from llmxive.librarian.search import SemanticScholarClient

    try:
        s2 = SemanticScholarClient()
        candidates = s2.search_papers(query, limit=5)
        for cand in candidates:
            ptr = cand.primary_pointer or ""
            # Try DOI (10.xxxx/...) or arXiv id
            if ptr.startswith("10."):
                doc = retrieve("doi", ptr, timeout=30.0)
                if doc.readable:
                    return doc
            elif re.match(r"^\d{4}\.\d{4,}", ptr):
                doc = retrieve("arxiv", ptr, timeout=30.0)
                if doc.readable:
                    return doc
            elif ptr.startswith("http"):
                doc = retrieve("url", ptr, timeout=30.0)
                if doc.readable:
                    return doc
            # Abstract-only from the candidate itself is acceptable
            if cand.claimed_abstract:
                return RetrievedDoc(
                    kind="s2_abstract",
                    value=query,
                    tier="abstract",
                    full_text=None,
                    abstract=cand.claimed_abstract,
                    title=cand.claimed_title,
                    final_url=ptr,
                )
    except Exception as exc:
        logger.debug("triple._search_for_source: S2 search failed (%s)", exc)

    # Wikipedia-style URL heuristic for well-known relational facts
    try:
        slug = re.sub(r"\s+", "_", query[:60])
        url = f"https://en.wikipedia.org/wiki/{slug}"
        doc = retrieve("url", url, timeout=20.0)
        if doc.readable:
            return doc
    except Exception as exc:
        logger.debug("triple._search_for_source: Wikipedia fetch failed (%s)", exc)

    return None


def _extract_numeric_candidates(text: str, *, claim: str) -> list[tuple[str, float]]:
    """Extract (label, value) pairs from text for ordering checks.

    Focuses on numbers that appear near proper nouns (capitalized words),
    which are typical in comparative/superlative contexts.

    Returns a list sorted by value descending (largest first) so
    ``check_ordering([first, ...], claim)`` with a "largest" claim checks
    whether the first candidate is actually the max.
    """
    # Find all "Word ... number" or "number ... Word" patterns
    NUMBER_RE = re.compile(r"[-+]?\d[\d,_]*(?:\.\d+)?(?:[eE][+-]?\d+)?")
    # Find candidate name+value pairs: "Foo Bar: 42" or "42 Foo Bar"
    LABEL_NUM_RE = re.compile(
        r"([A-Z][A-Za-z0-9 \-]{1,40})\s*[:\s]\s*"
        r"([-+]?\d[\d,_]*(?:\.\d+)?(?:[eE][+-]?\d+)?)"
    )
    results: list[tuple[str, float]] = []
    for m in LABEL_NUM_RE.finditer(text):
        label = m.group(1).strip()
        raw_num = re.sub(r"[,_]", "", m.group(2))
        try:
            results.append((label, float(raw_num)))
        except ValueError:
            pass

    # Also try bare numbers if we got fewer than 3
    if len(results) < 3:
        for m in NUMBER_RE.finditer(text):
            raw = re.sub(r"[,_]", "", m.group(0))
            try:
                results.append(("", float(raw)))
            except ValueError:
                pass

    # Deduplicate by value, sort descending
    seen: set[float] = set()
    deduped: list[tuple[str, float]] = []
    for label, val in results:
        if val not in seen:
            seen.add(val)
            deduped.append((label, val))
    deduped.sort(key=lambda x: x[1], reverse=True)
    return deduped


__all__ = [
    "decompose_triple",
    "check_ordering",
    "resolve_relational",
    "resolve_superlative",
]
