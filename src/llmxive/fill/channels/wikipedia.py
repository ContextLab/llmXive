"""Wikipedia channel (spec 017, T015/T016).

Uses the Wikipedia action=query API:
  - list=search  to find article titles matching the query
  - prop=extracts to fetch plain-text extracts for the top titles

Per librarian resilience pattern: any HTTP or parse failure returns [].
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from llmxive.fill.channels import AUTHORITY
from llmxive.fill.models import FetchedSource
from llmxive.librarian.search import USER_AGENT, _retry_request

if TYPE_CHECKING:
    from llmxive.claims.models import Claim

logger = logging.getLogger(__name__)

_WIKI_API = "https://en.wikipedia.org/w/api.php"
_MAX_TITLES = 3  # fetch extracts for at most this many search results


def _parse_search(json_dict: dict) -> list[str]:
    """Extract article titles from a Wikipedia action=query&list=search response."""
    try:
        items = json_dict.get("query", {}).get("search", [])
        return [item["title"] for item in items if "title" in item]
    except Exception:
        return []


def _parse_extract(json_dict: dict) -> tuple[str, str] | None:
    """Extract (title, text) from a Wikipedia action=query&prop=extracts response.

    Returns None if the page is missing or the extract is empty.
    """
    try:
        pages = json_dict.get("query", {}).get("pages", {})
        for page in pages.values():
            if "missing" in page:
                continue
            title = page.get("title", "")
            text = page.get("extract", "")
            if title and text:
                return (title, text)
        return None
    except Exception:
        return None


def _search_titles(query: str, *, timeout: float) -> list[str]:
    """Call Wikipedia search API, return up to _MAX_TITLES article titles."""
    try:
        r = _retry_request(
            "GET",
            _WIKI_API,
            headers={"User-Agent": USER_AGENT},
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": str(_MAX_TITLES),
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            logger.warning("wikipedia._search_titles: HTTP %s", r.status_code)
            return []
        return _parse_search(r.json())
    except Exception as exc:
        logger.warning("wikipedia._search_titles: failed: %s", exc)
        return []


def _fetch_extract(title: str, *, timeout: float) -> tuple[str, str] | None:
    """Fetch the plain-text extract for one Wikipedia article title."""
    try:
        r = _retry_request(
            "GET",
            _WIKI_API,
            headers={"User-Agent": USER_AGENT},
            params={
                "action": "query",
                "prop": "extracts",
                "explaintext": "1",
                "titles": title,
                "format": "json",
                "redirects": "1",
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            logger.warning("wikipedia._fetch_extract: HTTP %s for %r", r.status_code, title)
            return None
        return _parse_extract(r.json())
    except Exception as exc:
        logger.warning("wikipedia._fetch_extract: failed for %r: %s", title, exc)
        return None


def search_and_fetch(
    query: str,
    claim: "Claim",
    *,
    timeout: float = 30.0,
) -> list[FetchedSource]:
    """Search Wikipedia and fetch plain-text extracts for top results.

    Returns a list of FetchedSource (one per successfully fetched article).
    Returns [] on any failure — never raises into the caller.
    """
    try:
        titles = _search_titles(query, timeout=timeout)
        if not titles:
            return []

        results: list[FetchedSource] = []
        for title in titles[:_MAX_TITLES]:
            pair = _fetch_extract(title, timeout=timeout)
            if pair is None:
                continue
            resolved_title, text = pair
            if not text:
                continue
            # Build a clean Wikipedia URL from the title
            url_title = resolved_title.replace(" ", "_")
            url = f"https://en.wikipedia.org/wiki/{url_title}"
            results.append(FetchedSource(
                channel="wikipedia",
                source_id=resolved_title,
                url=url,
                title=resolved_title,
                text=text,
                authority=AUTHORITY["wikipedia"],
            ))

        return results
    except Exception as exc:
        logger.warning("wikipedia.search_and_fetch: unexpected error: %s", exc)
        return []


__all__ = ["_parse_search", "_parse_extract", "search_and_fetch"]
