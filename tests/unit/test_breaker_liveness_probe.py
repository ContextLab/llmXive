"""A recovery probe must not cost a full request budget.

The breaker opens immediately on a ``ModelDownError`` — correct, the request
budget is already spent — but it then allowed ONE real request through per
cooldown window as a recovery probe. For a model whose circuit was opened BY a
deadline hang, that probe re-hangs for the model's whole deadline (360s for a
reasoning model). Measured on the frozen 2026-10-09 totient canary: 7 deadline
hangs burned 2160s of an 8171s run (26%), roughly four of them probes.

These drive the REAL breaker state machine with an injected clock and an
injected liveness callable; the liveness callable IS the decision under test,
not a stand-in for the Dartmouth API. ``test_liveness_probe_real.py`` in
``tests/real_call`` exercises the genuine probe against a live free model.
"""

from __future__ import annotations

import pytest

from llmxive.backends.base import BackendUnavailable, ModelDownError, TransientBackendError
from llmxive.backends.dartmouth import _CircuitBreaker


class _FakeClock:
    def __init__(self) -> None:
        self._t = 1000.0

    def __call__(self) -> float:
        return self._t

    def advance(self, dt: float) -> None:
        self._t += dt


def _opened(clock, liveness, cooldown_s=900.0):
    """A breaker whose circuit a deadline hang has just opened."""
    br = _CircuitBreaker(max_consecutive=3, window_s=1e9, clock=clock,
                         cooldown_s=cooldown_s, liveness=liveness)
    br.name = "zai-org.glm-5.3"
    with pytest.raises(ModelDownError):
        br.call(lambda: (_ for _ in ()).throw(ModelDownError("hung past its deadline")))
    return br


def test_a_sick_model_is_not_probed_with_the_real_request():
    clock = _FakeClock()
    probes: list[str] = []
    br = _opened(clock, lambda name: probes.append(name) or False)

    clock.advance(901.0)
    with pytest.raises(BackendUnavailable):
        br.call(lambda: (_ for _ in ()).throw(AssertionError("the real request ran")))
    assert probes == ["zai-org.glm-5.3"], "the probe must be asked, with the model name"


def test_a_failed_probe_restarts_the_cooldown():
    clock = _FakeClock()
    probes: list[str] = []
    br = _opened(clock, lambda name: probes.append(name) or False)

    clock.advance(901.0)
    with pytest.raises(BackendUnavailable):
        br.call(lambda: "unreachable")
    # Immediately afterwards the circuit is shut again: no second probe, and
    # still no real request.
    with pytest.raises(BackendUnavailable):
        br.call(lambda: (_ for _ in ()).throw(AssertionError("the real request ran")))
    assert len(probes) == 1
    # ... until the next full cooldown elapses.
    clock.advance(901.0)
    with pytest.raises(BackendUnavailable):
        br.call(lambda: "unreachable")
    assert len(probes) == 2


def test_a_live_model_closes_the_circuit_and_the_real_request_runs():
    clock = _FakeClock()
    br = _opened(clock, lambda _name: True)

    clock.advance(901.0)
    assert br.call(lambda: "real answer") == "real answer"
    # The circuit is fully closed, so the next call needs no probe at all.
    assert br.call(lambda: "again") == "again"


def test_a_closed_circuit_is_not_reopened_by_one_transient_failure():
    """After a successful probe the call is ORDINARY, not a probe.

    A probe that fails reopens the circuit at once. A real call made after the
    model proved it answers must instead get the normal allowance, or one flap
    straight after recovery would slam the circuit shut for another cooldown.
    """
    clock = _FakeClock()
    br = _opened(clock, lambda _name: True)

    clock.advance(901.0)
    with pytest.raises(TransientBackendError):
        br.call(lambda: (_ for _ in ()).throw(TransientBackendError("one flap")))
    assert br.call(lambda: "ok") == "ok", "a single flap must not reopen the circuit"


def test_an_unaskable_model_falls_back_to_the_real_request_probe():
    """``None`` (a paid model) keeps the original behavior exactly."""
    clock = _FakeClock()
    br = _opened(clock, lambda _name: None)

    clock.advance(901.0)
    assert br.call(lambda: "probed with the real request") == "probed with the real request"


def test_a_raising_probe_counts_as_not_answering():
    clock = _FakeClock()

    def _explode(_name):
        raise RuntimeError("probe transport blew up")

    br = _opened(clock, _explode)
    clock.advance(901.0)
    with pytest.raises(BackendUnavailable):
        br.call(lambda: (_ for _ in ()).throw(AssertionError("the real request ran")))


def test_a_breaker_without_a_liveness_check_behaves_as_before():
    clock = _FakeClock()
    br = _CircuitBreaker(max_consecutive=3, window_s=1e9, clock=clock, cooldown_s=900.0)
    with pytest.raises(ModelDownError):
        br.call(lambda: (_ for _ in ()).throw(ModelDownError("hung")))
    with pytest.raises(BackendUnavailable):
        br.call(lambda: "blocked")
    clock.advance(901.0)
    assert br.call(lambda: "probed with the real request") == "probed with the real request"


# --- the backend's own liveness check ------------------------------------

class _Reply:
    def __init__(self, content: str) -> None:
        self.content = content


class _Client:
    """Stands in for the transport, the way the existing breaker tests do."""

    def __init__(self, reply=None, error=None) -> None:
        self._reply, self._error = reply, error
        self.invocations: list[dict] = []

    def invoke(self, messages, **kwargs):
        self.invocations.append({"messages": messages, **kwargs})
        if self._error is not None:
            raise self._error
        return self._reply


def _backend(monkeypatch, client):
    from llmxive.backends import dartmouth as dm

    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "liveness-test-credential")
    backend = dm.DartmouthBackend(max_retries=0)
    monkeypatch.setattr(backend, "_client", lambda model: client)
    return backend


def test_a_paid_model_is_never_pinged(monkeypatch):
    from llmxive.backends import dartmouth as dm

    client = _Client(reply=_Reply("OK"))
    backend = _backend(monkeypatch, client)
    monkeypatch.setattr(dm, "is_free_model", lambda _model: False)
    assert backend._liveness_ok("anthropic.claude-opus-5") is None
    assert client.invocations == [], "a paid model must not be spent on a ping"


def test_a_free_model_that_answers_is_live(monkeypatch):
    from llmxive.backends import dartmouth as dm

    client = _Client(reply=_Reply("OK"))
    backend = _backend(monkeypatch, client)
    monkeypatch.setattr(dm, "is_free_model", lambda _model: True)
    assert backend._liveness_ok("openai.gpt-oss-120b") is True
    assert len(client.invocations) == 1
    sent = client.invocations[0]
    assert sent["max_tokens"] == dm._LIVENESS_MAX_TOKENS
    # Bounded, but NOT minimal: a reasoning model given too few tokens answers
    # with empty content (verified live — gpt-oss-120b and gemma-4 both do at
    # 16), and an empty answer would read as "down" and strand a healthy model.
    assert 128 <= dm._LIVENESS_MAX_TOKENS <= 2048


def test_a_free_model_that_errors_is_not_live(monkeypatch):
    from llmxive.backends import dartmouth as dm

    backend = _backend(monkeypatch, _Client(error=RuntimeError("503 service unavailable")))
    monkeypatch.setattr(dm, "is_free_model", lambda _model: True)
    assert backend._liveness_ok("openai.gpt-oss-120b") is False


def test_an_empty_reply_is_not_live(monkeypatch):
    """The qwen ``<think>``-mode flap answers with nothing; that is not alive."""
    from llmxive.backends import dartmouth as dm

    backend = _backend(monkeypatch, _Client(reply=_Reply("")))
    monkeypatch.setattr(dm, "is_free_model", lambda _model: True)
    assert backend._liveness_ok("qwen.qwen3.5-122b") is False


def test_the_probe_deadline_is_far_below_a_request_deadline():
    from llmxive.backends import dartmouth as dm

    assert dm._LIVENESS_DEADLINE_S < dm._DEFAULT_DEADLINE_S
    assert dm._LIVENESS_DEADLINE_S * 4 < dm._DEFAULT_REASONING_DEADLINE_S


def test_each_model_breaker_knows_its_model_and_carries_the_check(monkeypatch):
    backend = _backend(monkeypatch, _Client(reply=_Reply("OK")))
    first = backend._breaker_for("openai.gpt-oss-120b")
    second = backend._breaker_for("zai-org.glm-5.3")
    assert first is not second, "breakers stay per-model"
    assert first.name == "openai.gpt-oss-120b"
    assert second.name == "zai-org.glm-5.3"
    assert first.liveness is not None and second.liveness is not None
    assert backend._breaker_for("openai.gpt-oss-120b") is first
