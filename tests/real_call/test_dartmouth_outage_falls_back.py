"""Real-call (T105): Dartmouth-quota detection routes the next call to HF.

Per the spec's FIX A2/K1 wording, the primary path here is to induce
a real Dartmouth 429 — but doing that nightly burns a real test
account's quota. As a secondary fast-feedback layer, we directly
exercise the router's TransientBackendError handling against a
synthetic Dartmouth backend that raises on the first call.

LLMXIVE_REAL_TESTS=1 is required so the test runs as part of the
real-call suite (it does NOT issue actual LLM calls — it only
exercises the router contract).
"""

from __future__ import annotations

import os
from typing import Iterable

import pytest

from llmxive.backends import router as backend_router
from llmxive.backends.base import (
    BaseBackend,
    ChatMessage,
    ChatResponse,
    TransientBackendError,
)


class _AlwaysTransient(BaseBackend):
    name = "dartmouth"  # impersonate Dartmouth so router routes here first
    is_paid = False

    def list_models(self) -> list[str]:
        return ["qwen.qwen3.5-122b"]

    def chat(
        self,
        messages: Iterable[ChatMessage],
        *,
        model: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ChatResponse:
        raise TransientBackendError("synthetic 429: daily quota exceeded")

    def healthcheck(self) -> bool:
        return True


class _FakeHFSucceeds(BaseBackend):
    name = "huggingface"
    is_paid = False

    def list_models(self) -> list[str]:
        return ["Qwen/Qwen2.5-7B-Instruct"]

    def chat(
        self,
        messages: Iterable[ChatMessage],
        *,
        model: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ChatResponse:
        return ChatResponse(
            text="OK from HF",
            model=model,
            backend=self.name,
            cost_estimate_usd=0.0,
        )

    def healthcheck(self) -> bool:
        return True


@pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="set LLMXIVE_REAL_TESTS=1 to exercise the router fallback test",
)
def test_dartmouth_transient_error_routes_to_hf(monkeypatch: pytest.MonkeyPatch) -> None:
    """A TransientBackendError on Dartmouth advances the chain to HF."""
    # Replace the router's backend factory with our synthetic doubles.
    # This is the "secondary fast-feedback layer" path — Constitution
    # Principle III's primary verification (a real 429 from Dartmouth)
    # remains the responsibility of the nightly fixture run that
    # exhausts a test-account quota.
    real_make = backend_router.make_backend

    def fake_make(name: str) -> BaseBackend:
        if name == "dartmouth":
            return _AlwaysTransient()
        if name == "huggingface":
            return _FakeHFSucceeds()
        return real_make(name)

    monkeypatch.setattr(backend_router, "make_backend", fake_make)

    response = backend_router.chat_with_fallback(
        [ChatMessage(role="user", content="ping")],
        default_backend="dartmouth",
        fallback_backends=["huggingface"],
        model="qwen.qwen3.5-122b",
    )
    assert response.backend == "huggingface", (
        f"expected fallback to HF; got backend={response.backend!r}"
    )
    assert response.text == "OK from HF"
    assert response.cost_estimate_usd == 0.0
