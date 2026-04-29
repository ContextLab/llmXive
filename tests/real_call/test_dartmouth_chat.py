"""Real-call: ChatDartmouth invocation (T032).

Skipped unless LLMXIVE_REAL_TESTS=1. Issues exactly one chat completion
against Dartmouth Chat with a tiny prompt and asserts response shape.
"""

from __future__ import annotations

import os

import pytest


@pytest.mark.skipif(
    not os.environ.get("DARTMOUTH_CHAT_API_KEY"),
    reason="DARTMOUTH_CHAT_API_KEY not set",
)
def test_dartmouth_real_chat() -> None:
    from llmxive.backends.dartmouth import DartmouthBackend
    from llmxive.backends.base import ChatMessage

    backend = DartmouthBackend()
    models = backend.list_models()
    assert isinstance(models, list) and models, "list_models() should return >=1 model"

    # Pick a non-reasoning chat model (reasoning models like gpt-oss-120b
    # need many output tokens before they emit user-visible text). Prefer
    # the v1 default (qwen.qwen3.5-122b), then gemma-3-27b, then anything
    # not flagged 'reasoning'.
    preferred = ("qwen.qwen3.5-122b", "google.gemma-3-27b-it")
    model_id = next((m for m in preferred if m in models), None)
    if model_id is None:
        non_reasoning = [m for m in models if "gpt-oss" not in m and "reasoning" not in m.lower()]
        model_id = non_reasoning[0] if non_reasoning else models[0]

    response = backend.chat(
        [ChatMessage(role="user", content="Reply with the single word OK.")],
        model=model_id,
        max_tokens=128,
        temperature=0.0,
    )
    assert response.text.strip(), (
        f"empty response from {model_id} — try a non-reasoning chat model"
    )
    assert response.backend == "dartmouth"
    assert response.cost_estimate_usd == 0.0
