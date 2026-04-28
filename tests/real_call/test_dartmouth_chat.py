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

    response = backend.chat(
        [ChatMessage(role="user", content="Reply with the single word OK.")],
        model=models[0],
        max_tokens=8,
        temperature=0.0,
    )
    assert response.text.strip()
    assert response.backend == "dartmouth"
    assert response.cost_estimate_usd == 0.0
