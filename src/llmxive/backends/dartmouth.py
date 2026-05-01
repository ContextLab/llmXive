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


def _ensure_api_key_env() -> None:
    """Resolve the Dartmouth Chat API key into the environment.

    Resolution order (matches credentials.load_dartmouth_key):
      1. existing env var (CI / GHA)
      2. ~/.config/llmxive/credentials.toml (set by `llmxive auth set`)

    Why mutate the env: ChatDartmouth (langchain) reads the key from
    `DARTMOUTH_CHAT_API_KEY` in os.environ, so we must populate it
    before instantiating the client.
    """
    if os.environ.get("DARTMOUTH_CHAT_API_KEY"):
        return
    try:
        from llmxive.credentials import load_dartmouth_key

        key = load_dartmouth_key(prompt_if_missing=False)
    except Exception:
        key = None
    if key:
        os.environ["DARTMOUTH_CHAT_API_KEY"] = key


class DartmouthBackend(BaseBackend):
    name = "dartmouth"
    is_paid = False

    def __init__(self, *, model_name: str | None = None) -> None:
        _ensure_api_key_env()
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
        # 10 min per-request timeout. Reasoning models like
        # qwen.qwen3.5-122b can legitimately take 2-5 min on big
        # 32K-token completions, but anything past 10 min is a
        # hung connection. Without this the implementer can sit on
        # a single LLM call for 50+ min holding the project lock.
        # ChatDartmouth.__init__ doesn't expose `timeout` directly
        # but accepts it via model_kwargs (it forwards to the
        # underlying ChatOpenAI which DOES have a timeout field).
        # Suppress the noisy "should be specified explicitly"
        # warning since this is the intended escape hatch.
        import warnings as _warnings

        with _warnings.catch_warnings():
            _warnings.filterwarnings(
                "ignore", message=r".*Parameters \{'timeout'\}.*"
            )
            return ChatDartmouth(
                model_name=model, model_kwargs={"timeout": 600}
            )

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
            transient_markers = (
                "rate limit", "quota", "429", "timeout", "5xx",
                # Dartmouth's vLLM backend transients:
                "500", "502", "503", "504", "internal server error",
                "cannot connect to host", "connection reset", "connection refused",
                "service unavailable", "bad gateway", "gateway timeout",
                "internalservererror", "operation not permitted",
                "litellm.internalservererror",
                # Network-level transients:
                "temporary failure", "name resolution", "connection error",
            )
            if any(s in text for s in transient_markers):
                raise TransientBackendError(str(exc)) from exc
            raise PermanentBackendError(str(exc)) from exc

        text_out = str(reply.content)
        # Detect "reasoning ate the budget" failure mode: reasoning models
        # (Qwen 3.5, gpt-oss) emit internal <think> tokens that count
        # toward the completion budget but are stripped from .content.
        # When max_tokens is too small the entire budget is consumed and
        # we get '' back with finish_reason='length'. Treat that as
        # transient so the router falls through to a non-reasoning model
        # rather than silently passing junk downstream.
        meta = getattr(reply, "response_metadata", {}) or {}
        finish_reason = meta.get("finish_reason")
        if not text_out.strip() and finish_reason == "length":
            usage = meta.get("token_usage", {}) or {}
            raise TransientBackendError(
                f"Dartmouth model {model!r} returned empty content "
                f"(finish_reason=length, completion_tokens={usage.get('completion_tokens')}); "
                "reasoning budget exhausted — retry with larger max_tokens or fall through to a non-reasoning model"
            )
        if not text_out.strip():
            # Other empty replies (filter, refusal, etc.) — surface loudly.
            raise PermanentBackendError(
                f"Dartmouth model {model!r} returned empty content "
                f"(finish_reason={finish_reason!r}, additional_kwargs={getattr(reply, 'additional_kwargs', {})})"
            )

        return ChatResponse(
            text=text_out,
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
