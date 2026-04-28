"""Citation-fetcher tool (T108).

Resolves a citation to its primary source and returns
`{fetched_title, fetched_authors, status}`. Distinguishes:
  - `verified`    — primary source reachable AND title-overlap ≥ threshold
  - `mismatch`    — reachable but title doesn't match the cited title
  - `unreachable` — transient 5xx / timeout / DNS / 4xx (other than 404)
                    — caller may retry on the next scheduled run
  - `pending`     — should never be returned; caller's responsibility

Per Constitution Principle II (Verified Accuracy), this tool MUST hit
the primary source on every call. No caching, no faking — the
Reference-Validator Agent depends on a live fetch each invocation.

Supported citation kinds (Citation.kind):
  url     — direct HTTP GET
  arxiv   — arXiv API lookup
  doi     — Crossref metadata lookup
  dataset — best-effort: Zenodo / HuggingFace datasets endpoints
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx

from llmxive.config import CITATION_TITLE_OVERLAP_THRESHOLD
from llmxive.state.citations import title_overlap
from llmxive.types import VerificationStatus

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT_S = 12.0
DEFAULT_USER_AGENT = "llmxive-citation-fetcher/0.1 (+https://github.com/ContextLab/llmXive)"

_ARXIV_ID_RE = re.compile(r"\b(\d{4}\.\d{4,5})(v\d+)?\b")
_DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)


@dataclass
class FetchResult:
    """Output contract used by the Reference-Validator Agent."""

    status: VerificationStatus
    fetched_url: str = ""
    fetched_title: str = ""
    fetched_authors: list[str] | None = None
    error: str = ""


def _classify_match(cited_title: str, fetched_title: str) -> VerificationStatus:
    """Decide verified vs mismatch by title-token-overlap threshold."""
    overlap = title_overlap(cited_title, fetched_title)
    if overlap >= CITATION_TITLE_OVERLAP_THRESHOLD:
        return VerificationStatus.VERIFIED
    return VerificationStatus.MISMATCH


def _fetch_url(value: str, *, cited_title: str, timeout: float) -> FetchResult:
    headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "text/html,*/*;q=0.5"}
    try:
        with httpx.Client(
            timeout=timeout, headers=headers, follow_redirects=True
        ) as client:
            resp = client.get(value)
    except (httpx.HTTPError, ConnectionError) as exc:
        return FetchResult(
            status=VerificationStatus.UNREACHABLE,
            fetched_url=value,
            error=str(exc),
        )
    if resp.status_code == 404:
        return FetchResult(
            status=VerificationStatus.MISMATCH,
            fetched_url=str(resp.url),
            error="404 Not Found",
        )
    if resp.status_code >= 400:
        return FetchResult(
            status=VerificationStatus.UNREACHABLE,
            fetched_url=str(resp.url),
            error=f"HTTP {resp.status_code}",
        )

    # Extract <title> from HTML; for non-HTML content, fall back to the
    # final URL path's last segment.
    text = resp.text or ""
    title_match = re.search(r"<title[^>]*>(?P<title>.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    fetched_title = title_match.group("title").strip() if title_match else ""
    if not fetched_title and value:
        fetched_title = value.rsplit("/", 1)[-1]
    if not cited_title:
        # No claim to match against; reachability + non-empty title only.
        status = VerificationStatus.VERIFIED if fetched_title else VerificationStatus.MISMATCH
    else:
        status = _classify_match(cited_title, fetched_title)
    return FetchResult(
        status=status,
        fetched_url=str(resp.url),
        fetched_title=fetched_title,
    )


def _fetch_arxiv(value: str, *, cited_title: str, timeout: float) -> FetchResult:
    arxiv_id = value.strip()
    m = _ARXIV_ID_RE.search(arxiv_id)
    if m:
        arxiv_id = m.group(1)
    try:
        # arxiv package handles parsing the Atom feed; lazy-import.
        import arxiv  # type: ignore[import-not-found]
    except ImportError as exc:
        return FetchResult(
            status=VerificationStatus.UNREACHABLE,
            error=f"arxiv package missing: {exc}",
        )
    try:
        results = list(arxiv.Search(id_list=[arxiv_id]).results())
    except Exception as exc:
        return FetchResult(
            status=VerificationStatus.UNREACHABLE,
            error=str(exc),
        )
    if not results:
        return FetchResult(
            status=VerificationStatus.MISMATCH,
            fetched_url=f"https://arxiv.org/abs/{arxiv_id}",
            error="arXiv ID not found",
        )
    first = results[0]
    fetched_title = (first.title or "").strip()
    return FetchResult(
        status=_classify_match(cited_title, fetched_title),
        fetched_url=first.entry_id or f"https://arxiv.org/abs/{arxiv_id}",
        fetched_title=fetched_title,
        fetched_authors=[a.name for a in first.authors],
    )


def _fetch_doi(value: str, *, cited_title: str, timeout: float) -> FetchResult:
    doi = value.strip()
    m = _DOI_RE.search(doi)
    if m:
        doi = m.group(0)
    url = f"https://api.crossref.org/works/{doi}"
    headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"}
    try:
        with httpx.Client(timeout=timeout, headers=headers) as client:
            resp = client.get(url)
    except (httpx.HTTPError, ConnectionError) as exc:
        return FetchResult(
            status=VerificationStatus.UNREACHABLE,
            error=str(exc),
        )
    if resp.status_code == 404:
        return FetchResult(
            status=VerificationStatus.MISMATCH,
            fetched_url=url,
            error="DOI not found",
        )
    if resp.status_code >= 400:
        return FetchResult(
            status=VerificationStatus.UNREACHABLE,
            fetched_url=url,
            error=f"HTTP {resp.status_code}",
        )
    try:
        body = resp.json()
    except ValueError as exc:
        return FetchResult(
            status=VerificationStatus.UNREACHABLE,
            fetched_url=url,
            error=f"non-JSON response: {exc}",
        )
    msg = body.get("message", {}) if isinstance(body, dict) else {}
    titles = msg.get("title") or []
    fetched_title = titles[0].strip() if titles else ""
    authors_raw = msg.get("author") or []
    authors = [
        f"{a.get('given', '')} {a.get('family', '')}".strip()
        for a in authors_raw
        if a.get("family")
    ]
    return FetchResult(
        status=_classify_match(cited_title, fetched_title),
        fetched_url=msg.get("URL") or url,
        fetched_title=fetched_title,
        fetched_authors=authors,
    )


def _fetch_dataset(value: str, *, cited_title: str, timeout: float) -> FetchResult:
    """Best-effort dataset resolver — try Zenodo and HuggingFace.

    `value` may be a Zenodo record id (e.g., "10.5281/zenodo.1234567"
    or "1234567"), a HuggingFace dataset slug ("user/dataset"), or a
    direct URL — in which case we fall through to URL fetch.
    """
    v = value.strip()
    if v.startswith("http://") or v.startswith("https://"):
        return _fetch_url(v, cited_title=cited_title, timeout=timeout)
    if v.startswith("10.") or "zenodo" in v.lower():
        # Try DOI path.
        return _fetch_doi(v, cited_title=cited_title, timeout=timeout)
    # HuggingFace datasets API.
    headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"}
    url = f"https://huggingface.co/api/datasets/{v}"
    try:
        with httpx.Client(timeout=timeout, headers=headers) as client:
            resp = client.get(url)
    except (httpx.HTTPError, ConnectionError) as exc:
        return FetchResult(status=VerificationStatus.UNREACHABLE, error=str(exc))
    if resp.status_code == 404:
        return FetchResult(
            status=VerificationStatus.MISMATCH,
            fetched_url=url,
            error="HF dataset not found",
        )
    if resp.status_code >= 400:
        return FetchResult(
            status=VerificationStatus.UNREACHABLE,
            fetched_url=url,
            error=f"HTTP {resp.status_code}",
        )
    try:
        body = resp.json()
    except ValueError as exc:
        return FetchResult(
            status=VerificationStatus.UNREACHABLE,
            fetched_url=url,
            error=f"non-JSON response: {exc}",
        )
    fetched_title = body.get("id") or v
    return FetchResult(
        status=_classify_match(cited_title, fetched_title),
        fetched_url=f"https://huggingface.co/datasets/{v}",
        fetched_title=fetched_title,
    )


def fetch_citation(
    *,
    kind: str,
    value: str,
    cited_title: str = "",
    timeout: float = DEFAULT_TIMEOUT_S,
) -> FetchResult:
    """Resolve a citation against its primary source.

    `kind` MUST be one of {"url", "arxiv", "doi", "dataset"}.
    """
    if kind == "url":
        return _fetch_url(value, cited_title=cited_title, timeout=timeout)
    if kind == "arxiv":
        return _fetch_arxiv(value, cited_title=cited_title, timeout=timeout)
    if kind == "doi":
        return _fetch_doi(value, cited_title=cited_title, timeout=timeout)
    if kind == "dataset":
        return _fetch_dataset(value, cited_title=cited_title, timeout=timeout)
    raise ValueError(f"unsupported citation kind: {kind!r}")


__all__ = ["FetchResult", "fetch_citation"]
