"""Real-call: HuggingFace fallback invocation (T033)."""

from __future__ import annotations

import os

import pytest


@pytest.mark.skipif(not os.environ.get("HF_TOKEN"), reason="HF_TOKEN not set")
def test_huggingface_real_chat() -> None:
    from llmxive.backends.huggingface import HuggingFaceBackend
    from llmxive.backends.base import ChatMessage

    backend = HuggingFaceBackend()
    response = backend.chat(
        [ChatMessage(role="user", content="Reply OK")],
        model="Qwen/Qwen2.5-7B-Instruct",
        max_tokens=8,
        temperature=0.0,
    )
    assert response.text.strip()
    assert response.backend == "huggingface"
    assert response.cost_estimate_usd == 0.0
