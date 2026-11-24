"""US5 AC3 — a no-LLM agent bypasses selection at BOTH layers."""
from __future__ import annotations

import pytest

from llmxive.backends.base import ChatMessage
from llmxive.model_selection.route import DETERMINISTIC_NO_LLM, route_chat


def test_route_chat_rejects_the_sentinel_profile_before_any_snapshot(monkeypatch):
    """Layer 2 (defense in depth): reaching the model layer with the sentinel is a
    programming error and must fail BEFORE snapshot/ledger work."""
    import llmxive.model_selection.route as route_mod

    def _boom(*_a, **_k):  # pragma: no cover - must never be called
        raise AssertionError("snapshot acquired before the sentinel guard fired")

    monkeypatch.setattr(route_mod, "runtime_snapshot", _boom)
    monkeypatch.setattr(route_mod, "_SNAPSHOT_CACHE", None)

    with pytest.raises(ValueError, match="deterministic-no-llm"):
        route_chat(
            [ChatMessage(role="user", content="hi")],
            profile=DETERMINISTIC_NO_LLM,
            max_tokens=100,
        )


def test_route_chat_still_rejects_the_sentinel_via_caller_model():
    """The pre-existing caller_model spelling must keep failing closed until
    Task 7 removes the last caller_model pins."""
    with pytest.raises(ValueError, match="deterministic-no-llm"):
        route_chat(
            [ChatMessage(role="user", content="hi")],
            caller_model=DETERMINISTIC_NO_LLM,
            max_tokens=100,
        )
