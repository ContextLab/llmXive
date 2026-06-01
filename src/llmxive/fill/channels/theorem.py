"""Theorem channel (spec 017, T017).

Uses TheoremSearchClient to find theorem candidates, then fetches their
full text via grounding.full_text.retrieve (same adaptation as papers.py).

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
from llmxive.librarian.search import ArxivClient, Candidate
from llmxive.librarian.theoremsearch import TheoremSearchClient

if TYPE_CHECKING:
    from llmxive.claims.models import Claim

logger = logging.getLogger(__name__)

# Spec: cap the theorem channel — it is the lowest-authority math channel and is
# the heaviest arXiv caller (each candidate triggers a per-id arXiv fetch). Two
# candidates is enough; the higher-authority channels (constants/OEIS/wikipedia)
# resolve most facts and the service short-circuits before theorem runs at all.
_MAX_CANDIDATES = 2

# ---------------------------------------------------------------------------
# Shared ArxivClient (Fix D): one module-level client so the circuit-breaker
# state (a tripped 429 cool-off) is shared across every theorem-channel call
# instead of being reset by a fresh ArxivClient() per invocation.
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
# Negative-result cache (Fix B): remember failed (channel, arxiv_id) retrieves
# and failed search queries so a 503 / empty-PDF candidate is not re-fetched
# within or across rounds.  Persists via the grounding verdict cache when a
# repo_root is available; an in-process set is always consulted as a fast path.
# Scoped to the SPECIFIC (channel,id)/query — never the whole claim — so a
# real-and-resolvable claim is never permanently blocked.
# ---------------------------------------------------------------------------
_NEG_CHANNEL = "theorem"
_NEG_MEMO: set[str] = set()


def _reset_negative_cache() -> None:
    """Clear the in-process negative memo (test hook; does not touch disk)."""
    _NEG_MEMO.clear()


def _neg_key(kind: str, ident: str) -> str:
    return f"theorem-neg::{kind}::{ident}"


def _is_negative(kind: str, ident: str, *, repo_root: Path | None) -> bool:
    key = _neg_key(kind, ident)
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
            _NEG_MEMO.add(key)  # promote to fast path
            return True
    except Exception as exc:  # pragma: no cover - cache is best-effort
        logger.debug("theorem: negative-cache read failed for %s: %s", key, exc)
    return False


def _mark_negative(kind: str, ident: str, *, repo_root: Path | None) -> None:
    key = _neg_key(kind, ident)
    _NEG_MEMO.add(key)
    if repo_root is None:
        return
    try:
        from llmxive.grounding import cache as _cache
        _cache.put_verdict(
            repo_root, source_id=_NEG_CHANNEL, claim=key, number=None,
            verdict={"status": "negative", "kind": kind, "ident": ident},
        )
    except Exception as exc:  # pragma: no cover - cache is best-effort
        logger.debug("theorem: negative-cache write failed for %s: %s", key, exc)


def _candidate_to_source(candidate: Candidate, doc: RetrievedDoc) -> FetchedSource | None:
    """Adapt a (Candidate, RetrievedDoc) pair to a theorem FetchedSource.

    Returns None if the doc has no readable text.
    """
    text = doc.full_text or doc.abstract
    if not text:
        return None
    return FetchedSource(
        channel="theorem",
        source_id=candidate.primary_pointer,
        url=doc.final_url or candidate.primary_pointer,
        title=candidate.claimed_title or doc.title,
        text=text,
        authority=AUTHORITY["theorem"],
    )


def _retrieve_for_candidate(candidate: Candidate, *, timeout: float) -> RetrievedDoc | None:
    """Determine kind/value from the candidate pointer and call retrieve()."""
    pointer = candidate.primary_pointer
    if pointer.startswith("https://doi.org/") or pointer.startswith("10."):
        doi = pointer.removeprefix("https://doi.org/")
        return retrieve("doi", doi, timeout=timeout)
    elif "/" not in pointer and "." in pointer and pointer[0].isdigit():
        # Bare arXiv ID
        return retrieve("arxiv", pointer, timeout=timeout)
    elif pointer.startswith("http"):
        return retrieve("url", pointer, timeout=timeout)
    else:
        return retrieve("arxiv", pointer, timeout=timeout)


def search_and_fetch(
    query: str,
    claim: Claim,
    *,
    timeout: float = 30.0,
    repo_root: Path | None = None,
) -> list[FetchedSource]:
    """Search TheoremSearch, fetch text, return FetchedSources.

    Returns [] on any failure — never raises into the caller.

    Volume controls:
      * shares one module-level ArxivClient (so a tripped 429 breaker is honoured
        across candidates and calls);
      * skips per-candidate retrieves and search queries already known to fail
        (negative cache, scoped to the specific id/query);
      * marks new failures so they are not re-fetched next round.
    """
    try:
        # Skip a query that previously yielded no usable result (avoids re-hitting
        # the TheoremSearch API + the downstream arXiv id resolves it triggers).
        if _is_negative("query", query.strip().lower(), repo_root=repo_root):
            logger.debug("theorem.search_and_fetch: query in negative cache; skipping")
            return []

        # Thread the SHARED ArxivClient so TheoremSearchClient's id-resolution
        # respects the shared circuit breaker (Fix D).
        client = TheoremSearchClient(arxiv_client=_shared_arxiv_client())
        candidates: list[Candidate] = []
        try:
            candidates = client.search(query, limit=_MAX_CANDIDATES)
        except Exception as exc:
            logger.warning("theorem.search_and_fetch: TheoremSearch failed: %s", exc)
            return []

        if not candidates:
            _mark_negative("query", query.strip().lower(), repo_root=repo_root)
            return []

        results: list[FetchedSource] = []
        for candidate in candidates[:_MAX_CANDIDATES]:
            ident = candidate.primary_pointer
            if _is_negative("id", ident, repo_root=repo_root):
                logger.debug(
                    "theorem.search_and_fetch: id %s in negative cache; skipping", ident
                )
                continue
            try:
                doc = _retrieve_for_candidate(candidate, timeout=timeout)
                if doc is None or not doc.readable:
                    # Failed / empty fetch → remember so we don't re-fetch this id.
                    _mark_negative("id", ident, repo_root=repo_root)
                    continue
                source = _candidate_to_source(candidate, doc)
                if source is not None:
                    results.append(source)
                else:
                    _mark_negative("id", ident, repo_root=repo_root)
            except Exception as exc:
                logger.warning(
                    "theorem.search_and_fetch: retrieve failed for %s: %s",
                    ident, exc,
                )
                _mark_negative("id", ident, repo_root=repo_root)
                continue

        return results
    except Exception as exc:
        logger.warning("theorem.search_and_fetch: unexpected error: %s", exc)
        return []


__all__ = [
    "_candidate_to_source",
    "_reset_negative_cache",
    "_shared_arxiv_client",
    "search_and_fetch",
]
