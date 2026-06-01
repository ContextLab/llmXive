"""Unit tests for the Dartmouth circuit breaker (sustained-outage fast-abort).

The per-instance breaker is the SECOND line of defense after the generous
per-call retry/backoff. The retries ride out short flaps (minutes); the breaker
trips on a SUSTAINED outage so the pipeline aborts FAST instead of thrashing for
hours (observed: review/reviser calls retried 9x on a dead endpoint, ~27 min/call,
7h zero-progress).

These drive the REAL breaker state machine via a deterministic injected callable
and an injectable clock — no external model is contacted (the injected callable
IS the code under test, not a mock of the Dartmouth API).
"""

from __future__ import annotations

import pytest

from llmxive.backends.base import (
    BackendUnavailable,
    ChatMessage,
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.dartmouth import _CircuitBreaker


def test_backend_unavailable_is_permanent():
    """BackendUnavailable must subclass PermanentBackendError so the run loop's
    existing permanent-error handling aborts cleanly (no retry/fallback burn)."""
    assert issubclass(BackendUnavailable, PermanentBackendError)


def test_noop_in_normal_operation():
    """A single transient failure followed by a success must NOT trip."""
    clock = _FakeClock()
    br = _CircuitBreaker(max_consecutive=3, window_s=1800.0, clock=clock)
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            raise TransientBackendError("one flap")
        return "ok"

    with pytest.raises(TransientBackendError):
        br.call(flaky)
    # not open after a single failure
    assert br.call(flaky) == "ok"
    # success fully reset state
    assert br.call(lambda: "still ok") == "still ok"


def test_trips_after_k_consecutive_failures():
    clock = _FakeClock()
    br = _CircuitBreaker(max_consecutive=3, window_s=1800.0, clock=clock)

    def always_fail():
        raise TransientBackendError("down")

    # 3 consecutive full failures pass through the inner call...
    for _ in range(3):
        with pytest.raises(TransientBackendError):
            br.call(always_fail)
    # ...the 4th call short-circuits OPEN without invoking the inner call.
    inner_called = {"n": 0}

    def tripwire():
        inner_called["n"] += 1
        raise TransientBackendError("should not be reached")

    with pytest.raises(BackendUnavailable) as ei:
        br.call(tripwire)
    assert inner_called["n"] == 0  # OPEN → inner NOT invoked
    assert "circuit open" in str(ei.value).lower()
    assert "3 consecutive" in str(ei.value)


def test_open_fails_fast_without_burning_inner_call():
    clock = _FakeClock()
    br = _CircuitBreaker(max_consecutive=2, window_s=1800.0, clock=clock)

    def fail():
        raise TransientBackendError("down")

    for _ in range(2):
        with pytest.raises(TransientBackendError):
            br.call(fail)
    # Now OPEN: repeated calls keep failing fast, inner never runs.
    for _ in range(5):
        with pytest.raises(BackendUnavailable):
            br.call(lambda: (_ for _ in ()).throw(AssertionError("inner ran")))


def test_resets_on_success_below_threshold():
    """Failures that don't reach K, interrupted by a success, reset the count."""
    clock = _FakeClock()
    br = _CircuitBreaker(max_consecutive=3, window_s=1800.0, clock=clock)

    def fail():
        raise TransientBackendError("down")

    # 2 fails (below K=3), then a success resets.
    for _ in range(2):
        with pytest.raises(TransientBackendError):
            br.call(fail)
    assert br.call(lambda: "ok") == "ok"
    # 2 more fails — still below threshold because the counter reset.
    for _ in range(2):
        with pytest.raises(TransientBackendError):
            br.call(fail)
    # Not open yet (only 2 consecutive since reset).
    assert br.call(lambda: "ok2") == "ok2"


def test_trips_on_wall_clock_window_even_below_k():
    """If the failure WINDOW elapses with no success, trip even if fewer than K
    consecutive (slow-drip outage). Uses the injectable clock."""
    clock = _FakeClock()
    br = _CircuitBreaker(max_consecutive=100, window_s=1800.0, clock=clock)

    def fail():
        raise TransientBackendError("down")

    # First failure marks the window start.
    with pytest.raises(TransientBackendError):
        br.call(fail)
    # Advance past the 30-min window with no intervening success.
    clock.advance(1801.0)
    # The very next call is already OPEN (window elapsed) — fails fast WITHOUT
    # invoking the inner callable.
    with pytest.raises(BackendUnavailable) as ei:
        br.call(lambda: (_ for _ in ()).throw(AssertionError("inner ran")))
    assert "min" in str(ei.value).lower()


def test_window_does_not_trip_if_success_resets_it():
    clock = _FakeClock()
    br = _CircuitBreaker(max_consecutive=100, window_s=1800.0, clock=clock)

    def fail():
        raise TransientBackendError("down")

    with pytest.raises(TransientBackendError):
        br.call(fail)
    clock.advance(1000.0)
    assert br.call(lambda: "ok") == "ok"  # success clears the window start
    clock.advance(1000.0)  # 2000s since FIRST failure, but window reset at 1000
    with pytest.raises(TransientBackendError):
        br.call(fail)
    # Only ~0s into the new window → not open.
    assert br.call(lambda: "ok2") == "ok2"


def test_permanent_error_does_not_count_as_breaker_failure():
    """Only fully-failed (TransientBackendError after retries) calls count.
    A PermanentBackendError (e.g. paid-model guard) is not an outage signal —
    it must pass through WITHOUT advancing the breaker toward OPEN."""
    clock = _FakeClock()
    br = _CircuitBreaker(max_consecutive=2, window_s=1800.0, clock=clock)

    def permanent():
        raise PermanentBackendError("not a free model")

    for _ in range(5):
        with pytest.raises(PermanentBackendError):
            br.call(permanent)
    # Breaker never tripped — a real transient would still pass through.
    with pytest.raises(TransientBackendError):
        br.call(lambda: (_ for _ in ()).throw(TransientBackendError("flap")))


def test_chat_integrates_breaker_and_fails_fast(monkeypatch):
    """End-to-end through DartmouthBackend.chat: once the endpoint has fully
    failed K times, the next chat() raises BackendUnavailable WITHOUT invoking
    the client (no retry-budget burn). Uses a deterministic failing fake client —
    no external model is contacted; max_retries=0 keeps each call to one attempt."""
    from llmxive.backends import dartmouth as dm

    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "sk-test-fake")
    # Treat the test model as free so the paid-model guard doesn't short-circuit.
    monkeypatch.setattr(dm, "is_free_model", lambda model: True)

    invoked = {"n": 0}

    class _FailingClient:
        def invoke(self, *_a, **_k):
            invoked["n"] += 1
            raise RuntimeError("503 service unavailable")  # classified transient

    backend = dm.DartmouthBackend(max_retries=0)
    monkeypatch.setattr(backend, "_client", lambda model: _FailingClient())
    # Trip after 3 consecutive full failures.
    monkeypatch.setattr(backend, "_breaker", _CircuitBreaker(max_consecutive=3, window_s=1e9))

    msgs = [ChatMessage(role="user", content="hi")]

    # 3 fully-failed calls pass through to the client (each raises transient).
    for _ in range(3):
        with pytest.raises(TransientBackendError):
            backend.chat(msgs, model="qwen.qwen3.5-122b")
    calls_after_three = invoked["n"]
    assert calls_after_three == 3  # one client.invoke per call (max_retries=0)

    # 4th call short-circuits OPEN — client NOT invoked again.
    with pytest.raises(BackendUnavailable):
        backend.chat(msgs, model="qwen.qwen3.5-122b")
    assert invoked["n"] == calls_after_three  # no further client call


class _FakeClock:
    """Deterministic monotonic clock for breaker window tests."""

    def __init__(self) -> None:
        self._t = 1000.0

    def __call__(self) -> float:
        return self._t

    def advance(self, dt: float) -> None:
        self._t += dt
