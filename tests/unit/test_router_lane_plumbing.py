"""The router forwards spec-025's five lane params (slice 1B, Task 3).

Two layers, deliberately. The forwarding tests wrap the REAL ``route_chat`` and let it run,
so they prove the params both arrive AND leave the real path working. The classification
tests pin the wrapper's own contract, which is what this task actually changed.
"""

from __future__ import annotations

import pytest

from llmxive.backends.base import BackendUnavailable, ChatMessage, ChatResponse
from llmxive.backends.router import chat_with_model_fallback
from llmxive.model_selection.execute import ChainExhausted
from llmxive.model_selection.types import IndependenceBaseline, ModelUnavailable

_MSGS = [ChatMessage(role="user", content="review this")]
#: Every family in the offline snapshot's free Dartmouth chain.
_ALL_FAMILIES = frozenset({"glm-5.3", "qwen3.5", "gemma-4", "gpt-oss"})


class _Fake:
    name = "dartmouth"

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
        return ChatResponse(text=f"OK {model}", model=model, backend="dartmouth")


class _Sink:
    """A real RouteAudit: records every event and always grants the dispatch claim."""

    def __init__(self):
        self.events = []

    def record(self, event) -> None:
        self.events.append(event)

    def claim_dispatch(self, event) -> bool:
        self.events.append(event)
        return True


class _Budget:
    """A real ReservationAuthority that counts whether it was ever consulted."""

    def __init__(self):
        self.reserves = []

    def reserve(self, credits, *, reservation_id, call_id) -> bool:
        self.reserves.append((credits, reservation_id, call_id))
        return True

    def release(self, reservation_id) -> None:
        pass

    def mark_retained(self, reservation_id) -> None:
        pass


def _spy_on_route_chat(monkeypatch, calls):
    """Record route_chat's kwargs and then RUN IT — a spy over the real function, not a
    replacement, so these tests also prove the real path still works with the new params."""
    import llmxive.model_selection.route as route_mod

    real = route_mod.route_chat

    def _spy(messages, **kw):
        calls.append(kw)
        return real(messages, **kw)

    monkeypatch.setattr(route_mod, "route_chat", _spy)


def _raise_from_route_chat(monkeypatch, exc):
    import llmxive.model_selection.route as route_mod

    def _boom(messages, **kw):
        raise exc

    monkeypatch.setattr(route_mod, "route_chat", _boom)


# ---- forwarding ----


def test_defaults_are_behavior_preserving(monkeypatch):
    # The five params arrive as route_chat's OWN defaults, so an unmigrated caller routes
    # exactly as before.
    calls = []
    _spy_on_route_chat(monkeypatch, calls)
    response = chat_with_model_fallback(_Fake(), _MSGS, model=None, max_tokens=64,
                                        profile="deep_review")
    assert response.text.startswith("OK")
    assert calls[0]["independence_against"] is None
    assert calls[0]["route_audit"] is None
    assert calls[0]["reservation_authority"] is None
    assert calls[0]["route_id"] is None


def test_all_five_params_are_forwarded(monkeypatch):
    calls = []
    _spy_on_route_chat(monkeypatch, calls)
    base = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    sink, budget = _Sink(), _Budget()
    chat_with_model_fallback(
        _Fake(), _MSGS, model=None, max_tokens=64, profile="independent_review",
        independence_against=base, route_audit=sink, reservation_authority=budget,
        route_id="RID",
    )
    assert calls[0]["independence_against"] is base
    assert calls[0]["route_audit"] is sink
    assert calls[0]["reservation_authority"] is budget
    assert calls[0]["route_id"] == "RID"
    assert calls[0]["profile"] == "independent_review"


def test_the_forwarded_hooks_actually_reach_execute():
    # Forwarding that stops short of `execute` would satisfy the kwargs assertions above
    # and still leave every lane call unaudited. No spy here — the real path runs.
    sink, budget = _Sink(), _Budget()
    chat_with_model_fallback(
        _Fake(), _MSGS, model=None, max_tokens=64, profile="independent_review",
        route_audit=sink, reservation_authority=budget, route_id="RID-e2e",
    )
    kinds = {type(e).__name__ for e in sink.events}
    assert {"ChainResolved", "DispatchStarted", "DispatchCompleted"} <= kinds
    assert {e.route_id for e in sink.events} == {"RID-e2e"}, "the durable route id was not used"
    # and the authority is NOT consulted for a free candidate — execute gates the whole
    # reservation path on `if not candidate.pricing.is_free`, which is what makes the
    # strictly-positive reserve() contract safe.
    assert budget.reserves == []


def test_independence_against_actually_constrains_selection():
    # Effect, not just arrival: excluding EVERY family in the snapshot must leave nothing
    # eligible, and that is a real ModelUnavailable from real selection logic.
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(
            _Fake(), _MSGS, model=None, max_tokens=64, profile="independent_review",
            independence_against=IndependenceBaseline(families=_ALL_FAMILIES),
        )


# ---- exception classification ----


def test_model_unavailable_reraises_raw_only_when_asked():
    # Real ModelUnavailable, produced by real selection finding nothing eligible.
    kwargs = dict(model=None, max_tokens=64, profile="independent_review",
                  independence_against=IndependenceBaseline(families=_ALL_FAMILIES))
    # default: the existing outage-classification contract is preserved
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(_Fake(), _MSGS, **kwargs)
    # FR-002's reroute needs the RAW exception to decide whether to try its relaxed leg
    with pytest.raises(ModelUnavailable):
        chat_with_model_fallback(_Fake(), _MSGS, reraise_model_unavailable=True, **kwargs)


def test_chain_exhausted_always_converts_even_when_reraise_is_set(monkeypatch):
    # ChainExhausted is an outage: the chain RAN and every candidate failed. It must never
    # become a reroute trigger, or the fallback leg burns on the same broken backends.
    _raise_from_route_chat(monkeypatch, ChainExhausted("every candidate advanced"))
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(_Fake(), _MSGS, model=None, max_tokens=64,
                                 profile="independent_review", reraise_model_unavailable=True)


def test_a_permanent_refusal_still_propagates_unchanged(monkeypatch):
    # The wrapper classifies exactly two exception types; anything else is the caller's.
    from llmxive.backends.base import PermanentBackendError

    _raise_from_route_chat(monkeypatch, PermanentBackendError("bad request"))
    with pytest.raises(PermanentBackendError):
        chat_with_model_fallback(_Fake(), _MSGS, model=None, max_tokens=64,
                                 reraise_model_unavailable=True)
