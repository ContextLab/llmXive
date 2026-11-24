"""Exercise the deployed primary on PRs and every configured free peer nightly."""

from __future__ import annotations

import os

import pytest

from llmxive.backends.router import REASONING_MAX_TOKENS

_NEEDS_KEY = pytest.mark.skipif(
    not os.environ.get("DARTMOUTH_CHAT_API_KEY"),
    reason="DARTMOUTH_CHAT_API_KEY not set; live coverage unavailable",
)


def _free_chain() -> tuple[str, ...]:
    """The free Dartmouth chain the selector offers a deep call RIGHT NOW (spec
    026): leader first, then every free peer. Resolved inside the test, from the
    live snapshot — there is no model table to read at import time. ``deep_review``
    admits no local candidate, so every id here is Dartmouth-hosted."""
    from llmxive.model_selection.route import free_peer_ids

    chain = free_peer_ids("deep_review")
    assert chain, "the selector offers no free model for deep_review"
    return chain


@_NEEDS_KEY
def test_dartmouth_real_chat_configured_primary() -> None:
    _exercise(_free_chain()[0])


@_NEEDS_KEY
@pytest.mark.slow
def test_dartmouth_real_chat_every_free_peer() -> None:
    failures: list[str] = []
    for model_id in _free_chain()[1:]:
        try:
            _exercise(model_id)
        except AssertionError as exc:  # report EVERY broken peer, not just the first
            failures.append(f"{model_id}: {exc}")
    assert not failures, "\n".join(failures)


def _exercise(model_id: str) -> None:
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
