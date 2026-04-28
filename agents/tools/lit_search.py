"""Lit-Search tool (T041) — queries Semantic Scholar / arXiv / OpenAlex.

Used by the Flesh-Out Agent to ground its `Related work` section in
real primary sources, by the Paper-Specifier to identify the paper's
prior-art landscape, and by the Writing-Agent to find references
during paper drafting.

Per Constitution Principle II, every record returned here MUST be a
real result from a real upstream API — no fabricated entries. The
caller (Reference-Validator Agent) re-verifies each cited paper
before review points are awarded.

The tool is intentionally tolerant of upstream outages: if all three
providers fail, it returns an empty list rather than raising, so the
Flesh-Out Agent can decide whether to proceed (a fleshed-out idea
with zero related-work bullets is rejected by the Idea-Selector).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT_S = 10.0
DEFAULT_USER_AGENT = "llmxive-lit-search/0.1 (+https://github.com/ContextLab/llmXive)"


@dataclass
class Paper:
    """Structured paper record returned by every provider."""

    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    source_url: str = ""
    abstract: str = ""
    provider: str = ""
    external_id: str = ""  # arXiv id / DOI / OpenAlex id, depending on provider

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


def _semantic_scholar(
    query: str, max_results: int, timeout: float, client: httpx.Client | None = None
) -> list[Paper]:
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params: dict[str, str | int] = {
        "query": query,
        "limit": max_results,
        "fields": "title,authors,year,externalIds,abstract,url",
    }
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    try:
        if client is None:
            with httpx.Client(timeout=timeout, headers=headers) as inner:
                resp = inner.get(url, params=params)
        else:
            resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except httpx.HTTPError as exc:
        LOGGER.warning("semantic_scholar query failed: %s", exc)
        return []

    papers: list[Paper] = []
    for item in data:
        title = (item.get("title") or "").strip()
        if not title:
            continue
        authors = [a.get("name", "") for a in item.get("authors") or [] if a.get("name")]
        ext_ids = item.get("externalIds") or {}
        external_id = ext_ids.get("DOI") or ext_ids.get("ArXiv") or ext_ids.get("CorpusId", "")
        papers.append(
            Paper(
                title=title,
                authors=authors,
                year=item.get("year"),
                source_url=item.get("url") or "",
                abstract=(item.get("abstract") or "").strip(),
                provider="semantic_scholar",
                external_id=str(external_id),
            )
        )
    return papers


def _arxiv(query: str, max_results: int, timeout: float) -> list[Paper]:
    try:
        import arxiv  # lazy import — arxiv is in optional deps for this tool
    except ImportError:
        LOGGER.warning("arxiv package not installed; skipping arxiv provider")
        return []
    try:
        search = arxiv.Search(query=query, max_results=max_results)
        results = list(search.results())
    except Exception as exc:  # arxiv raises a variety of errors
        LOGGER.warning("arxiv query failed: %s", exc)
        return []

    papers: list[Paper] = []
    for r in results:
        papers.append(
            Paper(
                title=(r.title or "").strip(),
                authors=[a.name for a in r.authors],
                year=r.published.year if r.published else None,
                source_url=r.entry_id or "",
                abstract=(r.summary or "").strip(),
                provider="arxiv",
                external_id=r.entry_id.rsplit("/", 1)[-1] if r.entry_id else "",
            )
        )
    return papers


def _openalex(
    query: str, max_results: int, timeout: float, client: httpx.Client | None = None
) -> list[Paper]:
    url = "https://api.openalex.org/works"
    params: dict[str, str | int] = {
        "search": query,
        "per-page": max_results,
        "select": "id,title,authorships,publication_year,doi,abstract_inverted_index",
    }
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    try:
        if client is None:
            with httpx.Client(timeout=timeout, headers=headers) as inner:
                resp = inner.get(url, params=params)
        else:
            resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("results", [])
    except httpx.HTTPError as exc:
        LOGGER.warning("openalex query failed: %s", exc)
        return []

    papers: list[Paper] = []
    for item in data:
        title = (item.get("title") or "").strip()
        if not title:
            continue
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in item.get("authorships") or []
            if a.get("author")
        ]
        # OpenAlex returns abstracts as inverted indexes; reconstruct loosely.
        abstract = ""
        inv = item.get("abstract_inverted_index") or {}
        if isinstance(inv, dict) and inv:
            tokens: list[tuple[int, str]] = []
            for word, positions in inv.items():
                for p in positions:
                    tokens.append((p, word))
            abstract = " ".join(w for _, w in sorted(tokens))
        papers.append(
            Paper(
                title=title,
                authors=[a for a in authors if a],
                year=item.get("publication_year"),
                source_url=item.get("doi") or item.get("id") or "",
                abstract=abstract,
                provider="openalex",
                external_id=item.get("id", ""),
            )
        )
    return papers


def _dedupe(papers: list[Paper]) -> list[Paper]:
    """Drop duplicate hits (same title, case-insensitive)."""
    seen: set[str] = set()
    out: list[Paper] = []
    for p in papers:
        key = p.title.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def lit_search(
    query: str,
    *,
    max_results: int = 8,
    timeout: float = DEFAULT_TIMEOUT_S,
    providers: list[str] | None = None,
) -> list[Paper]:
    """Search the configured providers in parallel order, dedupe, and trim.

    Default order: semantic_scholar → arxiv → openalex (most coverage
    first; later providers fill in gaps).
    """
    if not query.strip():
        return []
    providers = providers or ["semantic_scholar", "arxiv", "openalex"]

    collected: list[Paper] = []
    for prov in providers:
        if prov == "semantic_scholar":
            collected.extend(_semantic_scholar(query, max_results, timeout))
        elif prov == "arxiv":
            collected.extend(_arxiv(query, max_results, timeout))
        elif prov == "openalex":
            collected.extend(_openalex(query, max_results, timeout))
        else:
            LOGGER.warning("unknown provider: %s", prov)
        if len(_dedupe(collected)) >= max_results:
            break

    return _dedupe(collected)[:max_results]


__all__ = ["Paper", "lit_search"]
