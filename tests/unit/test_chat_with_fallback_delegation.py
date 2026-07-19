"""Slice-5 wiring: ``router.chat_with_fallback`` — the registry-agent routing
chokepoint — now delegates to ``model_selection.route.route_chat`` (select() →
execute()) instead of walking ``MODEL_FALLBACKS`` by hand.

Spec 026 slice 7: the obsolete ``default_backend`` / ``fallback_backends`` /
``model`` bridge parameters have been REMOVED from ``chat_with_fallback`` now
that every caller expresses its intent purely via ``profile`` — a call site
never pins a raw model id. These tests pin the WRAPPER contract: ``profile``
(+ budget) is forwarded to ``route_chat`` unchanged, and the legacy outage-
classification contract is preserved — a fully-ineligible or fully-exhausted
chain surfaces as ``BackendUnavailable`` (a clean run-loop abort with state
preserved) rather than a human-escalating ``BackendError``, while a
request-level permanent refusal propagates unchanged.
"""

from __future__ import annotations

import pytest

from llmxive.backends.base import (
    BackendUnavailable,
    ChatMessage,
    ChatResponse,
    PermanentBackendError,
)
from llmxive.backends.router import GENERATION_MAX_TOKENS, chat_with_fallback
from llmxive.model_selection.execute import ChainExhausted
from llmxive.model_selection.types import ModelUnavailable, RequirementOverrides

_MSGS = [ChatMessage(role="user", content="hello")]
QWEN = "qwen.qwen3.5-122b"


def _patch_route(monkeypatch, impl):
    # chat_with_fallback imports route_chat function-locally from the route module,
    # so patch the SOURCE attribute (resolved at call time).
    import llmxive.model_selection.route as route_mod

    monkeypatch.setattr(route_mod, "route_chat", impl)


def test_chat_with_fallback_forwards_profile_and_budget(monkeypatch):
    seen = {}

    def _fake_route(messages, **kwargs):
        seen.update(kwargs)
        seen["messages"] = list(messages)
        return ChatResponse(text="OK", model=QWEN, backend="dartmouth")

    _patch_route(monkeypatch, _fake_route)
    resp = chat_with_fallback(
        _MSGS,
        profile="deep_review",
        max_tokens=4096,
        temperature=0.0,
    )
    assert resp.text == "OK"
    assert seen["profile"] == "deep_review"
    assert seen["max_tokens"] == 4096
    assert seen["temperature"] == 0.0
    # No caller-side model pin exists anymore — the wrapper never threads one.
    assert "caller_model" not in seen
    assert "model" not in seen
    assert "default_backend" not in seen
    assert "fallback_backends" not in seen


def test_chat_with_fallback_defaults_to_generation_budget(monkeypatch):
    seen = {}

    def _fake_route(messages, **kwargs):
        seen.update(kwargs)
        return ChatResponse(text="OK", model=QWEN, backend="dartmouth")

    _patch_route(monkeypatch, _fake_route)
    chat_with_fallback(_MSGS)
    assert seen["max_tokens"] == GENERATION_MAX_TOKENS
    assert seen["profile"] == "standard_generation"  # the documented default


def test_chat_with_fallback_translates_model_unavailable_to_backend_unavailable(monkeypatch):
    def _fake_route(messages, **kwargs):
        raise ModelUnavailable("no eligible candidate (cold start)")

    _patch_route(monkeypatch, _fake_route)
    with pytest.raises(BackendUnavailable):
        chat_with_fallback(_MSGS)


def test_chat_with_fallback_translates_chain_exhausted_to_backend_unavailable(monkeypatch):
    def _fake_route(messages, **kwargs):
        raise ChainExhausted("every candidate advanced without success (outage)")

    _patch_route(monkeypatch, _fake_route)
    with pytest.raises(BackendUnavailable):
        chat_with_fallback(_MSGS)


def test_chat_with_fallback_propagates_permanent_refusal(monkeypatch):
    def _fake_route(messages, **kwargs):
        raise PermanentBackendError("hard refusal / bad request")

    _patch_route(monkeypatch, _fake_route)
    with pytest.raises(PermanentBackendError):
        chat_with_fallback(_MSGS)


def test_chat_with_fallback_forwards_overrides(monkeypatch):
    # Spec 026 slice 6: escalation constraints (RequirementOverrides) must flow
    # from the walker through to route_chat's `overrides` kwarg UNCHANGED (same
    # object), so the caller's escalation ladder actually reaches selection.
    seen = {}

    def _fake_route(messages, **kwargs):
        seen.update(kwargs)
        return ChatResponse(text="OK", model=QWEN, backend="dartmouth")

    _patch_route(monkeypatch, _fake_route)
    ov = RequirementOverrides(allow_paid=False, exclude_models=frozenset({"m"}))
    chat_with_fallback(
        _MSGS,
        overrides=ov,
    )
    assert seen["overrides"] is ov
