"""Exercise the deployed primary on PRs and every configured free peer nightly."""

from __future__ import annotations

import os

import pytest

from llmxive.backends.dartmouth import KNOWN_FREE_MODELS
from llmxive.backends.router import DEFAULT_MODEL, MODEL_FALLBACKS, REASONING_MAX_TOKENS

_MODELS = [
    pytest.param(DEFAULT_MODEL, id="configured-primary"),
    *(
        pytest.param(model, id=model, marks=pytest.mark.slow)
        for model in dict.fromkeys(MODEL_FALLBACKS.get(DEFAULT_MODEL, []))
        if model != DEFAULT_MODEL and model in KNOWN_FREE_MODELS
    ),
]


@pytest.mark.skipif(
    not os.environ.get("DARTMOUTH_CHAT_API_KEY"),
    reason="DARTMOUTH_CHAT_API_KEY not set; live coverage unavailable",
)
@pytest.mark.parametrize("model_id", _MODELS)
def test_dartmouth_real_chat(model_id: str) -> None:
    from llmxive.backends.base import ChatMessage
    from llmxive.backends.dartmouth import DartmouthBackend, is_free_model

    backend = DartmouthBackend()
    models = backend.list_models()
    assert model_id in models, f"configured model {model_id} missing from live catalog"
    assert is_free_model(model_id), f"configured free model {model_id} is not free"
    # Direct call: fallback must not hide a broken primary. Use the production
    # reasoning allowance and deadline, not an artificial short timeout/budget.
    response = backend.chat(
        [ChatMessage(role="user", content="Reply with the single word OK.")],
        model=model_id,
        max_tokens=REASONING_MAX_TOKENS,
        temperature=0.0,
    )
    assert response.text.strip(), f"empty response from {model_id}"
    assert response.model == model_id
    assert response.backend == "dartmouth"
    assert response.cost_estimate_usd == 0.0
