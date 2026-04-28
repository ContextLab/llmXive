"""Hugging Face Inference (free tier) backend (T020).

Used as the fallback when Dartmouth is rate-limited or unavailable
(FR-019). Models default to a small free-tier-friendly chat model unless
the agent registry overrides.
"""

from __future__ import annotations

import os
from typing import Iterable

from llmxive.backends.base import (
    BaseBackend,
    ChatMessage,
    ChatResponse,
    PermanentBackendError,
    TransientBackendError,
)


class HuggingFaceBackend(BaseBackend):
    name = "huggingface"
    is_paid = False

    def __init__(self) -> None:
        # Token check is deferred to chat() so list_models() and healthcheck()
        # remain usable on a fresh fork during preflight bootstrap.
        pass

    def _client(self, model: str):  # type: ignore[no-untyped-def]
        if not os.environ.get("HF_TOKEN"):
            raise PermanentBackendError("HF_TOKEN is not set (required by HF backend)")
        try:
            from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
        except ImportError as exc:
            raise PermanentBackendError("langchain-huggingface is not installed") from exc
        endpoint = HuggingFaceEndpoint(repo_id=model, max_new_tokens=512)
        return ChatHuggingFace(llm=endpoint)

    def list_models(self) -> list[str]:
        # HF Inference exposes thousands; the registry pins one per agent.
        # Surface a small whitelist so preflight can verify reachability.
        return [
            "Qwen/Qwen2.5-7B-Instruct",
            "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.3",
        ]

    def chat(
        self,
        messages: Iterable[ChatMessage],
        *,
        model: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ChatResponse:
        try:
            from langchain_core.messages import (
                AIMessage,
                HumanMessage,
                SystemMessage,
            )
        except ImportError as exc:
            raise PermanentBackendError("langchain-core is not installed") from exc

        client = self._client(model)
        msg_objs = []
        for m in messages:
            if m.role == "system":
                msg_objs.append(SystemMessage(content=m.content))
            elif m.role == "assistant":
                msg_objs.append(AIMessage(content=m.content))
            else:
                msg_objs.append(HumanMessage(content=m.content))

        try:
            reply = client.invoke(msg_objs)
        except Exception as exc:
            text = str(exc).lower()
            if any(s in text for s in ("rate limit", "quota", "429", "timeout", "5xx")):
                raise TransientBackendError(str(exc)) from exc
            raise PermanentBackendError(str(exc)) from exc

        return ChatResponse(
            text=str(reply.content),
            model=model,
            backend=self.name,
            cost_estimate_usd=0.0,
        )

    def healthcheck(self) -> bool:
        return bool(os.environ.get("HF_TOKEN"))


__all__ = ["HuggingFaceBackend"]
