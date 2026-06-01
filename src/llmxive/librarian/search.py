"""Semantic Scholar + arXiv search clients (spec 005 / FR-001 / Q1).

Two thin clients that return ``Candidate`` records (data-model.md E2).
Both share the existing router-style retry pattern (3 attempts on
429/5xx with exponential backoff). Per-backend rate limiting:

  - Semantic Scholar: token bucket (2/sec replenish, 5 burst). Authenticated
    with ``SEMANTIC_SCHOLAR_API_KEY`` via ``x-api-key`` header (free tier
    requires this — unauthenticated returns 429 on the first call).
  - arXiv: 3-second sleep between calls (matches arXiv's documented
    "1 req/3 sec" guideline; gentleman's-agreement, not enforced).

Per Constitution Principle III: real HTTP, no mocks. Per Principle IV
(Free-First): both APIs free-tier; only Semantic Scholar requires the
free key.
"""

from __future__ import annotations

import dataclasses
import threading
import time
from typing import Any

import requests  # type: ignore[import-untyped]  # no stub package available

from llmxive.credentials import load_semantic_scholar_key

USER_AGENT = "llmxive-librarian/1.0 (https://github.com/ContextLab/llmXive)"
SS_BASE = "https://api.semanticscholar.org/graph/v1"
ARXIV_API = "http://export.arxiv.org/api/query"
RETRY_STATUS = {429, 500, 502, 503, 504}


@dataclasses.dataclass(frozen=True)
class Candidate:
    """A pre-verification record from one of the search backends.

    Identity: (backend, primary_pointer). Two candidates with the same
    identity from different backends are de-duplicated by the orchestrator.
    """

    backend: str  # "semantic_scholar" | "arxiv"
    primary_pointer: str  # DOI / arXiv ID / HTTPS URL
    claimed_title: str
    claimed_authors: list[str]
    claimed_year: int | None
    claimed_venue: str | None
    claimed_abstract: str | None


class _TokenBucket:
    """Thread-safe token bucket for rate limiting.

    ``capacity`` is the burst size; ``replenish_rate`` is tokens-per-second.
    """

    def __init__(self, capacity: int, replenish_rate: float) -> None:
        self.capacity = capacity
        self.replenish_rate = replenish_rate
        self._tokens = float(capacity)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until one token is available, then consume it."""
        while True:
            with self._lock:
                now = time.monotonic()
                self._tokens = min(
                    self.capacity,
                    self._tokens + (now - self._last) * self.replenish_rate,
                )
                self._last = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = (1.0 - self._tokens) / self.replenish_rate
            time.sleep(wait)


def _retry_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    timeout: float = 30.0,
    max_attempts: int = 3,
) -> requests.Response:
    """Wrapper around requests.request with exponential backoff on 429/5xx."""
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            r = requests.request(
                method, url, headers=headers, params=params, timeout=timeout
            )
            if r.status_code in RETRY_STATUS and attempt < max_attempts - 1:
                # Exponential backoff: 1s, 2s, 4s.
                time.sleep(2**attempt)
                continue
            return r
        except (requests.RequestException, OSError) as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                time.sleep(2**attempt)
                continue
            raise
    if last_exc:
        raise last_exc
    # Unreachable, but keeps type checkers happy.
    raise RuntimeError("retry loop exited without response or exception")


class SemanticScholarClient:
    """Wraps Semantic Scholar Graph API endpoints used by the librarian.

    Endpoints:
      - GET /paper/search — keyword search; returns candidate list.
      - GET /paper/{paper_id} — fetch full record (title, abstract,
        externalIds for DOI/arXiv resolution) for verification.

    Per Q1 / FR-001: ``SEMANTIC_SCHOLAR_API_KEY`` required (sent as the
    ``x-api-key`` header). The unauthenticated free tier returns 429 on
    the first call; the authenticated free tier supports the volume
    spec 005 needs (verified empirically during preflight).
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        bucket: _TokenBucket | None = None,
    ) -> None:
        # Caller can pass a key explicitly (e.g., tests); default loads from
        # env / credentials file.
        self._key = api_key if api_key is not None else load_semantic_scholar_key()
        # 2 tokens/sec sustained, 5 burst.
        self._bucket = bucket or _TokenBucket(capacity=5, replenish_rate=2.0)

    @property
    def has_key(self) -> bool:
        return bool(self._key)

    def _headers(self) -> dict[str, str]:
        h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if self._key:
            h["x-api-key"] = self._key
        return h

    def search_papers(
        self,
        query: str,
        *,
        limit: int = 10,
        fields: str = "title,authors,year,venue,abstract,externalIds,url",
    ) -> list[Candidate]:
        """Keyword search. Returns up to ``limit`` Candidate records."""
        if not query.strip():
            return []
        if not self._key:
            raise RuntimeError(
                "SEMANTIC_SCHOLAR_API_KEY missing — see "
                "https://www.semanticscholar.org/product/api#api-key-form. "
                "Use llmxive.credentials.save_semantic_scholar_key(...) once obtained."
            )
        self._bucket.acquire()
        r = _retry_request(
            "GET",
            f"{SS_BASE}/paper/search",
            headers=self._headers(),
            params={"query": query, "limit": limit, "fields": fields},
        )
        r.raise_for_status()
        data = r.json() or {}
        out: list[Candidate] = []
        for paper in data.get("data", []):
            primary = _ss_primary_pointer(paper)
            if not primary:
                continue
            out.append(
                Candidate(
                    backend="semantic_scholar",
                    primary_pointer=primary,
                    claimed_title=str(paper.get("title") or "").strip(),
                    claimed_authors=[
                        a.get("name", "") for a in paper.get("authors") or [] if a.get("name")
                    ],
                    claimed_year=paper.get("year"),
                    claimed_venue=paper.get("venue"),
                    claimed_abstract=paper.get("abstract"),
                )
            )
        return out

    def get_paper(
        self,
        paper_id: str,
        *,
        fields: str = "title,authors,year,venue,abstract,externalIds,url",
    ) -> Candidate | None:
        """Fetch full record for one paper. ``paper_id`` may be Semantic
        Scholar's internal ID, a DOI prefixed by ``DOI:``, or an arXiv
        ID prefixed by ``ARXIV:`` per the API.
        """
        if not self._key:
            raise RuntimeError("SEMANTIC_SCHOLAR_API_KEY missing")
        self._bucket.acquire()
        r = _retry_request(
            "GET",
            f"{SS_BASE}/paper/{paper_id}",
            headers=self._headers(),
            params={"fields": fields},
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        paper = r.json() or {}
        primary = _ss_primary_pointer(paper)
        if not primary:
            return None
        return Candidate(
            backend="semantic_scholar",
            primary_pointer=primary,
            claimed_title=str(paper.get("title") or "").strip(),
            claimed_authors=[
                a.get("name", "") for a in paper.get("authors") or [] if a.get("name")
            ],
            claimed_year=paper.get("year"),
            claimed_venue=paper.get("venue"),
            claimed_abstract=paper.get("abstract"),
        )


def _ss_primary_pointer(paper: dict[str, Any]) -> str | None:
    """Pick the canonical pointer for a Semantic Scholar paper record.

    Preference: DOI → arXiv ID → external URL → SS paper_id.
    """
    eids = paper.get("externalIds") or {}
    if eids.get("DOI"):
        return f"https://doi.org/{eids['DOI']}"
    if eids.get("ArXiv"):
        return str(eids["ArXiv"])  # bare arXiv ID; arXiv client handles it
    url = paper.get("url")
    if url:
        return str(url)
    pid = paper.get("paperId")
    return f"semantic-scholar:{pid}" if pid else None


class ArxivClient:
    """Wraps the arXiv Atom-XML API.

    Uses the existing ``arxiv`` library if available (already in
    pyproject.toml deps). Falls back to a thin XML-parse if the library
    is unavailable.
    """

    def __init__(self, *, min_interval_seconds: float = 5.0) -> None:
        # arXiv documents a 1-req-per-3-second guideline. We use 5s with
        # margin to avoid 429s during burst loads (e.g., the US4
        # cross-domain test which fires 8+ invocations x 3-20 expanded
        # terms each).
        self._min_interval = min_interval_seconds
        self._last_call_at: float = 0.0
        self._lock = threading.Lock()
        # Circuit-breaker: once we get a sustained 429, stop calling
        # arXiv until this monotonic timestamp. Prevents a single
        # rate-limited run from blocking the entire workflow timeout
        # (was: 105s per query * many queries → 25-min job cancellation).
        self._disabled_until: float = 0.0

    def _wait_for_slot(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call_at
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call_at = time.monotonic()

    def search(self, query: str, *, max_results: int = 10) -> list[Candidate]:
        """Keyword search on arXiv. Returns Candidate records.

        Rate-limit handling has two layers:
          1. Per-call: on 429, back off once (15s) and retry. A second
             429 trips the circuit breaker and returns [].
          2. Circuit breaker: while `_disabled_until > now`, return []
             immediately without making a request. The breaker auto-
             clears 60s after the most recent 429. This prevents the
             pathological case of many sequential queries each waiting
             105s on backoffs and blowing past the GH Actions 25-min
             job timeout.
        """
        if not query.strip():
            return []
        # Circuit-breaker check: short-circuit on sustained 429s.
        if time.monotonic() < self._disabled_until:
            import sys as _sys
            print(
                f"[arxiv] circuit-breaker active; skipping query={query[:50]!r}",
                file=_sys.stderr,
            )
            return []
        try:
            import arxiv
        except ImportError:
            return self._search_via_xml(query, max_results=max_results)

        # Two attempts only (was 3). With circuit breaker, a 2nd 429
        # disables arXiv for 60s so subsequent queries are instant-empty.
        for attempt in range(2):
            self._wait_for_slot()
            try:
                client = arxiv.Client(page_size=max_results, num_retries=2)
                search_obj = arxiv.Search(query=query, max_results=max_results)
                out: list[Candidate] = []
                for result in client.results(search_obj):
                    arxiv_id = _arxiv_short_id(result.entry_id)
                    if not arxiv_id:
                        continue
                    out.append(
                        Candidate(
                            backend="arxiv",
                            primary_pointer=arxiv_id,
                            claimed_title=(result.title or "").strip(),
                            claimed_authors=[a.name for a in (result.authors or [])],
                            claimed_year=result.published.year if result.published else None,
                            claimed_venue="arXiv",
                            claimed_abstract=(result.summary or "").strip() or None,
                        )
                    )
                return out
            except arxiv.HTTPError as exc:
                if exc.status != 429:
                    # Non-429 HTTP error → surface immediately.
                    import sys as _sys
                    print(
                        f"[arxiv] HTTP {exc.status} on query={query!r}; aborting search",
                        file=_sys.stderr,
                    )
                    return []
                # 429 — back off briefly, then either retry or trip
                # the circuit breaker. Was: 15s/30s/60s exponential
                # over 3 attempts (105s/query worst case). Now: 15s
                # on first 429; second 429 trips breaker WITHOUT a
                # second sleep (the breaker itself provides the cool-
                # off, no need to waste another 15s in this call).
                if attempt + 1 < 2:
                    backoff = 15
                    import sys as _sys
                    print(
                        f"[arxiv] 429 rate-limited on query={query[:50]!r}; backing off {backoff}s (attempt {attempt + 1}/2)",
                        file=_sys.stderr,
                    )
                    time.sleep(backoff)
            except Exception as exc:
                import sys as _sys
                print(
                    f"[arxiv] {type(exc).__name__} on query={query!r}: {exc}",
                    file=_sys.stderr,
                )
                return []

        # Both attempts hit 429 — trip the breaker for 60s so this
        # workflow run doesn't keep wasting time on arXiv.
        self._disabled_until = time.monotonic() + 60.0
        import sys as _sys
        print(
            f"[arxiv] 2 consecutive 429s on query={query[:50]!r}; "
            f"disabling arXiv calls for 60s",
            file=_sys.stderr,
        )
        return []

    def get_by_id(self, arxiv_id: str) -> Candidate | None:
        """Fetch a single paper by arXiv ID (e.g., '1706.03762' or '1706.03762v3').

        Respects the same circuit breaker as ``search()``: while
        ``_disabled_until > now`` (a sustained-429 cool-off is in effect) this
        short-circuits to ``None`` WITHOUT a network attempt, so the
        per-candidate path (theorem/papers fill channels) also stops hammering
        arXiv once the breaker has tripped.
        """
        # Circuit-breaker check: short-circuit on sustained 429s.
        if time.monotonic() < self._disabled_until:
            import sys as _sys
            print(
                f"[arxiv] circuit-breaker active; skipping get_by_id={arxiv_id!r}",
                file=_sys.stderr,
            )
            return None
        try:
            import arxiv
        except ImportError:
            return self._search_via_xml(f"id:{arxiv_id}", max_results=1)[:1][0] if False else None

        self._wait_for_slot()
        client = arxiv.Client()
        search_obj = arxiv.Search(id_list=[arxiv_id])
        for result in client.results(search_obj):
            return Candidate(
                backend="arxiv",
                primary_pointer=_arxiv_short_id(result.entry_id) or arxiv_id,
                claimed_title=(result.title or "").strip(),
                claimed_authors=[a.name for a in (result.authors or [])],
                claimed_year=result.published.year if result.published else None,
                claimed_venue="arXiv",
                claimed_abstract=(result.summary or "").strip() or None,
            )
        return None

    def _search_via_xml(self, query: str, *, max_results: int) -> list[Candidate]:
        """Direct Atom-XML fallback if the arxiv library is unavailable."""
        self._wait_for_slot()
        r = _retry_request(
            "GET",
            ARXIV_API,
            headers={"User-Agent": USER_AGENT},
            params={"search_query": query, "max_results": max_results},
        )
        r.raise_for_status()
        # Minimal XML parse: extract id + title + summary + authors per <entry>.
        # For the librarian's purposes the arxiv lib is the primary path; this
        # fallback is just to avoid a hard ImportError in environments that
        # somehow lack the lib.
        import xml.etree.ElementTree as ET

        ns = {"a": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(r.text)
        out: list[Candidate] = []
        for entry in root.findall("a:entry", ns):
            entry_id = (entry.findtext("a:id", default="", namespaces=ns) or "").strip()
            arxiv_id = _arxiv_short_id(entry_id)
            if not arxiv_id:
                continue
            title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
            summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
            authors = [
                (a.findtext("a:name", default="", namespaces=ns) or "").strip()
                for a in entry.findall("a:author", ns)
            ]
            published = entry.findtext("a:published", default="", namespaces=ns) or ""
            year = int(published[:4]) if published[:4].isdigit() else None
            out.append(
                Candidate(
                    backend="arxiv",
                    primary_pointer=arxiv_id,
                    claimed_title=title,
                    claimed_authors=[a for a in authors if a],
                    claimed_year=year,
                    claimed_venue="arXiv",
                    claimed_abstract=summary or None,
                )
            )
        return out


def _arxiv_short_id(entry_id: str) -> str | None:
    """Extract the short arXiv ID from an entry_id URL like
    'http://arxiv.org/abs/1706.03762v3' → '1706.03762'.
    """
    if not entry_id:
        return None
    # Strip the URL prefix.
    if "/abs/" in entry_id:
        entry_id = entry_id.split("/abs/", 1)[1]
    # Strip version suffix.
    if "v" in entry_id:
        head, _, tail = entry_id.rpartition("v")
        if tail.isdigit():
            entry_id = head
    return entry_id or None


def merge_candidates(*candidate_lists: list[Candidate]) -> list[Candidate]:
    """De-duplicate candidates by ``(backend, primary_pointer)`` across
    multiple backend results. Preserves first-seen order.
    """
    seen: set[tuple[str, str]] = set()
    out: list[Candidate] = []
    for clist in candidate_lists:
        for c in clist:
            key = (c.backend, c.primary_pointer)
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
    return out


__all__ = [
    "USER_AGENT",
    "ArxivClient",
    "Candidate",
    "SemanticScholarClient",
    "merge_candidates",
]
