"""FR-040 (spec 015 T034): theoremsearch retries transient 429/503/5xx with
backoff, then degrades gracefully (TransientBackendError, which the librarian
wrapper already treats as "optional source unavailable"). Non-transient 4xx are
not retried. A controlled fake `requests.post` exercises the retry logic (the
external API cannot be made to return 503 on demand; the happy path has a real-call
test in tests/real_call/)."""

from __future__ import annotations

import pytest

from llmxive.backends.base import TransientBackendError
from llmxive.librarian import theoremsearch as ts


class _Resp:
    def __init__(self, status: int, body: dict | None = None):
        self.status_code = status
        self._body = body or {}

    def json(self) -> dict:
        return self._body


def _client() -> ts.TheoremSearchClient:
    # backoff 0 + interval 0 so the test neither sleeps nor rate-limits.
    return ts.TheoremSearchClient(min_interval_seconds=0.0, retry_backoff_base_seconds=0.0)


def test_retries_transient_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def fake_post(*a, **k):
        calls["n"] += 1
        if calls["n"] < 3:
            return _Resp(503)              # transient -> retry
        return _Resp(200, {"theorems": []})  # finally OK (no arXiv hits -> [])

    monkeypatch.setattr(ts.requests, "post", fake_post)
    assert _client().search("banach fixed point") == []
    assert calls["n"] == 3                 # two retries then success


def test_degrades_after_exhausting_retries(monkeypatch):
    calls = {"n": 0}

    def fake_post(*a, **k):
        calls["n"] += 1
        return _Resp(429)                  # always rate-limited

    monkeypatch.setattr(ts.requests, "post", fake_post)
    with pytest.raises(TransientBackendError):
        _client().search("x")
    assert calls["n"] == ts.MAX_TRANSIENT_RETRIES  # bounded retries, then degrade


def test_non_transient_4xx_not_retried(monkeypatch):
    calls = {"n": 0}

    def fake_post(*a, **k):
        calls["n"] += 1
        return _Resp(400)                  # client error -> won't recover

    monkeypatch.setattr(ts.requests, "post", fake_post)
    with pytest.raises(TransientBackendError):
        _client().search("x")
    assert calls["n"] == 1                 # not retried


def test_request_exception_retried_then_degrades(monkeypatch):
    calls = {"n": 0}

    def fake_post(*a, **k):
        calls["n"] += 1
        raise ts.requests.RequestException("connection reset")

    monkeypatch.setattr(ts.requests, "post", fake_post)
    with pytest.raises(TransientBackendError):
        _client().search("x")
    assert calls["n"] == ts.MAX_TRANSIENT_RETRIES
