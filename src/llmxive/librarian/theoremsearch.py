"""TheoremSearch backend client (spec 006, amends spec 005).

`TheoremSearchClient` is a third candidate-source backend for the
librarian — a peer of `SemanticScholarClient` and `ArxivClient`. It
queries https://api.theoremsearch.com/search (a semantic search over
theorem *statements* extracted from arXiv + other sources), and for
each **arXiv-sourced** theorem hit it resolves the source paper's
arXiv ID to the librarian's existing `Candidate` shape (via
`ArxivClient.get_by_id`), re-tagged with ``backend="theoremsearch"``.

Per spec 006:
  - Only arXiv-sourced hits are processed; non-arXiv sources
    (ProofWiki, Stacks Project, …) lack a DOI/arXiv ID and are
    skipped (reserved for Spec B / #114).
  - A TheoremSearch API failure raises `TransientBackendError`; the
    librarian's `_theoremsearch_candidates(...)` wrapper catches it
    and falls through to Semantic Scholar + arXiv — the librarian
    never *depends* on TheoremSearch being up (FR-A06).
  - Self-imposed rate limit (~1 req / 2 s, same pattern as
    `ArxivClient`) — the TheoremSearch API documents no rate limits.

Constitution Principle I: TheoremSearch is a *backend*, not a
competing agent. The librarian remains the single entry point + the
single verifier — TheoremSearch `Candidate`s flow through the
unchanged verification chain (URL resolves → title-overlap ≥0.7 →
summary-grounding ≥0.5 → LLM topical-relevance judge).
"""

from __future__ import annotations

import dataclasses
import logging
import re
import threading
import time

import requests  # type: ignore[import-untyped]  # installed, no stubs

from llmxive.backends.base import TransientBackendError
from llmxive.librarian.search import USER_AGENT, ArxivClient, Candidate

LOGGER = logging.getLogger(__name__)

API_URL = "https://api.theoremsearch.com/search"
DEFAULT_TIMEOUT_SECONDS = 30.0

# Spec 015 FR-040: bounded retry-with-backoff on TRANSIENT statuses (rate-limit /
# gateway / server) and timeouts before degrading. The librarian wrapper already
# treats a TransientBackendError as "theoremsearch unavailable" (optional enrichment).
MAX_TRANSIENT_RETRIES = 3
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
_RETRY_BACKOFF_BASE_SECONDS = 1.0

# Modern arXiv IDs (`1306.5434`, optionally `v2`) and old-style IDs
# (`hep-th/9901001`, optionally a `.XX` subcategory). `ArxivClient.
# get_by_id` accepts versioned IDs; we strip the version anyway so the
# resulting Candidate.primary_pointer matches an arXiv-search-sourced
# copy of the same paper (for dedup).
_MODERN_ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
_OLD_ARXIV_RE = re.compile(r"^[a-z\-]+(\.[A-Z]{2})?/\d{7}(v\d+)?$")
_VERSION_SUFFIX_RE = re.compile(r"v\d+$")


class TheoremSearchClient:
    """Wraps the TheoremSearch `/search` endpoint as a `Candidate` source."""

    def __init__(
        self,
        *,
        min_interval_seconds: float = 2.0,
        arxiv_client: ArxivClient | None = None,
        retry_backoff_base_seconds: float = _RETRY_BACKOFF_BASE_SECONDS,
    ) -> None:
        # TheoremSearch documents no rate limit; self-impose a conservative
        # one (one /search per librarian invocation, so 2s is plenty).
        self._min_interval = min_interval_seconds
        self._last_call_at: float = 0.0
        self._lock = threading.Lock()
        # Reuse the librarian's shared ArxivClient if provided so its
        # rate limiter is respected globally; else construct a fresh one.
        self._arxiv = arxiv_client or ArxivClient()
        # Exponential-backoff base for transient retries (tests pass 0).
        self._retry_backoff_base = retry_backoff_base_seconds

    def _backoff(self, attempt: int) -> None:
        if self._retry_backoff_base > 0:
            time.sleep(self._retry_backoff_base * (2 ** attempt))

    def _wait_for_slot(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call_at
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call_at = time.monotonic()

    def search(self, term: str, *, limit: int = 10) -> list[Candidate]:
        """Query TheoremSearch and return resolved arXiv `Candidate`s.

        Raises `TransientBackendError` on any HTTP error / network
        error / timeout / non-JSON / missing-`theorems`-array. May
        return `[]` if the response had zero usable arXiv-sourced hits
        (a normal outcome).
        """
        if not term or not term.strip():
            return []

        # FR-040: retry transient failures with exponential backoff, then degrade.
        resp = None
        last_error: str | None = None
        for attempt in range(MAX_TRANSIENT_RETRIES):
            self._wait_for_slot()
            try:
                resp = requests.post(
                    API_URL,
                    json={"query": term, "limit": limit},
                    headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
                    timeout=DEFAULT_TIMEOUT_SECONDS,
                )
            except requests.RequestException as exc:
                last_error = f"request failed: {exc}"
                self._backoff(attempt)
                continue
            if resp.status_code in RETRY_STATUSES:
                last_error = f"HTTP {resp.status_code}"
                LOGGER.warning(
                    "[theoremsearch] transient %s (attempt %d/%d); backing off",
                    last_error, attempt + 1, MAX_TRANSIENT_RETRIES,
                )
                resp = None
                self._backoff(attempt)
                continue
            break  # usable response (success or a non-transient error)

        if resp is None:
            # Exhausted retries on a transient condition → degrade gracefully
            # (the librarian wrapper catches this; theoremsearch is optional).
            raise TransientBackendError(
                f"TheoremSearch unavailable after {MAX_TRANSIENT_RETRIES} attempts "
                f"({last_error}) for query {term[:80]!r}"
            )

        if resp.status_code >= 400:
            # Non-transient 4xx/5xx → still TransientBackendError (never hard-fail),
            # but no retry (it will not recover on its own).
            raise TransientBackendError(
                f"TheoremSearch HTTP {resp.status_code} for query {term[:80]!r}"
            )

        try:
            body = resp.json()
        except ValueError as exc:
            raise TransientBackendError(f"TheoremSearch returned non-JSON: {exc}") from exc

        theorems = body.get("theorems") if isinstance(body, dict) else None
        if not isinstance(theorems, list):
            raise TransientBackendError(
                "TheoremSearch response missing a 'theorems' array"
            )

        # Sort by descending score (the `limit` request param already
        # bounds the count, but the API has been observed to return a
        # few extra — be defensive).
        try:
            theorems = sorted(theorems, key=lambda t: t.get("score", 0.0), reverse=True)
        except TypeError:
            pass  # heterogeneous scores → keep API order

        out: list[Candidate] = []
        seen_pointers: set[str] = set()
        for hit in theorems:
            if not isinstance(hit, dict):
                continue
            paper = hit.get("paper")
            if not isinstance(paper, dict):
                continue
            if paper.get("source") != "arXiv":
                LOGGER.debug(
                    "[theoremsearch] skipping non-arXiv source %r", paper.get("source")
                )
                continue
            raw_id = str(paper.get("paper_id") or "").strip()
            arxiv_id = _VERSION_SUFFIX_RE.sub("", raw_id)
            if not (_MODERN_ARXIV_RE.match(raw_id) or _OLD_ARXIV_RE.match(raw_id)):
                LOGGER.debug("[theoremsearch] skipping unparseable arXiv id %r", raw_id)
                continue
            cand = self._arxiv.get_by_id(arxiv_id)
            if cand is None:
                LOGGER.warning(
                    "[theoremsearch] arXiv id %r didn't resolve; dropping hit", arxiv_id
                )
                continue
            cand = dataclasses.replace(cand, backend="theoremsearch")
            if cand.primary_pointer in seen_pointers:
                continue  # two TheoremSearch hits → same paper → emit once
            seen_pointers.add(cand.primary_pointer)
            out.append(cand)
        return out


__all__ = ["API_URL", "TheoremSearchClient"]
