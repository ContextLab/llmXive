"""Open-access full-text retrieval + text extraction for claim grounding."""
from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, cast
from urllib.parse import urlsplit

import requests  # type: ignore[import-untyped]  # no stub package available

from llmxive.config import unpaywall_email
from llmxive.credentials import load_semantic_scholar_key
from llmxive.librarian.pdf_sample import PDF_MAX_BYTES, _download_pdf
from llmxive.librarian.search import USER_AGENT
from llmxive.librarian.verify import _fetch_from_arxiv, resolve_reference

logger = logging.getLogger(__name__)

_WS_RE = re.compile(r"[ \t]+")
_NL_RE = re.compile(r"\n{3,}")
_S2_BASE = "https://api.semanticscholar.org/graph/v1/paper"
_UNPAYWALL_BASE = "https://api.unpaywall.org/v2"


@dataclass(frozen=True, slots=True)
class RetrievedDoc:
    kind: str
    value: str
    tier: str | None
    full_text: str | None
    abstract: str | None
    title: str | None
    final_url: str
    error: str | None = None

    @property
    def readable(self) -> bool:
        return bool(self.full_text or self.abstract)


def _normalize_extracted(text: str, *, max_chars: int) -> str:
    """Collapse runs of spaces/blank lines and hard-cap length."""
    t = _WS_RE.sub(" ", text or "")
    t = _NL_RE.sub("\n\n", t)
    t = "\n".join(line.strip() for line in t.splitlines())
    t = t.strip()
    return t[:max_chars]


def extract_pdf_text(pdf_bytes: bytes, *, max_chars: int = 200_000) -> str:
    """Extract all page text from PDF bytes via pypdf.

    Returns '' on genuine PDF-parse failures. ImportError (missing pypdf
    dependency) propagates so the missing dependency surfaces clearly.
    The *max_chars* cap is applied after final normalisation; pre-loop
    accumulation break is approximate and avoids reading the whole file.
    """
    import pypdf  # ImportError propagates intentionally

    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        parts: list[str] = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue
            if sum(len(p) for p in parts) > max_chars:
                break
        return _normalize_extracted("\n".join(parts), max_chars=max_chars)
    except Exception:
        return ""


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip and data.strip():
            self.chunks.append(data)


def html_to_text(html: str, *, max_chars: int = 200_000) -> str:
    """Strip tags/scripts/styles from HTML, returning readable text."""
    p = _TextExtractor()
    try:
        p.feed(html or "")
    except Exception:
        pass
    return _normalize_extracted(" ".join(p.chunks), max_chars=max_chars)


def _unpaywall_pdf_url(payload: dict[str, Any]) -> str | None:
    if not isinstance(payload, dict) or not payload.get("is_oa"):
        return None
    loc = payload.get("best_oa_location") or {}
    url = loc.get("url_for_pdf") or loc.get("url") or None
    return cast("str | None", url)


def _s2_oa_pdf_url(payload: dict[str, Any]) -> str | None:
    oa = (payload or {}).get("openAccessPdf") or {}
    return cast("str | None", oa.get("url") or None)


def _preprint_pdf_urls(kind: str, value: str) -> list[str]:
    urls: list[str] = []
    if kind == "doi" and value.startswith("10.1101/"):
        for host in ("www.biorxiv.org", "www.medrxiv.org"):
            urls.append(f"https://{host}/content/{value}v1.full.pdf")
    if kind == "doi" and value.startswith(("10.31234/", "10.31219/")):
        osf_id = value.rsplit("/", 1)[-1]
        urls.append(f"https://osf.io/{osf_id}/download")
    return urls


def _pdf_from_url(url: str, *, timeout: float) -> str:
    # ``_download_pdf`` manages its own (module-level) timeout/size caps and
    # takes no timeout argument; ``timeout`` is accepted here only to keep the
    # cascade call sites uniform.
    data, _err = _download_pdf(url)
    return extract_pdf_text(data) if data else ""


def _fetch_url_text(value: str, *, timeout: float) -> tuple[str, str]:
    """Tier-5 direct-URL fetch, hardened like ``_download_pdf``.

    Returns ``(extracted_text, final_url)``. Only ``http``/``https`` schemes are
    fetched (others — ``file://``, ``ftp://`` — are treated as unreadable: no
    text). The response body is STREAMED and capped at :data:`PDF_MAX_BYTES`
    (50MB), so a hostile/huge URL cannot exhaust memory. Bounded timeout +
    redirects are kept. On any error returns ``("", "")``.

    # NOTE: SSRF residual — no private-IP/localhost block; F-19 only fetches
    # source URLs already extracted from produced docs, and the byte cap +
    # scheme restriction bound the blast radius.
    """
    scheme = urlsplit(value).scheme.lower()
    if scheme not in ("http", "https"):
        return "", ""
    try:
        r = requests.get(
            value, headers={"User-Agent": USER_AGENT},
            timeout=timeout, allow_redirects=True, stream=True,
        )
    except (requests.RequestException, OSError) as exc:
        logger.warning("grounding retrieve: URL fetch failed %s (%s)", value, exc)
        return "", ""
    try:
        final_url = r.url
        ctype = r.headers.get("content-type", "")
        chunks: list[bytes] = []
        total = 0
        try:
            for chunk in r.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                chunks.append(chunk)
                total += len(chunk)
                if total > PDF_MAX_BYTES:
                    logger.warning(
                        "grounding retrieve: URL body exceeded %d bytes; capping %s",
                        PDF_MAX_BYTES, value,
                    )
                    break
        except (requests.RequestException, OSError) as exc:
            logger.warning("grounding retrieve: URL stream failed %s (%s)", value, exc)
            return "", final_url
        raw = b"".join(chunks)
        if "pdf" in ctype.lower():
            return extract_pdf_text(raw), final_url
        text = raw.decode(r.encoding or "utf-8", errors="replace")
        return html_to_text(text), final_url
    finally:
        r.close()


def _get_json(
    url: str, *, timeout: float, headers: dict[str, str] | None = None
) -> dict[str, Any] | None:
    try:
        r = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, **(headers or {})},
            timeout=timeout,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        return data if isinstance(data, dict) else None
    except (requests.RequestException, ValueError, OSError) as exc:
        logger.warning("grounding retrieve: JSON GET failed %s (%s)", url, exc)
        return None


def retrieve(kind: str, value: str, *, timeout: float = 60.0) -> RetrievedDoc:
    """OA-first cascade. Returns the first tier that yields full text; falls
    back to an abstract-only doc; else an unreadable doc (caller flags)."""
    final_url = ""
    abstract: str | None = None
    title: str | None = None

    # Tier 1: arXiv
    if kind == "arxiv":
        t, a = _fetch_from_arxiv(value)
        title, abstract = t or None, a
        body = _pdf_from_url(f"https://arxiv.org/pdf/{value}", timeout=timeout)
        if body:
            return RetrievedDoc(kind, value, "arxiv", body, abstract, title,
                                f"https://arxiv.org/abs/{value}")

    # Tier 2: Unpaywall (DOI)
    if kind == "doi":
        email = unpaywall_email()
        if email:
            payload = _get_json(f"{_UNPAYWALL_BASE}/{value}?email={email}", timeout=timeout)
            if payload:
                abstract = abstract or payload.get("abstract")
                title = title or payload.get("title")
                pdf_url = _unpaywall_pdf_url(payload)
                if pdf_url:
                    body = _pdf_from_url(pdf_url, timeout=timeout)
                    if body:
                        return RetrievedDoc(kind, value, "unpaywall", body, abstract,
                                            title, pdf_url)

    # Tier 3: Semantic Scholar openAccessPdf (DOI or arXiv)
    s2_id = f"DOI:{value}" if kind == "doi" else (f"ARXIV:{value}" if kind == "arxiv" else None)
    if s2_id:
        key = load_semantic_scholar_key()
        headers = {"x-api-key": key} if key else None
        payload = _get_json(
            f"{_S2_BASE}/{s2_id}?fields=openAccessPdf,abstract,title",
            timeout=timeout, headers=headers,
        )
        if payload:
            abstract = abstract or payload.get("abstract")
            title = title or payload.get("title")
            pdf_url = _s2_oa_pdf_url(payload)
            if pdf_url:
                body = _pdf_from_url(pdf_url, timeout=timeout)
                if body:
                    return RetrievedDoc(kind, value, "s2", body, abstract, title, pdf_url)

    # Tier 4: preprint URL patterns
    for url in _preprint_pdf_urls(kind, value):
        body = _pdf_from_url(url, timeout=timeout)
        if body:
            return RetrievedDoc(kind, value, "preprint", body, abstract, title, url)

    # Tier 5: direct URL fetch (kind == url) — scheme-restricted + size-capped.
    if kind == "url":
        body, fetched_url = _fetch_url_text(value, timeout=timeout)
        final_url = fetched_url or final_url
        if body:
            return RetrievedDoc(kind, value, "url", body, abstract, title, final_url)

    # Abstract-only fallback
    if abstract:
        return RetrievedDoc(kind, value, "abstract", None, abstract, title, final_url)

    # Confirm existence for the error message; unreadable either way.
    try:
        outcome = resolve_reference(kind, value, timeout=timeout)
        err = "resolved but no open-access full text" if outcome.present else "unresolvable"
    except Exception as exc:  # existence probe is best-effort
        err = f"retrieval failed ({type(exc).__name__})"
    return RetrievedDoc(kind, value, None, None, None, title, final_url, error=err)
