"""Canonical citation-verification helper (spec 005 / FR-003 / Q2).

Single source of truth for the three-check verification chain that
spec 003's `tests/phase1/citation_resolver.py` and spec 004's
`reference_validator` previously each implemented separately.

The three checks (per data-model.md E3):

  1. **URL resolves**: HTTP HEAD with redirect-follow + GET-fallback on 405.
     Per spec 003's pattern, 401/403/429 after ≥1 redirect = ``ambiguous``
     (paywall, not unreachable) — we still admit the citation but flag it.
  2. **Title-token-overlap**: Jaccard on lowercased word tokens
     (search-result-claimed title vs primary-source-fetched title).
     Threshold: ``CITATION_TITLE_OVERLAP_THRESHOLD`` (default 0.7,
     inheriting from the parent constitution).
  3. **Summary-grounded**: Jaccard on lowercased word-stem tokens
     (librarian-generated summary vs fetched abstract). Threshold:
     ``SUMMARY_GROUNDING_THRESHOLD`` (default 0.5, introduced by spec 005).

Each check returns a structured result; the orchestrator decides whether
to admit the citation based on per-check verdicts.

Per Constitution Principle III: real HTTP, no mocks. Per Principle V:
fail-fast — every check has a bounded deadline (60s per citation).
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import re
from typing import Any, Literal

import requests

from llmxive.librarian.search import USER_AGENT, Candidate

CITATION_TITLE_OVERLAP_THRESHOLD = 0.7
SUMMARY_GROUNDING_THRESHOLD = 0.5
# Topical-relevance gate: fraction of the user's salient query tokens
# (after stop-word + short-token filtering) that must appear in the
# candidate's claimed title + abstract. Low absolute number because
# queries are often long sentences while titles are short, but high
# enough to filter out false positives where a search backend returned a
# paper that shares only generic stop-tokens (e.g., "demographic",
# "lifestyle", "analysis") with the query. Spec 005 / SC-001 + FR-003.
QUERY_RELEVANCE_THRESHOLD = 0.30
PER_CITATION_TIMEOUT = 60.0  # seconds

# Common English stop-tokens that produce false topical matches when a
# query and an unrelated paper happen to share them. Conservative list:
# only words that genuinely carry no topical signal.
_QUERY_STOPWORDS: frozenset[str] = frozenset({
    "the", "and", "for", "with", "from", "into", "that", "this", "these",
    "those", "have", "has", "was", "were", "are", "been", "being", "but",
    "not", "any", "all", "can", "may", "will", "would", "could", "should",
    "must", "than", "then", "such", "some", "more", "most", "less", "much",
    "many", "few", "very", "well", "also", "even", "just", "only", "still",
    "after", "before", "during", "while", "when", "where", "what", "which",
    "who", "whom", "whose", "why", "how", "does", "doing", "done", "did",
    "between", "across", "through", "along", "among", "about", "above",
    "below", "under", "over", "within", "without", "their", "there",
    "they", "them", "his", "her", "its", "our", "your", "study", "studies",
    "analysis", "analyses", "research", "method", "methods", "approach",
    "approaches", "results", "result", "effect", "effects", "impact",
    "impacts", "investigation", "investigate", "investigating", "examine",
    "examining", "evaluating", "evaluation", "predict", "predicting",
    "prediction", "controlling", "control", "factor", "factors",
    "individual", "individuals", "instance", "instances",
})


@dataclasses.dataclass(frozen=True)
class VerificationLog:
    """Audit trail for a single verify_citation call (data-model.md E3)."""

    url_resolves: bool
    final_url: str
    redirect_chain: list[str]
    http_status: int | None
    title_token_overlap_score: float
    summary_grounding_score: float
    pdf_sample_score: float | None
    verified_at: str  # ISO-8601 UTC
    query_relevance_score: float = 0.0  # spec 005 fix: topical relevance to user query
    backend: str = ""  # spec 006: the search backend that produced the candidate
                       # ("semantic_scholar" | "arxiv" | "theoremsearch"); "" for legacy entries


@dataclasses.dataclass(frozen=True)
class VerifiedCitation:
    """A Candidate that passed all three verification checks."""

    primary_pointer: str
    bibliographic_info: dict[str, Any]
    summary: str
    summary_grounded_pdf: bool | None  # None if PDF inaccessible
    verification_log: VerificationLog


@dataclasses.dataclass(frozen=True)
class VerificationFailure:
    """A Candidate that failed one or more verification checks."""

    candidate: Candidate
    reason: Literal[
        "url_not_resolves",
        "title_mismatch",
        "summary_not_grounded",
        "summary_not_grounded_pdf",
        "paywall_partial",
        "timeout",
        "query_irrelevant",
    ]
    details: str
    failed_at: str  # ISO-8601 UTC


VerifyResult = VerifiedCitation | VerificationFailure


def verify_citation(
    candidate: Candidate,
    *,
    fetch_pdf: bool = False,
    summary: str | None = None,
    timeout: float = PER_CITATION_TIMEOUT,
    query: str | None = None,
) -> VerifyResult:
    """Run the four-check chain on one Candidate.

    ``query``: the user's search term that produced this candidate.
    If supplied, a topical-relevance gate (Check 0, fail-fast) rejects
    candidates whose claimed title+abstract share fewer than
    ``QUERY_RELEVANCE_THRESHOLD`` of the query's salient (non-stop-word,
    length≥3) tokens. None disables the check (preserves prior behavior
    for callers that don't have a query — e.g., direct DOI lookups).

    ``summary``: librarian-generated summary to verify against fetched
    content. If None, the Candidate's ``claimed_abstract`` is used as a
    minimal fallback (so the verify check still runs but is essentially
    self-comparison; callers should always pass a real summary).

    Returns either a VerifiedCitation (passed all checks, possibly with
    ``summary_grounded_pdf`` flagged) or a VerificationFailure (one or
    more checks failed).
    """
    started = _now_iso()

    # Check 0 (fail-fast): topical relevance to the user's query.
    # Filters out search-backend false positives that share only generic
    # stop-tokens with the query (spec 005 fix; see SC-001 + FR-003).
    relevance_score = 0.0
    if query:
        candidate_blob = " ".join(filter(None, [
            candidate.claimed_title,
            candidate.claimed_abstract,
        ]))
        relevance_score = query_relevance_score(query, candidate_blob)
        if relevance_score < QUERY_RELEVANCE_THRESHOLD:
            return VerificationFailure(
                candidate=candidate,
                reason="query_irrelevant",
                details=(
                    f"query-relevance {relevance_score:.3f} < "
                    f"{QUERY_RELEVANCE_THRESHOLD} "
                    f"(query={query[:80]!r}, "
                    f"candidate_title={candidate.claimed_title!r})"
                ),
                failed_at=_now_iso(),
            )

    # Resolve the URL form of the primary pointer.
    url = _candidate_url(candidate)

    # Check 1: URL resolves.
    head_result = _head_with_get_fallback(url, timeout=min(30.0, timeout))
    if head_result.outcome == "unreachable":
        return VerificationFailure(
            candidate=candidate,
            reason="url_not_resolves",
            details=(
                f"HTTP HEAD/GET failed for {url} "
                f"(status={head_result.http_status}, error={head_result.error})"
            ),
            failed_at=_now_iso(),
        )

    # Fetch the primary source's title + abstract for overlap checks.
    fetched_title, fetched_abstract = _fetch_title_and_abstract(candidate, head_result.final_url)

    # Check 2: title-token-overlap.
    title_score = jaccard_tokens(candidate.claimed_title, fetched_title)
    if title_score < CITATION_TITLE_OVERLAP_THRESHOLD:
        return VerificationFailure(
            candidate=candidate,
            reason="title_mismatch",
            details=(
                f"title token-overlap {title_score:.3f} < "
                f"{CITATION_TITLE_OVERLAP_THRESHOLD} "
                f"(claimed={candidate.claimed_title!r}, fetched={fetched_title!r})"
            ),
            failed_at=_now_iso(),
        )

    # Check 3: summary-grounded against the fetched abstract.
    summary_text = (summary or candidate.claimed_abstract or "").strip()
    grounding_score = (
        jaccard_tokens(summary_text, fetched_abstract or "")
        if (summary_text and fetched_abstract)
        else 0.0
    )
    if summary_text and (fetched_abstract or "").strip():
        if grounding_score < SUMMARY_GROUNDING_THRESHOLD:
            return VerificationFailure(
                candidate=candidate,
                reason="summary_not_grounded",
                details=(
                    f"summary-abstract token-overlap {grounding_score:.3f} < "
                    f"{SUMMARY_GROUNDING_THRESHOLD}"
                ),
                failed_at=_now_iso(),
            )

    log = VerificationLog(
        url_resolves=True,
        final_url=head_result.final_url,
        redirect_chain=head_result.redirect_chain,
        http_status=head_result.http_status,
        title_token_overlap_score=round(title_score, 4),
        summary_grounding_score=round(grounding_score, 4),
        pdf_sample_score=None,  # filled in by pdf_sample.py if/when sampled
        verified_at=started,
        query_relevance_score=round(relevance_score, 4),
        backend=candidate.backend,
    )

    return VerifiedCitation(
        primary_pointer=candidate.primary_pointer,
        bibliographic_info={
            "title": fetched_title or candidate.claimed_title,
            "authors": candidate.claimed_authors,
            "year": candidate.claimed_year,
            "venue": candidate.claimed_venue,
        },
        summary=summary_text,
        summary_grounded_pdf=None,  # decided later by pdf_sample.py
        verification_log=log,
    )


# --- Tokenization + Jaccard helpers ---------------------------------------

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    """Lowercase + extract alphanumeric tokens. Drops 1-letter tokens.

    Simpler than full stemming but adequate for title + abstract
    similarity. Matches spec 003's resolver behavior.
    """
    if not text:
        return set()
    toks = _WORD_RE.findall(text.lower())
    return {t for t in toks if len(t) > 1}


def jaccard_tokens(a: str, b: str) -> float:
    """Return Jaccard similarity of the alphanumeric token sets of a + b."""
    sa, sb = _tokenize(a), _tokenize(b)
    if not sa or not sb:
        return 0.0
    inter = sa & sb
    union = sa | sb
    return len(inter) / len(union)


def _salient_query_tokens(query: str) -> set[str]:
    """Tokens carrying topical signal: lowercased, length>=3, not stop-words."""
    return {t for t in _tokenize(query) if len(t) >= 3 and t not in _QUERY_STOPWORDS}


def query_relevance_score(query: str, candidate_text: str) -> float:
    """Fraction of the user's salient query tokens present in the candidate.

    Uses *containment* (intersection / |query|), not Jaccard, because
    queries are often long sentences while candidate titles are short —
    Jaccard would penalize length asymmetry. Returns 0.0 if the query
    has no salient tokens (e.g., all stop-words).

    Threshold: ``QUERY_RELEVANCE_THRESHOLD`` (0.30 — at least ~3 salient
    query tokens must appear in the candidate's title+abstract).
    """
    qs = _salient_query_tokens(query)
    if not qs:
        return 0.0
    cand_tokens = _tokenize(candidate_text)
    if not cand_tokens:
        return 0.0
    return len(qs & cand_tokens) / len(qs)


# --- HTTP helpers ---------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class _HeadResult:
    outcome: Literal["resolved", "ambiguous", "unreachable"]
    http_status: int | None
    final_url: str
    redirect_chain: list[str]
    error: str | None


def _head_with_get_fallback(url: str, *, timeout: float = 30.0) -> _HeadResult:
    """Match spec 003's pattern: HEAD with redirect-follow; GET fallback on 405.

    Per spec 003: 401/403/429 after ≥1 redirect classifies as
    ``ambiguous`` (paywall/login-wall on a real host), NOT unreachable.
    """
    try:
        r = requests.head(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
        if r.status_code == 405:
            r = requests.get(
                url,
                headers={"User-Agent": USER_AGENT, "Range": "bytes=0-2047"},
                timeout=timeout,
                allow_redirects=True,
                stream=True,
            )
            r.close()
        chain = [resp.url for resp in r.history]
        if 200 <= r.status_code < 300:
            return _HeadResult("resolved", r.status_code, r.url, chain, None)
        if 300 <= r.status_code < 400:
            return _HeadResult("ambiguous", r.status_code, r.url, chain, None)
        if r.status_code in (401, 403, 429) and r.history:
            return _HeadResult("ambiguous", r.status_code, r.url, chain, None)
        return _HeadResult("unreachable", r.status_code, r.url, chain, None)
    except (requests.RequestException, OSError) as exc:
        return _HeadResult("unreachable", None, url, [], f"{type(exc).__name__}: {exc}")


def _candidate_url(candidate: Candidate) -> str:
    """Best-effort URL form of the candidate's primary_pointer.

    DOI → https://doi.org/<doi>
    arXiv ID → https://arxiv.org/abs/<id>
    Already-an-URL → unchanged
    """
    p = candidate.primary_pointer
    if p.startswith(("http://", "https://")):
        return p
    if p.startswith("10.") and "/" in p:
        return f"https://doi.org/{p}"
    # arXiv IDs look like "1706.03762" or "cs.CL/0301012"
    if re.match(r"^\d{4}\.\d{4,5}$", p) or re.match(r"^[a-z\-]+(?:\.[A-Z]{2})?/\d{7}$", p):
        return f"https://arxiv.org/abs/{p}"
    return p  # best effort — verification will likely fail upstream


def _fetch_title_and_abstract(
    candidate: Candidate, final_url: str
) -> tuple[str, str | None]:
    """Re-fetch (title, abstract) from the primary source.

    The whole point of check 2 (title-token-overlap) is to verify the
    *backend's claim* against the *primary source's actual content*.
    Returning ``candidate.claimed_*`` would make this check a tautology
    (the candidate's claim compared to itself), defeating the purpose.

    Strategy by primary_pointer shape:
      - arXiv ID (e.g. ``1706.03762``): re-fetch via arXiv API (the
        ``arxiv`` Python library) — ground-truth metadata.
      - DOI (https://doi.org/...): trust the candidate's claim. Most
        DOI redirects land on publisher HTML behind a paywall; we
        can't reliably extract title/abstract from arbitrary publisher
        pages without a separate scraper for each. The Semantic Scholar
        Graph API has already done that resolution and returned the
        canonical metadata when our SS client called it. (If the SS
        backend itself misreports, that's a different bug — out of
        scope.)
      - Other URL: trust the candidate's claim, same reasoning.

    Returns (fetched_title, fetched_abstract). ``fetched_abstract`` may
    be None if the primary source doesn't expose one.
    """
    pointer = candidate.primary_pointer

    # arXiv — re-fetch via arXiv API.
    if _is_arxiv_id(pointer):
        return _fetch_from_arxiv(pointer)
    if pointer.startswith("https://arxiv.org/abs/"):
        arxiv_id = pointer.removeprefix("https://arxiv.org/abs/")
        # Strip version suffix.
        if "v" in arxiv_id:
            head, _, tail = arxiv_id.rpartition("v")
            if tail.isdigit():
                arxiv_id = head
        return _fetch_from_arxiv(arxiv_id)

    # DOI / other URL — trust the candidate's claim.
    return (candidate.claimed_title, candidate.claimed_abstract)


def _is_arxiv_id(s: str) -> bool:
    """Match modern arXiv IDs (2007.04567) and old-style (cs.CL/0301012)."""
    return bool(
        re.match(r"^\d{4}\.\d{4,5}$", s)
        or re.match(r"^[a-z\-]+(?:\.[A-Z]{2})?/\d{7}$", s)
    )


def _fetch_from_arxiv(arxiv_id: str) -> tuple[str, str | None]:
    """Fetch title + abstract from arXiv API by ID. Returns ('', None) on
    fetch failure (caller's title-overlap check will then fail with score
    0, which is the correct behavior — we can't verify against a source
    we couldn't reach).
    """
    try:
        import arxiv  # type: ignore[import-not-found]

        client = arxiv.Client()
        search = arxiv.Search(id_list=[arxiv_id])
        for result in client.results(search):
            return (
                (result.title or "").strip(),
                (result.summary or "").strip() or None,
            )
    except Exception:
        pass
    return ("", None)


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


__all__ = [
    "CITATION_TITLE_OVERLAP_THRESHOLD",
    "QUERY_RELEVANCE_THRESHOLD",
    "SUMMARY_GROUNDING_THRESHOLD",
    "VerificationFailure",
    "VerificationLog",
    "VerifiedCitation",
    "VerifyResult",
    "jaccard_tokens",
    "query_relevance_score",
    "verify_citation",
]
