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
    DeadlineExceededError,
    ModelDownError,
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.dartmouth import (
    _is_model_down_text,
    _is_transient_error_text,
    _retry_with_backoff,
)


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
    # Pin equal jitter to its UPPER bound so the slept delay == the computed
    # backoff (delay = half + uniform(0, half); uniform→half ⇒ delay=computed).
    # This asserts the exact backoff SCHEDULE while jitter is in play.
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.random.uniform", lambda _a, b: b,
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
    # Backoff: base * 2^0, base * 2^1 = 0.1, 0.2 (jitter pinned to upper bound)
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


def test_302_outage_classified_as_model_down_not_generic_transient():
    """A 302→outage.dartmouth.edu maintenance redirect is a model-DOWN signal
    (distinct from a generic retryable transient). It is still a transient by
    type so the router falls back, but it must match _is_model_down_text so the
    retry layers fast-fail to a peer instead of burning the retry budget."""
    for txt in (
        "<title>302 Moved Temporarily</title> the document has moved to "
        "http://outage.dartmouth.edu",
        "302 moved",
        "moved temporarily",
    ):
        assert _is_model_down_text(txt), txt
        assert _is_transient_error_text(txt), txt  # still transient (router falls back)
    # A generic transient is NOT a model-down signal — it keeps its retries.
    for txt in ("503 service unavailable", "connection reset by peer", "429 rate"):
        assert not _is_model_down_text(txt), txt


def test_retry_does_not_retry_model_down(monkeypatch):
    """A ModelDownError (302→outage, or a deadline hang — its subclass) is NOT
    inner-retried; it propagates after ONE attempt so the model-fallback chain
    escapes to a healthy peer. (DeadlineExceededError IS a ModelDownError, so the
    deadline-hang test below is the subclass case.)"""
    sleeps: list[float] = []
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.time.sleep", lambda s: sleeps.append(s),
    )
    attempts = []

    def fn():
        attempts.append(1)
        raise ModelDownError("302 Moved Temporarily → outage.dartmouth.edu")

    with pytest.raises(ModelDownError):
        _retry_with_backoff(fn, max_retries=8, base_delay_s=1.0)
    assert len(attempts) == 1  # no inner retry on a model-down signal
    assert sleeps == []


def test_retry_does_not_retry_deadline_hang(monkeypatch):
    """A DeadlineExceededError (the model hung past its FULL deadline) is NOT
    inner-retried — retrying the same hung model costs another full deadline and
    almost never succeeds. It propagates after ONE attempt so the model-fallback
    chain can escape to a healthy peer. Fast-flap transients keep their generous
    retries (see test_retry_absorbs_brief_flicker / the 5-min outage test)."""
    sleeps: list[float] = []
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.time.sleep", lambda s: sleeps.append(s),
    )
    attempts = []

    def fn():
        attempts.append(1)
        raise DeadlineExceededError(
            "qwen hung past 360s deadline (no response received)"
        )

    with pytest.raises(DeadlineExceededError):
        _retry_with_backoff(fn, max_retries=8, base_delay_s=1.0)
    assert len(attempts) == 1  # NO inner retry on a deadline hang
    assert sleeps == []        # and no backoff sleep


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
    # Pin jitter to its upper bound → slept delay == computed backoff.
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.random.uniform", lambda _a, b: b,
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


def test_backoff_delay_is_capped_to_ride_out_multi_minute_outage(monkeypatch):
    """The per-attempt delay is capped (default 60s) so exponential backoff
    plateaus instead of exploding — the client keeps re-probing ~once a minute
    across a multi-minute Dartmouth outage (302->outage / hang) rather than
    sleeping for huge single intervals. Regression for extending the window from
    35s to ~5 min."""

    sleeps: list[float] = []
    monkeypatch.setattr("llmxive.backends.dartmouth.time.sleep", lambda s: sleeps.append(s))
    # Pin jitter to its upper bound → slept delay == computed (capped) backoff,
    # so the cap/plateau contract is asserted exactly with jitter in play.
    monkeypatch.setattr("llmxive.backends.dartmouth.random.uniform", lambda _a, b: b)

    def fn():
        raise TransientBackendError("302 moved (outage.dartmouth.edu)")

    # base=10, x2 each attempt: 10,20,40,80,160,320,640,1280 -> capped at 60.
    with pytest.raises(TransientBackendError):
        _retry_with_backoff(fn, max_retries=8, base_delay_s=10.0)
    assert sleeps == pytest.approx([10.0, 20.0, 40.0, 60.0, 60.0, 60.0, 60.0, 60.0])
    # rode out > 5 minutes before giving up
    assert sum(sleeps) >= 300.0


def test_backoff_delay_has_equal_jitter(monkeypatch):
    """Each slept delay must be EQUAL-JITTERED around the computed backoff:
    ``delay = half + uniform(0, half)`` where ``half = computed/2``. So the slept
    value always falls in ``[computed/2, computed]``. This de-synchronizes the
    many parallel lens-call retries so they don't reconverge into waves that
    hammer a recovering pod. We assert the CONTRACT/range deterministically by
    patching ``random.uniform`` to its endpoints — not a single fixed value."""
    base, mult, cap = 10.0, 2.0, 60.0
    computed = [min(base * (mult ** a), cap) for a in range(4)]  # 10,20,40,60

    # uniform(0, half) at its LOWER bound (0) → delay == half == computed/2.
    sleeps_low: list[float] = []
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.time.sleep", lambda s: sleeps_low.append(s)
    )
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.random.uniform", lambda _a, _b: 0.0
    )

    def fail():
        raise TransientBackendError("503 service unavailable")

    with pytest.raises(TransientBackendError):
        _retry_with_backoff(fail, max_retries=4, base_delay_s=base)
    assert sleeps_low == pytest.approx([c / 2 for c in computed])

    # uniform(0, half) at its UPPER bound (half) → delay == computed.
    sleeps_high: list[float] = []
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.time.sleep", lambda s: sleeps_high.append(s)
    )
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.random.uniform", lambda _a, b: b
    )
    with pytest.raises(TransientBackendError):
        _retry_with_backoff(fail, max_retries=4, base_delay_s=base)
    assert sleeps_high == pytest.approx(computed)

    # And for an arbitrary real draw, every slept delay is in [computed/2, computed].
    sleeps_mid: list[float] = []
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.time.sleep", lambda s: sleeps_mid.append(s)
    )
    monkeypatch.setattr(
        "llmxive.backends.dartmouth.random.uniform", lambda _a, b: b * 0.37
    )
    with pytest.raises(TransientBackendError):
        _retry_with_backoff(fail, max_retries=4, base_delay_s=base)
    for slept, comp in zip(sleeps_mid, computed, strict=True):
        assert comp / 2 <= slept <= comp


def test_default_retry_window_spans_several_minutes():
    """The shipped defaults must give up only after several minutes, not 35s."""
    from llmxive.backends import dartmouth

    assert dartmouth._DEFAULT_MAX_RETRIES >= 6
    # cumulative wait at defaults (capped) must exceed ~4 minutes
    base, mult, cap = (
        dartmouth._DEFAULT_RETRY_BASE_S,
        dartmouth._RETRY_MULTIPLIER,
        dartmouth._DEFAULT_RETRY_MAX_DELAY_S,
    )
    total = sum(min(base * (mult ** a), cap) for a in range(dartmouth._DEFAULT_MAX_RETRIES))
    assert total >= 240.0, f"default retry window only {total}s — too short to ride a few-min outage"


def test_empty_reply_caps_retries_low():
    """An EmptyReplyError (qwen <think>-mode flap) retries only a few times before
    falling through — NOT the full 8-retry budget — so the router reaches a healthy
    peer / the fast paid fallback quickly instead of stalling ~5 min on a flapper."""
    from llmxive.backends.base import EmptyReplyError
    from llmxive.backends.dartmouth import _EMPTY_REPLY_MAX_RETRIES

    calls = []

    def fn():
        calls.append(1)
        raise EmptyReplyError("empty")

    with pytest.raises(EmptyReplyError):
        _retry_with_backoff(fn, max_retries=8, base_delay_s=0.001)
    assert len(calls) == _EMPTY_REPLY_MAX_RETRIES + 1
    assert len(calls) < 9  # NOT the full budget


def test_generic_transient_keeps_full_retry_budget():
    """A generic transient (5xx/reset — a true network blip) still gets the full
    retry budget; only the empty-reply flap is capped low."""
    calls = []

    def fn():
        calls.append(1)
        raise TransientBackendError("5xx")

    with pytest.raises(TransientBackendError):
        _retry_with_backoff(fn, max_retries=4, base_delay_s=0.001)
    assert len(calls) == 5  # max_retries + 1


def test_client_closed_request_is_transient():
    """Regression (engine-failure #505): Dartmouth's gateway returns HTTP 499
    'Client Closed Request' when an upstream proxy drops the connection before
    the model responds — a textbook transient. Before the fix it fell through to
    PermanentBackendError, crashing the plan stage and filing a spurious
    engine-failure issue instead of riding out the flap."""
    for txt in (
        "Client Closed Request",
        "PermanentBackendError: Client Closed Request",
        "499 client closed request",
    ):
        assert _is_transient_error_text(txt), txt


def test_auth_error_text_matches_gateway_reject_strings():
    """The auth-error matcher recognizes the gateway's key-rejection strings
    (both word orders) without over-matching unrelated errors."""
    from llmxive.backends.dartmouth import _is_auth_error_text

    for txt in (
        "api key invalid!",          # Dartmouth gateway's exact string (#515-518)
        "'API key invalid!'",
        "invalid api key",
        "authentication failed: 401 unauthorized",
        "AuthenticationError: 401",
    ):
        assert _is_auth_error_text(txt.lower()), txt
    for txt in (
        "503 service unavailable",
        "connection reset by peer",
        "the model produced a malformed schema",
    ):
        assert not _is_auth_error_text(txt.lower()), txt


def test_auth_flap_with_valid_key_is_transient(monkeypatch):
    """Regression (engine-failure #515-518): the Dartmouth gateway transiently
    rejected a VALID key ('API key invalid!') during a ~2h auth-service flap on
    2026-07-06. When the catalog endpoint (same key + host) still ACCEPTS the key
    — i.e. we cannot confirm the key is genuinely bad — the mid-run rejection is a
    flap and must be TRANSIENT so the router aborts cleanly (BackendUnavailable)
    and the project retries next tick, NOT a PermanentBackendError that files a
    spurious engine-failure issue."""
    from llmxive.backends import dartmouth

    # Catalog accepts the key → NOT a genuine bad key → flap.
    monkeypatch.setattr(dartmouth, "_gateway_rejects_key", lambda **_: False)
    with pytest.raises(TransientBackendError):
        dartmouth._raise_for_backend_error("'api key invalid!'", RuntimeError("x"))


def test_genuine_bad_key_stays_permanent(monkeypatch):
    """A GENUINELY bad/expired key is rejected by the catalog endpoint too
    (401/403). That is a real config error — it must stay PermanentBackendError so
    the run surfaces a loud, actionable engine-failure issue (Fail Fast), never a
    silent retry-forever."""
    from llmxive.backends import dartmouth

    monkeypatch.setattr(dartmouth, "_gateway_rejects_key", lambda **_: True)
    with pytest.raises(PermanentBackendError):
        dartmouth._raise_for_backend_error("'api key invalid!'", RuntimeError("x"))


def test_raise_for_backend_error_preserves_model_down_and_transient(monkeypatch):
    """The centralized classifier keeps the existing precedence: a model-down
    redirect → ModelDownError; a generic transient → TransientBackendError; an
    unclassified non-auth error → PermanentBackendError (auth preflight is only
    consulted for auth-shaped errors)."""
    from llmxive.backends import dartmouth

    # Auth preflight must NOT be consulted for non-auth errors.
    def _boom(**_):  # pragma: no cover - must never run
        raise AssertionError("_gateway_rejects_key consulted for a non-auth error")

    monkeypatch.setattr(dartmouth, "_gateway_rejects_key", _boom)

    with pytest.raises(ModelDownError):
        dartmouth._raise_for_backend_error(
            "302 moved temporarily → outage.dartmouth.edu", RuntimeError("x")
        )
    with pytest.raises(TransientBackendError):
        dartmouth._raise_for_backend_error("503 service unavailable", RuntimeError("x"))
    with pytest.raises(PermanentBackendError):
        dartmouth._raise_for_backend_error(
            "the model produced a malformed schema", RuntimeError("x")
        )
