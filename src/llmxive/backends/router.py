"""Backend router (T020) — falls back through a chain on transient errors.

The agent registry declares a default backend and an ordered list of
fallback backends per agent. The router is configured per-call from
those declarations.
"""

from __future__ import annotations

from typing import Iterable

from llmxive.backends.base import (
    BaseBackend,
    BackendError,
    ChatMessage,
    ChatResponse,
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.dartmouth import DartmouthBackend
from llmxive.backends.huggingface import HuggingFaceBackend
from llmxive.backends.local import LocalBackend


_REGISTRY: dict[str, type[BaseBackend]] = {
    "dartmouth": DartmouthBackend,
    "huggingface": HuggingFaceBackend,
    "local": LocalBackend,
}


def make_backend(name: str) -> BaseBackend:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise PermanentBackendError(f"unknown backend: {name!r}")
    return cls()  # type: ignore[call-arg]


def chat_with_fallback(
    messages: Iterable[ChatMessage],
    *,
    default_backend: str,
    fallback_backends: list[str],
    model: str,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> ChatResponse:
    """Try default backend; on TransientBackendError, walk the fallback chain."""
    chain = [default_backend, *fallback_backends]
    last_err: BackendError | None = None
    msg_list = list(messages)
    for name in chain:
        try:
            backend = make_backend(name)
        except PermanentBackendError as exc:
            last_err = exc
            continue
        try:
            return backend.chat(
                msg_list,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except TransientBackendError as exc:
            last_err = exc
            continue
        except PermanentBackendError as exc:
            # Permanent failure on this backend (auth/config) — try the next.
            last_err = exc
            continue
    raise BackendError(
        f"every backend in chain {chain} failed; last error: {last_err}"
    )


__all__ = ["chat_with_fallback", "make_backend"]
