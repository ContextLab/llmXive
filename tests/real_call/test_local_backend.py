"""Real-call: local (HF-models-run-locally via transformers) backend.

Replaces the former HuggingFace Inference API fallback test. HF models
are now run *locally* through the ``local`` backend (kind:
local_transformers), which loads open-weight models via the
``transformers`` library — no HF_TOKEN required.

Gated on LLMXIVE_REAL_TESTS=1 because local inference downloads model
weights from the Hugging Face Hub and needs ``torch`` + ``transformers``
installed. Mirrors the gating style of the other tests/real_call tests.
A tiny model is used so the download + forward pass stay cheap while
still exercising the real generation path (no mocks).
"""

from __future__ import annotations

import os

import pytest


@pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="set LLMXIVE_REAL_TESTS=1 to run the local-transformers real-call test",
)
def test_local_backend_real_chat() -> None:
    pytest.importorskip("torch", reason="local backend needs torch")
    pytest.importorskip("transformers", reason="local backend needs transformers")

    from llmxive.backends.base import ChatMessage
    from llmxive.backends.local import LocalBackend

    backend = LocalBackend()

    # list_models() pins the production small model; assert the contract.
    models = backend.list_models()
    assert isinstance(models, list) and models, "list_models() should return >=1 model"

    # Use a tiny instruct model for the actual forward pass so the weight
    # download + generation stay cheap. This is a genuine local inference
    # call through transformers — no network LLM API, no mocks.
    response = backend.chat(
        [ChatMessage(role="user", content="Say OK.")],
        model="sshleifer/tiny-gpt2",
        max_tokens=4,
        temperature=0.0,
    )
    assert isinstance(response.text, str)
    assert response.backend == "local"
    assert response.model == "sshleifer/tiny-gpt2"
    assert response.cost_estimate_usd == 0.0
