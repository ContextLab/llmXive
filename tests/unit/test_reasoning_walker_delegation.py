"""Slice-5 (Step B): ``reasoning_chat`` + ``chat_with_model_fallback`` — the
reasoning/analysis + convergence-panel entry points — now delegate to
``model_selection.route.route_chat`` (select() → execute()) instead of hand-walking
``MODEL_FALLBACKS`` on a single injected backend.

These pin the WRAPPER contract: intent forwarded (standard_generation profile +
caller model + reasoning-safe budget), the caller's injected backend adapted into a
``backend_factory`` (so a caller that built a real backend, or a test that injects a
fake, still serves its own candidates while other backends resolve via
``make_backend``), and the outage-classification contract preserved
(``ModelUnavailable``/``ChainExhausted`` → ``BackendUnavailable``; permanent
propagates).
"""

from __future__ import annotations

import pytest

from llmxive.backends.base import (
    BackendUnavailable,
    ChatMessage,
    ChatResponse,
    PermanentBackendError,
)
from llmxive.backends.router import (
    REASONING_MAX_TOKENS,
    chat_with_model_fallback,
    reasoning_chat,
)
from llmxive.model_selection.execute import ChainExhausted
from llmxive.model_selection.types import ModelUnavailable, RequirementOverrides

_MSGS = [ChatMessage(role="user", content="analyze")]
PRIMARY = "openai.gpt-oss-120b"


class _Fake:
    name = "dartmouth"

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
        return ChatResponse(text=f"OK {model}", model=model, backend="dartmouth")


def _patch_route(monkeypatch, impl):
    import llmxive.model_selection.route as route_mod

    monkeypatch.setattr(route_mod, "route_chat", impl)


# --------------------------------------------------------------------------- #
# reasoning_chat
# --------------------------------------------------------------------------- #


def test_reasoning_chat_delegates_with_reasoning_budget_default(monkeypatch):
    seen = {}

    def _fake_route(messages, **kwargs):
        seen.update(kwargs)
        return ChatResponse(text="OK", model=PRIMARY, backend="dartmouth")

    _patch_route(monkeypatch, _fake_route)
    resp = reasoning_chat(_Fake(), _MSGS, model=PRIMARY)
    assert resp.text == "OK"
    assert seen["profile"] == "standard_generation"
    assert seen["caller_model"] == PRIMARY
    assert seen["max_tokens"] == REASONING_MAX_TOKENS  # reasoning-safe default


def test_reasoning_chat_explicit_max_tokens_overrides_default(monkeypatch):
    seen = {}
    _patch_route(monkeypatch, lambda messages, **k: seen.update(k) or ChatResponse(text="x", model="m", backend="b"))
    reasoning_chat(_Fake(), _MSGS, model=PRIMARY, max_tokens=131_072)
    assert seen["max_tokens"] == 131_072


def test_reasoning_chat_threads_injected_backend_into_factory(monkeypatch):
    # The caller's backend must serve its own candidates; other backends resolve
    # via make_backend. Assert the factory route_chat received returns the injected
    # backend for its name.
    seen = {}

    def _fake_route(messages, **kwargs):
        seen.update(kwargs)
        return ChatResponse(text="x", model="m", backend="b")

    _patch_route(monkeypatch, _fake_route)
    injected = _Fake()
    reasoning_chat(injected, _MSGS, model=PRIMARY)
    factory = seen["backend_factory"]
    assert factory("dartmouth") is injected  # injected backend serves its own name


def test_reasoning_chat_translates_outage_to_backend_unavailable(monkeypatch):
    for exc in (ModelUnavailable("cold start"), ChainExhausted("all advanced")):
        _patch_route(monkeypatch, lambda *a, _e=exc, **k: (_ for _ in ()).throw(_e))
        with pytest.raises(BackendUnavailable):
            reasoning_chat(_Fake(), _MSGS, model=PRIMARY)


def test_reasoning_chat_propagates_permanent(monkeypatch):
    _patch_route(monkeypatch, lambda *a, **k: (_ for _ in ()).throw(PermanentBackendError("refused")))
    with pytest.raises(PermanentBackendError):
        reasoning_chat(_Fake(), _MSGS, model=PRIMARY)


def test_reasoning_chat_forwards_overrides(monkeypatch):
    # Spec 026 slice 6: escalation constraints (RequirementOverrides) must flow
    # from the walker through to route_chat's `overrides` kwarg UNCHANGED (same
    # object), so the caller's escalation ladder actually reaches selection.
    seen = {}

    def _fake_route(messages, **kwargs):
        seen.update(kwargs)
        return ChatResponse(text="OK", model=PRIMARY, backend="dartmouth")

    _patch_route(monkeypatch, _fake_route)
    ov = RequirementOverrides(allow_paid=False, exclude_models=frozenset({"m"}))
    reasoning_chat(_Fake(), _MSGS, model=PRIMARY, overrides=ov)
    assert seen["overrides"] is ov


# --------------------------------------------------------------------------- #
# chat_with_model_fallback
# --------------------------------------------------------------------------- #


def test_chat_with_model_fallback_delegates_and_forwards_intent(monkeypatch):
    seen = {}

    def _fake_route(messages, **kwargs):
        seen.update(kwargs)
        return ChatResponse(text="OK", model=PRIMARY, backend="dartmouth")

    _patch_route(monkeypatch, _fake_route)
    resp = chat_with_model_fallback(_Fake(), _MSGS, model=PRIMARY, max_tokens=4096, temperature=0.0)
    assert resp.text == "OK"
    assert seen["profile"] == "standard_generation"
    assert seen["caller_model"] == PRIMARY
    assert seen["max_tokens"] == 4096
    assert seen["temperature"] == 0.0


def test_chat_with_model_fallback_translates_outage(monkeypatch):
    _patch_route(monkeypatch, lambda *a, **k: (_ for _ in ()).throw(ChainExhausted("outage")))
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(_Fake(), _MSGS, model=PRIMARY)
