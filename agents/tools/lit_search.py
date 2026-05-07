"""DEPRECATED — soft-deprecated post spec 005 (2026-05-06).

This module's literature-search implementation has been REPLACED by
the canonical ``llmxive.agents.librarian.LibrarianAgent``. New callers
MUST NOT import from here:

    # Old (deprecated):
    from agents.tools.lit_search import lit_search

    # New (canonical):
    from llmxive.agents.librarian import LibrarianAgent
    from llmxive.agents import registry
    librarian = LibrarianAgent(registry.get("librarian"))
    result = librarian.invoke(term="...", field="...", target_n=5)

This file is preserved with a soft-deprecation banner because:
  - Pre-spec-005 callers (``flesh_out`` agent at
    ``src/llmxive/agents/idea_lifecycle.py:173``) used to import
    ``lit_search`` and consume its ``Paper`` records.
  - Spec 003's tests may reference this module via the historical
    invocation path.
  - Constitution Principle I requires deletion of duplicate
    implementations, but soft-deprecation (banner + delegate) is the
    intermediate state per spec-004's iteration-convention doc.

The ``lit_search()`` function below now delegates to the librarian
and adapts its rich ``VerifiedCitation`` records into the legacy
``Paper`` dataclass shape. Behavior is preserved; the implementation
is consolidated.

Per FR-022: any NEW agent that needs literature search MUST import the
librarian directly. Tests at ``tests/phase2/test_no_duplicate_lit_search.py``
(spec 005 / T070a) will fail any PR that re-introduces a duplicate
search-and-verify implementation outside ``src/llmxive/librarian/``.

See also:
  - notes/2026-05-06-spec-005-librarian-outline.md
  - specs/005-librarian-agent/research.md (Decision 1)
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from typing import Any

LOGGER = logging.getLogger(__name__)


@dataclass
class Paper:
    """Legacy paper record from the pre-spec-005 lit_search tool.

    Preserved for backwards-compat with callers that consume
    ``p.title``, ``p.year``, ``p.source_url``, ``p.abstract``. New
    callers should use the librarian's ``VerifiedCitation`` shape
    instead (richer, includes verification log).
    """

    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    source_url: str = ""
    abstract: str = ""
    provider: str = ""
    external_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "source_url": self.source_url,
            "abstract": self.abstract,
            "provider": self.provider,
            "external_id": self.external_id,
        }


def lit_search(query: str, max_results: int = 8) -> list[Paper]:
    """DEPRECATED: thin wrapper around ``LibrarianAgent.invoke()``.

    Delegates to the canonical librarian + adapts its
    ``VerifiedCitation`` records into the legacy ``Paper`` shape.
    Existing flesh_out call site at ``idea_lifecycle.py:173`` continues
    to work without modification; the implementation underneath now
    consolidates the search + verify + PDF-sample + cache logic into
    one canonical place per Constitution Principle I.
    """
    warnings.warn(
        "agents.tools.lit_search.lit_search is deprecated; "
        "use llmxive.agents.librarian.LibrarianAgent.invoke() directly.",
        DeprecationWarning,
        stacklevel=2,
    )

    if not query or not query.strip():
        return []

    try:
        from llmxive.agents import registry as registry_loader
        from llmxive.agents.librarian import LibrarianAgent
    except ImportError as exc:
        LOGGER.warning("librarian import failed; lit_search returning []: %s", exc)
        return []

    try:
        entry = registry_loader.get("librarian")
    except KeyError:
        LOGGER.warning("librarian not registered; lit_search returning []")
        return []

    librarian = LibrarianAgent(entry)
    try:
        result = librarian.invoke(term=query, target_n=max_results)
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("librarian.invoke failed; lit_search returning []: %s", exc)
        return []

    return _verified_citations_to_papers(result.to_dict()["verified_citations"])


def _verified_citations_to_papers(citations: list[dict[str, Any]]) -> list[Paper]:
    """Adapt librarian-shaped citations to legacy Paper records.

    Mapping:
      - bibliographic_info.title → Paper.title
      - bibliographic_info.authors → Paper.authors
      - bibliographic_info.year → Paper.year
      - verification_log.final_url → Paper.source_url
      - summary → Paper.abstract  (Note: librarian's summary is
                                    abstract-derived per FR-003)
      - primary_pointer prefix → Paper.provider (heuristic)
      - primary_pointer → Paper.external_id
    """
    papers: list[Paper] = []
    for c in citations:
        bib = c.get("bibliographic_info") or {}
        log = c.get("verification_log") or {}
        pointer = c.get("primary_pointer", "")
        provider = "arxiv" if _looks_like_arxiv(pointer) else "semantic_scholar"
        papers.append(
            Paper(
                title=str(bib.get("title") or "").strip(),
                authors=list(bib.get("authors") or []),
                year=bib.get("year"),
                source_url=str(log.get("final_url") or pointer),
                abstract=str(c.get("summary") or "").strip(),
                provider=provider,
                external_id=pointer,
            )
        )
    return papers


def _looks_like_arxiv(pointer: str) -> bool:
    """Return True if pointer looks like an arXiv ID (modern or old-style)."""
    import re

    return bool(
        re.match(r"^\d{4}\.\d{4,5}$", pointer)
        or re.match(r"^[a-z\-]+(?:\.[A-Z]{2})?/\d{7}$", pointer)
        or "arxiv.org" in pointer.lower()
    )


__all__ = ["Paper", "lit_search"]
