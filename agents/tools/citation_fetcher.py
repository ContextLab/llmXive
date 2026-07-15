"""Citation-fetcher tool (T108).

⚠️ **Soft-deprecated post spec 005 (2026-05-06)** — this module's
title-overlap verification logic duplicates ``llmxive.librarian.verify.
verify_citation()``. New callers MUST use the librarian directly:

    from llmxive.librarian.verify import verify_citation

This file remains in place because:
  - The Reference-Validator Agent at
    ``src/llmxive/agents/reference_validator.py`` consumes this
    module's ``FetchResult`` shape (with a ``VerificationStatus``
    enum) which differs from the librarian's richer
    ``VerifiedCitation`` / ``VerificationFailure`` split.
  - Adapting reference_validator + its tests to the librarian shape
    is non-trivial; it was DEFERRED from spec 005 to a follow-up
    issue (per spec.md FR-014/15) to keep spec 005's blast radius
    contained. See ``notes/2026-05-06-spec-005-librarian-outline.md``
    for context.
  - The librarian's verification logic IS the canonical
    implementation going forward; this module's ``fetch_citation()``
    will be progressively migrated by the follow-up issue.

FR-022 (no new duplicates): adding a NEW caller of this module is
forbidden. Use the librarian. The CI test at
``tests/phase2/test_no_duplicate_lit_search.py`` (T070a) enforces
this.

Resolves a citation to its primary source and returns
`{fetched_title, fetched_authors, status}`. Distinguishes:
  - `verified`    — primary source reachable AND a REAL cited title
                    cross-checks (token-overlap ≥ threshold, or verbatim body
                    match). Reachability ALONE never earns verified (D14).
  - `mismatch`    — reachable but title doesn't match the cited title
  - `unreachable` — transient 5xx / timeout / DNS / 4xx (other than 404)
                    — caller may retry on the next scheduled run
  - `pending`     — present-but-unverified: reachable but the title can't be
                    cross-checked (access-gated body, redirect/bot-wall stub, or
                    no real cited title stored). Bounded retry / substitution
                    upstream; the reference gate treats it as blocking.

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


def _is_real_title(s: str) -> bool:
    """True iff ``s`` looks like an actual paper title (not a URL / DOI / bare id).

    Citation extraction sometimes stores the URL or DOI in the ``cited_title``
    field (or leaves it empty); comparing that against the fetched page title then
    yields ~0 overlap and a FALSE ``mismatch`` — even though the reference resolved
    to the REAL paper (``fetched_title`` is the genuine title). When there is no
    real title to cross-check, existence is NOT verification: the caller treats a
    resolved-but-uncrosscheckable reference as PENDING (present-but-unverified,
    bounded retry/substitution — recover a real title from DOI/arXiv metadata
    upstream, then title-match), never VERIFIED (issue #1139 D14)."""
    s = (s or "").strip()
    if not s:
        return False
    if s.lower().startswith(("http://", "https://", "doi:", "arxiv:")):
        return False
    if re.match(r"^10\.\d{4,9}/", s):          # bare DOI
        return False
    if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", s):  # bare arXiv id
        return False
    if " " not in s and len(s) < 30:           # a single token / id, not a title
        return False
    return True


#: Page titles that are NOT the document title — JS-redirect stubs, bot/cookie
#: walls, login/captcha interstitials. A real host RESOLVED (HTTP 200) but served
#: one of these instead of the paper's landing page, so the title can't be
#: cross-checked. Treat that like access-gating (PENDING — present but
#: unverifiable), not a fabricated-reference MISMATCH.
_BLOCK_TITLE_MARKERS = (
    "redirecting", "just a moment", "attention required", "access denied",
    "forbidden", "log in", "login", "sign in", "captcha", "are you a robot",
    "verifying you are human", "please wait", "checking your browser",
    "cookies", "consent", "service unavailable", "page not found",
)


def _is_block_title(s: str) -> bool:
    """True iff the fetched page title is a redirect/bot-wall/interstitial stub
    (or empty / too short to be a real title) rather than the document title."""
    s = (s or "").strip().lower()
    if len(s) < 6:
        return True
    return any(m in s for m in _BLOCK_TITLE_MARKERS)


def _norm_phrase(s: str) -> str:
    """Lowercase + reduce to a space-joined ``[a-z0-9]`` token stream (order kept),
    so a title compares cleanly across markup/punctuation/whitespace differences."""
    return " ".join(re.findall(r"[a-z0-9]+", (s or "").lower()))


def _title_in_body(cited_title: str, html_text: str) -> bool:
    """True iff the cited article title appears VERBATIM (as a contiguous token
    phrase) in the fetched page body.

    Publisher article pages (msp.org, ScienceDirect, Springer, …) routinely serve a
    GENERIC ``<title>`` — the journal/issue, e.g. "Algebraic & Geometric Topology
    Volume 6, issue 5" — while the real article title sits in the page body / table
    of contents. The ``<title>``-only overlap check then FALSE-flags a real article
    as a MISMATCH. Confirming the cited title is physically present on the resolved
    page upgrades MISMATCH -> VERIFIED. This STRENGTHENS the anti-fabrication gate
    (it demands the exact title actually appear) rather than weakening it: a
    fabricated title is absent from the real page and stays MISMATCH. Require >=4
    tokens so a short title can't match coincidentally."""
    ct = _norm_phrase(cited_title)
    if len(ct.split()) < 4:
        return False
    body = _norm_phrase(re.sub(r"<[^>]+>", " ", html_text or ""))
    return ct in body


def _classify_match(cited_title: str, fetched_title: str) -> VerificationStatus:
    """Decide verified / mismatch / pending by title-token-overlap.

    The reference has already RESOLVED (HTTP 200) by the time we get here, so it
    EXISTS — the only question is whether we can confirm the TITLE. When we can't
    (the page served a redirect/bot-wall stub, or no readable title, or the citation
    never stored a real title), we DEFER (PENDING — present but unverifiable),
    NOT MISMATCH. A genuinely fabricated reference fails upstream (404 / DNS /
    conn-error -> mismatch/unreachable), so this preserves the anti-fabrication gate
    while it stops false-flagging real-but-bot-hostile academic sources."""
    ft = (fetched_title or "").strip()
    title_unreadable = (not ft) or _is_block_title(ft)
    if not _is_real_title(cited_title):
        # No real cited title to cross-check (the citation stored a URL/DOI/id).
        # Existence != verification (issue #1139 D14): a reference that RESOLVED
        # to a live, readable page but whose cited title we cannot cross-check is
        # PRESENT-BUT-UNVERIFIED, so DEFER to PENDING (bounded retry/substitution:
        # resolve DOI/arXiv metadata to recover a real title, then title-match).
        # Only a real cited-title token-overlap match (below) or a verbatim
        # body match (``_title_in_body`` in the caller) earns VERIFIED.
        return VerificationStatus.PENDING
    if title_unreadable:
        # We have a real cited title but the page didn't give us a readable one to
        # compare against — present but unverifiable, not fabricated.
        return VerificationStatus.PENDING
    overlap = title_overlap(cited_title, ft)
    if overlap >= CITATION_TITLE_OVERLAP_THRESHOLD:
        return VerificationStatus.VERIFIED
    return VerificationStatus.MISMATCH


def _access_gated(status_code: int, url: str) -> FetchResult | None:
    """A real host that ANSWERED with access-gating (401 / 403 / 429: paywall,
    bot-block, or rate-limit) — the reference EXISTS, an automated client just
    can't read the body to title-match it. Classify as PENDING: honestly
    unverified, but NON-blocking (the research-accept / paper-accept gate blocks
    only UNREACHABLE / MISMATCH). This stops real-but-bot-hostile academic sources
    (publisher pages, OEIS behind Cloudflare, KnotInfo, rate-limited registrars)
    from being false-flagged as fabricated and HARD-blocking advancement. A
    genuinely fabricated reference fails differently — a made-up domain DNS-fails
    and a made-up path 404s (still UNREACHABLE / MISMATCH below) — so this does NOT
    weaken the anti-fabrication gate. Returns None for any other status."""
    if status_code in (401, 403, 429):
        return FetchResult(
            status=VerificationStatus.PENDING,
            fetched_url=url,
            error=f"access-gated (HTTP {status_code}); host present, title unverifiable",
        )
    return None


def _clean_url(value: str) -> str:
    """Strip trailing markdown/punctuation junk that citation extraction sometimes
    leaves on a URL (e.g. a trailing backtick ``https://katlas.org` `` from an
    inline-code span, or a closing bracket/paren/quote). Such junk makes an
    otherwise-real URL fail to resolve -> a FALSE unreachable."""
    return (value or "").strip().rstrip("`'\"<>)]}.,;")


def _fetch_url(value: str, *, cited_title: str, timeout: float) -> FetchResult:
    value = _clean_url(value)
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
    gated = _access_gated(resp.status_code, str(resp.url))
    if gated is not None:
        return gated
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
    # _classify_match handles the no-real-title case (empty, or a URL/DOI stored in
    # cited_title): reachability + a non-empty fetched title -> verified.
    status = _classify_match(cited_title, fetched_title)
    if status == VerificationStatus.MISMATCH and _title_in_body(cited_title, text):
        # The <title> was generic (e.g. a publisher journal/issue title) but the
        # cited article title is physically present in the resolved page body -> a
        # REAL article on the right page, not a fabricated reference.
        status = VerificationStatus.VERIFIED
        if not fetched_title or _is_block_title(fetched_title):
            fetched_title = cited_title
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
        import arxiv
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
    # arXiv DOIs (10.48550/arXiv.XXXX) are DataCite-minted and NOT in CrossRef, so
    # the CrossRef lookup below 404s -> a FALSE "DOI not found" mismatch on a real
    # paper. Route them to the arXiv API (which has them) instead.
    ax = re.match(r"10\.48550/arxiv\.(.+)$", doi, re.IGNORECASE)
    if ax:
        return _fetch_arxiv(ax.group(1), cited_title=cited_title, timeout=timeout)
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
    gated = _access_gated(resp.status_code, url)
    if gated is not None:
        return gated
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
    gated = _access_gated(resp.status_code, url)
    if gated is not None:
        return gated
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
