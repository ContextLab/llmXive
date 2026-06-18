"""Papers channel (spec 017, T017).

Uses SemanticScholar + arXiv search to find candidate papers, then
fetches their full text via grounding.full_text.retrieve.

Per librarian resilience pattern: any failure returns [].
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from llmxive.fill.channels import AUTHORITY
from llmxive.fill.models import FetchedSource
from llmxive.grounding.full_text import RetrievedDoc, retrieve
from llmxive.librarian.search import ArxivClient, Candidate, SemanticScholarClient, merge_candidates

if TYPE_CHECKING:
    from llmxive.claims.models import Claim

logger = logging.getLogger(__name__)

_MAX_CANDIDATES = 5

# ---------------------------------------------------------------------------
# Shared ArxivClient (Fix D): one module-level client so the circuit-breaker
# state is shared across every papers-channel call (was: a fresh ArxivClient()
# per invocation, which reset the tripped 429 breaker each round).
# ---------------------------------------------------------------------------
_SHARED_ARXIV_LOCK = threading.Lock()
_SHARED_ARXIV: ArxivClient | None = None


def _shared_arxiv_client() -> ArxivClient:
    """Return a process-wide singleton ArxivClient (lazily constructed)."""
    global _SHARED_ARXIV
    with _SHARED_ARXIV_LOCK:
        if _SHARED_ARXIV is None:
            _SHARED_ARXIV = ArxivClient()
        return _SHARED_ARXIV


# ---------------------------------------------------------------------------
# SemanticScholar availability breaker (Fix E): SS rate-limits aggressively
# (HTTP 429) and recovers slowly.  Re-querying it once per claim after a 429
# wedges a whole pipeline run in fail-soft retries (observed: the in_progress
# tick logging nothing but "SS failed: 429" for minutes while verifying a
# report's claims, never reaching execution).  Once SS signals it is
# unavailable (429 / rate-limit / 403), skip it for the REMAINDER of the
# process; arXiv and the other fill channels still run, so claims still get
# real sources — we just stop hammering a service that has told us to stop.
# ---------------------------------------------------------------------------
_SS_BREAKER_LOCK = threading.Lock()
_ss_unavailable = False
_SS_UNAVAILABLE_MARKERS = (
    "429",
    "too many requests",
    "rate limit",
    "ratelimit",
    "403",
    "forbidden",
)


def _ss_is_unavailable() -> bool:
    with _SS_BREAKER_LOCK:
        return _ss_unavailable


def _trip_ss_breaker_if_persistent(exc: Exception) -> None:
    """Trip the SS breaker when the error is a persistent unavailability signal."""
    text = str(exc).lower()
    if not any(marker in text for marker in _SS_UNAVAILABLE_MARKERS):
        return
    global _ss_unavailable
    with _SS_BREAKER_LOCK:
        already = _ss_unavailable
        _ss_unavailable = True
    if not already:
        logger.warning(
            "papers.search_and_fetch: SemanticScholar unavailable (%s); skipping "
            "SS for the rest of this run, using arXiv + other channels only.",
            exc,
        )


def _reset_ss_breaker() -> None:
    """Test hook: clear the SS availability breaker (does not touch disk)."""
    global _ss_unavailable
    with _SS_BREAKER_LOCK:
        _ss_unavailable = False


# ---------------------------------------------------------------------------
# Negative-result cache (Fix B): remember failed (paper, id) retrieves so a
# 503 / empty-PDF candidate is not re-fetched within or across rounds.  Scoped
# to the specific id — never the whole claim.
# ---------------------------------------------------------------------------
_NEG_CHANNEL = "paper"
_NEG_MEMO: set[str] = set()


def _reset_negative_cache() -> None:
    """Clear the in-process negative memo (test hook; does not touch disk)."""
    _NEG_MEMO.clear()


def _neg_key(ident: str) -> str:
    return f"paper-neg::id::{ident}"


def _is_negative(ident: str, *, repo_root: Path | None) -> bool:
    key = _neg_key(ident)
    if key in _NEG_MEMO:
        return True
    if repo_root is None:
        return False
    try:
        from llmxive.grounding import cache as _cache
        data = _cache.get_verdict(
            repo_root, source_id=_NEG_CHANNEL, claim=key, number=None
        )
        if data is not None and data.get("status") == "negative":
            _NEG_MEMO.add(key)
            return True
    except Exception as exc:  # pragma: no cover - best-effort
        logger.debug("papers: negative-cache read failed for %s: %s", key, exc)
    return False


def _mark_negative(ident: str, *, repo_root: Path | None) -> None:
    key = _neg_key(ident)
    _NEG_MEMO.add(key)
    if repo_root is None:
        return
    try:
        from llmxive.grounding import cache as _cache
        _cache.put_verdict(
            repo_root, source_id=_NEG_CHANNEL, claim=key, number=None,
            verdict={"status": "negative", "ident": ident},
        )
    except Exception as exc:  # pragma: no cover - best-effort
        logger.debug("papers: negative-cache write failed for %s: %s", key, exc)


def _candidate_to_source(candidate: Candidate, doc: RetrievedDoc) -> FetchedSource | None:
    """Adapt a (Candidate, RetrievedDoc) pair to a FetchedSource.

    Returns None if the doc has no readable text.
    """
    text = doc.full_text or doc.abstract
    if not text:
        return None
    return FetchedSource(
        channel="paper",
        source_id=candidate.primary_pointer,
        url=doc.final_url or candidate.primary_pointer,
        title=candidate.claimed_title or doc.title,
        text=text,
        authority=AUTHORITY["paper"],
    )


def _retrieve_for_candidate(candidate: Candidate, *, timeout: float) -> RetrievedDoc | None:
    """Determine kind/value from the candidate pointer and call retrieve()."""
    pointer = candidate.primary_pointer
    # Determine retrieval kind based on the pointer format
    if pointer.startswith("https://doi.org/") or pointer.startswith("10."):
        doi = pointer.removeprefix("https://doi.org/")
        return retrieve("doi", doi, timeout=timeout)
    elif "/" not in pointer and "." in pointer and pointer[0].isdigit():
        # Looks like a bare arXiv ID (e.g. "2301.12345")
        return retrieve("arxiv", pointer, timeout=timeout)
    elif pointer.startswith("http"):
        return retrieve("url", pointer, timeout=timeout)
    else:
        # Try as arXiv ID anyway
        return retrieve("arxiv", pointer, timeout=timeout)


def search_and_fetch(
    query: str,
    claim: Claim,
    *,
    timeout: float = 30.0,
    repo_root: Path | None = None,
) -> list[FetchedSource]:
    """Search SemanticScholar + arXiv, fetch text, return FetchedSources.

    Returns [] on any failure — never raises into the caller.
    """
    try:
        candidates: list[Candidate] = []

        # SemanticScholar — skipped for the rest of the run once it has signalled
        # unavailability (429/403), so a rate-limited SS cannot wedge the loop.
        if not _ss_is_unavailable():
            try:
                ss = SemanticScholarClient()
                if ss.has_key:
                    ss_results = ss.search_papers(query, limit=_MAX_CANDIDATES)
                    candidates.extend(ss_results)
            except Exception as exc:
                logger.warning("papers.search_and_fetch: SS failed: %s", exc)
                _trip_ss_breaker_if_persistent(exc)

        # arXiv — use the SHARED ArxivClient so the circuit breaker is honoured
        # across calls (Fix D).
        try:
            arxiv = _shared_arxiv_client()
            arxiv_results = arxiv.search(query, max_results=_MAX_CANDIDATES)
            candidates.extend(arxiv_results)
        except Exception as exc:
            logger.warning("papers.search_and_fetch: arXiv failed: %s", exc)

        # Deduplicate
        try:
            candidates = merge_candidates(candidates)
        except Exception:
            pass  # merge is best-effort

        results: list[FetchedSource] = []
        for candidate in candidates[:_MAX_CANDIDATES]:
            ident = candidate.primary_pointer
            if _is_negative(ident, repo_root=repo_root):
                logger.debug(
                    "papers.search_and_fetch: id %s in negative cache; skipping", ident
                )
                continue
            try:
                doc = _retrieve_for_candidate(candidate, timeout=timeout)
                if doc is None or not doc.readable:
                    _mark_negative(ident, repo_root=repo_root)
                    continue
                source = _candidate_to_source(candidate, doc)
                if source is not None:
                    results.append(source)
                else:
                    _mark_negative(ident, repo_root=repo_root)
            except Exception as exc:
                logger.warning(
                    "papers.search_and_fetch: retrieve failed for %s: %s",
                    ident, exc,
                )
                _mark_negative(ident, repo_root=repo_root)
                continue

        return results
    except Exception as exc:
        logger.warning("papers.search_and_fetch: unexpected error: %s", exc)
        return []


__all__ = [
    "_candidate_to_source",
    "_reset_negative_cache",
    "_reset_ss_breaker",
    "_shared_arxiv_client",
    "_ss_is_unavailable",
    "search_and_fetch",
]
