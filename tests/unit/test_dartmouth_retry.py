"""Unit tests for the centralized Dartmouth retry-with-backoff.

The retry helper makes every DartmouthBackend.chat() call automatically
resilient to brief flickers (5xx, connection-reset, model temporarily
unloaded, the Dartmouth maintenance HTML redirect). Tests cover both
the standalone ``_retry_with_backoff`` helper AND its integration with
the chat() classification path.
"""

from __future__ import annotations

import pytest

from llmxive.backends.base import (
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.dartmouth import _is_transient_error_text, _retry_with_backoff


def test_retry_returns_value_on_first_success():
    calls = []

    def fn():
        calls.append(1)
        return "ok"

    assert _retry_with_backoff(
        fn, max_retries=3, base_delay_s=0.001,
    ) == "ok"
    assert len(calls) == 1


def test_retry_absorbs_brief_flicker(monkeypatch):
    """Two transients then a success → returns the success after exactly
    3 attempts. Delay slept twice (after attempts 0 and 1)."""
    calls = []
    sleeps: list[float] = []
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.time.sleep", lambda s: sleeps.append(s),
    )

    def fn():
        calls.append(1)
        if len(calls) < 3:
            raise TransientBackendError(f"flicker {len(calls)}")
        return "recovered"

    result = _retry_with_backoff(
        fn, max_retries=3, base_delay_s=0.1, description="test",
    )
    assert result == "recovered"
    assert len(calls) == 3
    # Backoff: base * 2^0, base * 2^1 = 0.1, 0.2
    assert sleeps == pytest.approx([0.1, 0.2])


def test_retry_surfaces_final_transient_after_exhausting_attempts(monkeypatch):
    """When every attempt fails transiently, the LAST exception
    propagates as a TransientBackendError so callers see the real
    underlying error (and their own router-level retry/fallback can
    still trigger)."""
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.time.sleep", lambda s: None,
    )
    attempts = []

    def fn():
        attempts.append(1)
        raise TransientBackendError(f"attempt {len(attempts)}")

    with pytest.raises(TransientBackendError, match="attempt 4"):
        _retry_with_backoff(
            fn, max_retries=3, base_delay_s=0.001,
        )
    # 1 initial + 3 retries = 4 attempts.
    assert len(attempts) == 4


def test_retry_does_not_retry_permanent_errors(monkeypatch):
    """Permanent errors propagate immediately — no retry, no sleep."""
    sleeps = []
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.time.sleep", lambda s: sleeps.append(s),
    )
    attempts = []

    def fn():
        attempts.append(1)
        raise PermanentBackendError("you may not pass")

    with pytest.raises(PermanentBackendError, match="may not pass"):
        _retry_with_backoff(
            fn, max_retries=5, base_delay_s=1.0,
        )
    assert len(attempts) == 1  # no retry
    assert sleeps == []  # no sleep


def test_retry_does_not_retry_unrelated_exceptions(monkeypatch):
    """Non-BackendError exceptions propagate immediately (they're
    programming bugs, not retryable conditions)."""
    sleeps = []
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.time.sleep", lambda s: sleeps.append(s),
    )

    def fn():
        raise ValueError("totally unrelated bug")

    with pytest.raises(ValueError, match="totally unrelated"):
        _retry_with_backoff(
            fn, max_retries=5, base_delay_s=1.0,
        )
    assert sleeps == []


def test_retry_with_zero_max_retries_makes_no_retries(monkeypatch):
    """max_retries=0 → one attempt; if it fails transient, surface
    immediately. Configurable shut-off for tests / impatient callers."""
    sleeps = []
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.time.sleep", lambda s: sleeps.append(s),
    )
    attempts = []

    def fn():
        attempts.append(1)
        raise TransientBackendError("one and done")

    with pytest.raises(TransientBackendError):
        _retry_with_backoff(
            fn, max_retries=0, base_delay_s=1.0,
        )
    assert len(attempts) == 1
    assert sleeps == []


def test_retry_backoff_multiplier_is_exponential(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.time.sleep", lambda s: sleeps.append(s),
    )

    def fn():
        raise TransientBackendError("always fails")

    with pytest.raises(TransientBackendError):
        _retry_with_backoff(
            fn, max_retries=4, base_delay_s=1.0,
        )
    # Sleeps after attempts 0, 1, 2, 3 (the 5th attempt is the final
    # one — no sleep after it). Backoff: 1, 2, 4, 8.
    assert sleeps == pytest.approx([1.0, 2.0, 4.0, 8.0])


def test_connection_dropped_midstream_is_transient():
    """Regression (Part-7): a connection broken mid-read while streaming a
    large planner/reviewer reply (requests ChunkedEncodingError wrapping
    http.client IncompleteRead) MUST be classified transient so it retries —
    before the fix it surfaced raw and crashed the plan stage at `clarified`."""
    # The exact run #12 failure text:
    assert _is_transient_error_text(
        "('Connection broken: IncompleteRead(77671 bytes read)', "
        "IncompleteRead(77671 bytes read))"
    )
    for txt in (
        "ChunkedEncodingError: Connection broken: IncompleteRead",
        "('Connection aborted.', RemoteDisconnected('Remote end closed "
        "connection without response'))",
        "EOF occurred in violation of protocol",
        "BrokenPipeError: [Errno 32] Broken pipe",
    ):
        assert _is_transient_error_text(txt), txt


def test_permanent_errors_stay_permanent():
    """The classifier must NOT over-match: genuine permanent failures (auth,
    a malformed model reply) are not retried."""
    for txt in (
        "invalid api key",
        "authentication failed: 401 unauthorized",
        "the model produced a malformed schema",
        "valueerror: bad request body",
    ):
        assert not _is_transient_error_text(txt), txt
