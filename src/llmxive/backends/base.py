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
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TypeVar


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


class BackendUnavailable(PermanentBackendError):
    """A backend's circuit breaker is OPEN: the endpoint is persistently down.

    Raised immediately (no retry/fallback burn) once a per-backend circuit
    breaker trips on a SUSTAINED outage — too many consecutive fully-failed
    calls, or no success within a wall-clock window. Subclasses
    PermanentBackendError so the run loop's existing permanent-error handling
    aborts the run cleanly (stage state preserved for the next scheduled tick)
    instead of thrashing for hours on a dead endpoint.
    """


_T = TypeVar("_T")


def invoke_with_deadline(
    fn: Callable[[], _T],
    *,
    timeout: float,
    description: str,
) -> _T:
    """Run ``fn()`` under a hard wall-clock deadline and return its result.

    LLM client libraries (langchain's ``ChatDartmouth``, which wraps
    ``ChatOpenAI``) accept a nominal ``timeout`` but forward it as a
    *chat-completion body parameter*, not as an
    HTTP/socket timeout. A sick connection therefore blocks the calling thread
    indefinitely — observed in CI as a backend ``invoke`` hanging for ~54 min
    until the job-level timeout killed it.

    This helper bounds that. ``fn`` runs on a **daemon** thread; if it blows the
    deadline we abandon it and raise :class:`TransientBackendError` so the
    router falls through to a peer backend. A daemon thread never blocks
    interpreter exit — which is precisely why ``ThreadPoolExecutor`` is the
    WRONG tool here: its context-manager ``__exit__`` (and ``shutdown(wait=True)``)
    would itself hang waiting for the stuck worker, re-creating the very hang
    this guards against.

    On success returns ``fn``'s value. If ``fn`` raises, that exception is
    re-raised in the calling thread so the backend's own error classifier can
    decide transient-vs-permanent.
    """
    result: list[_T] = []
    error: list[BaseException] = []

    def _runner() -> None:
        try:
            result.append(fn())
        except BaseException as exc:
            error.append(exc)

    worker = threading.Thread(
        target=_runner, name=f"llmxive-backend-{description}", daemon=True
    )
    worker.start()
    worker.join(timeout)
    if worker.is_alive():
        raise TransientBackendError(
            f"{description} hung past {timeout:.0f}s deadline (no response received)"
        )
    if error:
        raise error[0]
    return result[0]


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
    "BackendError",
    "BackendUnavailable",
    "BaseBackend",
    "ChatMessage",
    "ChatResponse",
    "PermanentBackendError",
    "TransientBackendError",
    "invoke_with_deadline",
]
