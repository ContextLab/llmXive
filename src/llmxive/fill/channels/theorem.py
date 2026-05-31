"""Theorem channel (spec 017, T017).

Uses TheoremSearchClient to find theorem candidates, then fetches their
full text via grounding.full_text.retrieve (same adaptation as papers.py).

Per librarian resilience pattern: any failure returns [].
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from llmxive.fill.channels import AUTHORITY
from llmxive.fill.models import FetchedSource
from llmxive.grounding.full_text import RetrievedDoc, retrieve
from llmxive.librarian.search import Candidate
from llmxive.librarian.theoremsearch import TheoremSearchClient

if TYPE_CHECKING:
    from llmxive.claims.models import Claim

logger = logging.getLogger(__name__)

_MAX_CANDIDATES = 5


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
) -> list[FetchedSource]:
    """Search TheoremSearch, fetch text, return FetchedSources.

    Returns [] on any failure — never raises into the caller.
    """
    try:
        client = TheoremSearchClient()
        candidates: list[Candidate] = []
        try:
            candidates = client.search(query, limit=_MAX_CANDIDATES)
        except Exception as exc:
            logger.warning("theorem.search_and_fetch: TheoremSearch failed: %s", exc)
            return []

        results: list[FetchedSource] = []
        for candidate in candidates[:_MAX_CANDIDATES]:
            try:
                doc = _retrieve_for_candidate(candidate, timeout=timeout)
                if doc is None or not doc.readable:
                    continue
                source = _candidate_to_source(candidate, doc)
                if source is not None:
                    results.append(source)
            except Exception as exc:
                logger.warning(
                    "theorem.search_and_fetch: retrieve failed for %s: %s",
                    candidate.primary_pointer, exc,
                )
                continue

        return results
    except Exception as exc:
        logger.warning("theorem.search_and_fetch: unexpected error: %s", exc)
        return []


__all__ = ["_candidate_to_source", "search_and_fetch"]
