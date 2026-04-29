"""Dartmouth Chat backend via langchain-dartmouth (T020).

Uses ChatDartmouth(ChatOpenAI). Models are resolved at runtime via
ChatDartmouth.list() and CloudModelListing.list() per FR-022 — never
hardcoded.
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


class DartmouthBackend(BaseBackend):
    name = "dartmouth"
    is_paid = False

    def __init__(self, *, model_name: str | None = None) -> None:
        if not os.environ.get("DARTMOUTH_CHAT_API_KEY"):
            raise PermanentBackendError(
                "DARTMOUTH_CHAT_API_KEY is not set (required by Dartmouth backend)"
            )
        self._model_name = model_name

    def _client(self, model: str):  # type: ignore[no-untyped-def]
        try:
            from langchain_dartmouth.llms import ChatDartmouth
        except ImportError as exc:
            raise PermanentBackendError(
                "langchain-dartmouth is not installed; pip install -e ."
            ) from exc
        return ChatDartmouth(model_name=model)

    def list_models(self) -> list[str]:
        try:
            from langchain_dartmouth.llms import ChatDartmouth
        except ImportError as exc:
            raise PermanentBackendError("langchain-dartmouth missing") from exc
        try:
            # Prefer ChatDartmouth.list() if exposed; otherwise fall back to
            # the documented CloudModelListing helper.
            listing = getattr(ChatDartmouth, "list", None)
            if callable(listing):
                models = list(listing())
            else:
                from langchain_dartmouth.llms import CloudModelListing
                models = list(CloudModelListing().list())
            # ChatDartmouth.list() returns Model objects; we need plain id
            # strings (e.g. 'qwen.qwen3.5-122b') that can be passed to
            # ChatDartmouth(model_name=...) per langchain-dartmouth's API.
            ids: list[str] = []
            for m in models:
                # Prefer the canonical .id attribute; fall back to .name; finally str()
                mid = getattr(m, "id", None) or getattr(m, "name", None) or str(m)
                ids.append(str(mid))
            return ids
        except Exception as exc:  # pragma: no cover — surfaced in preflight
            raise TransientBackendError(f"Dartmouth list_models failed: {exc}") from exc

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

        kwargs: dict[str, object] = {}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if temperature is not None:
            kwargs["temperature"] = temperature
        try:
            reply = client.invoke(msg_objs, **kwargs)  # type: ignore[arg-type]
        except Exception as exc:
            text = str(exc).lower()
            if any(s in text for s in ("rate limit", "quota", "429", "timeout", "5xx")):
                raise TransientBackendError(str(exc)) from exc
            raise PermanentBackendError(str(exc)) from exc

        return ChatResponse(
            text=str(reply.content),
            model=model,
            backend=self.name,
            cost_estimate_usd=0.0,  # Dartmouth Chat is free for community members
        )

    def healthcheck(self) -> bool:
        try:
            self.list_models()
            return True
        except Exception:
            return False


__all__ = ["DartmouthBackend"]
