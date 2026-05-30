"""Papers channel (spec 017, T017).

Uses SemanticScholar + arXiv search to find candidate papers, then
fetches their full text via grounding.full_text.retrieve.

Per librarian resilience pattern: any failure returns [].
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from llmxive.fill.channels import AUTHORITY
from llmxive.fill.models import FetchedSource
from llmxive.grounding.full_text import RetrievedDoc, retrieve
from llmxive.librarian.search import ArxivClient, Candidate, SemanticScholarClient, merge_candidates

if TYPE_CHECKING:
    from llmxive.claims.models import Claim

logger = logging.getLogger(__name__)

_MAX_CANDIDATES = 5


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
    claim: "Claim",
    *,
    timeout: float = 30.0,
) -> list[FetchedSource]:
    """Search SemanticScholar + arXiv, fetch text, return FetchedSources.

    Returns [] on any failure — never raises into the caller.
    """
    try:
        candidates: list[Candidate] = []

        # SemanticScholar
        try:
            ss = SemanticScholarClient()
            if ss.has_key:
                ss_results = ss.search_papers(query, limit=_MAX_CANDIDATES)
                candidates.extend(ss_results)
        except Exception as exc:
            logger.warning("papers.search_and_fetch: SS failed: %s", exc)

        # arXiv
        try:
            arxiv = ArxivClient()
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
            try:
                doc = _retrieve_for_candidate(candidate, timeout=timeout)
                if doc is None or not doc.readable:
                    continue
                source = _candidate_to_source(candidate, doc)
                if source is not None:
                    results.append(source)
            except Exception as exc:
                logger.warning(
                    "papers.search_and_fetch: retrieve failed for %s: %s",
                    candidate.primary_pointer, exc,
                )
                continue

        return results
    except Exception as exc:
        logger.warning("papers.search_and_fetch: unexpected error: %s", exc)
        return []


__all__ = ["_candidate_to_source", "search_and_fetch"]
