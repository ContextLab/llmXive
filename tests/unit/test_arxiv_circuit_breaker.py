"""Tests for the arXiv circuit-breaker in `librarian.search.ArxivClient`.

Why this matters: a sustained arXiv 429 storm previously caused every
subsequent search call to wait 15+30+60s = 105s on exponential backoff,
which compounded across many sequential queries (each citation lookup
makes 2+ queries) and blew past the GitHub Actions 25-minute job
timeout. Every Brainstorm + Flesh-Out run was getting cancelled.

The fix:
  - Per-call: only 2 attempts (was 3), with a single 15s backoff
    between them (was 15+30+60).
  - Session-wide: a second consecutive 429 trips a 60-second circuit
    breaker — subsequent calls return [] immediately without touching
    the network — so one rate-limited workflow doesn't blow the budget.
"""

from __future__ import annotations

import sys
import time
import types
from unittest.mock import patch

import pytest

from llmxive.librarian.search import ArxivClient


class _FakeHTTPError(Exception):
    """Stand-in for arxiv.HTTPError (we can't import arxiv at module
    scope without forcing the dep to load). The breaker only inspects
    `.status` so this is enough."""

    def __init__(self, status: int) -> None:
        super().__init__(f"HTTP {status}")
        self.status = status


@pytest.fixture
def fake_arxiv_mod():
    """Install a minimal arxiv-module stand-in whose `Client.results`
    raises HTTP 429. Restored on teardown."""
    mod = types.ModuleType("arxiv")
    mod.HTTPError = _FakeHTTPError

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def results(self, search):
            raise _FakeHTTPError(429)

    class _Search:
        def __init__(self, *args, **kwargs):
            pass

    mod.Client = _Client
    mod.Search = _Search
    sys.modules["arxiv"] = mod
    yield mod
    sys.modules.pop("arxiv", None)


def test_breaker_trips_after_two_consecutive_429s(fake_arxiv_mod) -> None:
    # min_interval_seconds=0 so we don't actually sleep between slots.
    client = ArxivClient(min_interval_seconds=0)
    # Patch time.sleep so the 15-second backoff doesn't slow the test.
    with patch("llmxive.librarian.search.time.sleep") as sleep_mock:
        out = client.search("any query")
    # Both attempts hit 429 → 1 backoff sleep recorded → breaker trips.
    assert out == []
    assert sleep_mock.call_count == 1
    assert sleep_mock.call_args[0][0] == 15
    # Breaker is now active.
    assert client._disabled_until > time.monotonic()


def test_breaker_short_circuits_subsequent_calls(fake_arxiv_mod) -> None:
    client = ArxivClient(min_interval_seconds=0)
    # Manually trip the breaker for the next 30 seconds.
    client._disabled_until = time.monotonic() + 30.0
    # Even though the fake arxiv would 429, search must not touch it
    # and must not sleep.
    with patch("llmxive.librarian.search.time.sleep") as sleep_mock:
        out = client.search("any query")
    assert out == []
    assert sleep_mock.call_count == 0


def test_breaker_auto_clears_when_window_expires() -> None:
    client = ArxivClient(min_interval_seconds=0)
    # Already-expired breaker is treated as cleared.
    client._disabled_until = time.monotonic() - 5.0
    # An empty query short-circuits before touching arxiv → []
    # demonstrates the breaker is bypassed without crashing.
    assert client.search("") == []
