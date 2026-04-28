"""Base classes and protocols for the LLM backend chain (T020).

Each backend exposes a uniform `chat(messages, *, model, **kwargs)` API
that returns the model's text reply. The router (router.py) selects a
backend per agent registry config and falls back through the chain on
transient errors.

Per Constitution Principle IV (Free First) every backend in v1 has
is_paid=False; the schema asserts this invariant.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str


@dataclass(frozen=True)
class ChatResponse:
    text: str
    model: str
    backend: str
    cost_estimate_usd: float = 0.0  # v1 invariant: 0.0 for every free backend


class BackendError(RuntimeError):
    """Generic backend failure. Subclasses describe transient vs permanent."""


class TransientBackendError(BackendError):
    """A failure the router should fall back from (rate limit, 5xx, timeout)."""


class PermanentBackendError(BackendError):
    """A failure that should not trigger fallback (auth, bad request)."""


class BaseBackend(abc.ABC):
    """All backends implement this interface."""

    name: str = ""
    is_paid: bool = False  # invariant for v1

    @abc.abstractmethod
    def list_models(self) -> list[str]:
        """Return available model identifiers (FR-022 — never hardcode)."""

    @abc.abstractmethod
    def chat(
        self,
        messages: Iterable[ChatMessage],
        *,
        model: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ChatResponse:
        """Issue a chat completion request."""

    @abc.abstractmethod
    def healthcheck(self) -> bool:
        """Return True iff a minimal probe succeeds (used by preflight)."""


__all__ = [
    "BaseBackend",
    "BackendError",
    "ChatMessage",
    "ChatResponse",
    "PermanentBackendError",
    "TransientBackendError",
]
