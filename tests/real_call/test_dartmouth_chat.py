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

    # Prefer the v1 default model (qwen.qwen3.5-122b). It is a *reasoning*
    # model: it emits internal <think> tokens that count toward the
    # completion budget but are stripped from .content. With too small a
    # max_tokens the reasoning block consumes the entire budget and we
    # get '' back with finish_reason=length — which dartmouth.py correctly
    # surfaces as a TransientBackendError so the router falls through to a
    # peer. So this test must give it a generous budget (see below).
    # Fall back to gemma-3-27b (non-reasoning) or anything not flagged.
    preferred = ("qwen.qwen3.5-122b", "google.gemma-3-27b-it")
    model_id = next((m for m in preferred if m in models), None)
    if model_id is None:
        non_reasoning = [m for m in models if "gpt-oss" not in m and "reasoning" not in m.lower()]
        model_id = non_reasoning[0] if non_reasoning else models[0]

    # Reasoning models can burn 1-2K tokens on a <think> block even for a
    # trivial prompt; 4096 leaves comfortable headroom for the answer.
    response = backend.chat(
        [ChatMessage(role="user", content="Reply with the single word OK.")],
        model=model_id,
        max_tokens=4096,
        temperature=0.0,
    )
    assert response.text.strip(), (
        f"empty response from {model_id} — reasoning may have consumed the "
        f"max_tokens budget; bump max_tokens or pick a non-reasoning model"
    )
    assert response.backend == "dartmouth"
    assert response.cost_estimate_usd == 0.0
