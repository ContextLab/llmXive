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

#: Allowed image MIME types (Dartmouth's OpenAI-compatible vision endpoint).
_IMAGE_MIMES = frozenset({"image/png", "image/jpeg", "image/webp"})


@dataclass(frozen=True)
class TextPart:
    """A text span inside a multimodal message."""

    text: str


@dataclass(frozen=True)
class ImagePart:
    """An image inside a multimodal message.

    Dimensions and payload size are BOUNDED and validated here so the token
    estimator's per-image charge is a true UPPER bound (FR-003/FR-010): an
    unbounded payload priced at a fixed constant would invalidate the cost bound
    ``select()`` reserves against.
    """

    mime: str
    data: bytes
    width: int
    height: int

    def __post_init__(self) -> None:
        # Function-local: backends.base must not import model_selection at module scope.
        from llmxive.model_selection.tokens import MAX_IMAGE_BYTES, MAX_IMAGE_DIMENSION_PX

        if self.mime not in _IMAGE_MIMES:
            raise ValueError(
                f"ImagePart: unsupported mime {self.mime!r} (allowed: {sorted(_IMAGE_MIMES)})"
            )
        if self.width <= 0 or self.height <= 0:
            raise ValueError("ImagePart: dimension must be positive")
        if self.width > MAX_IMAGE_DIMENSION_PX or self.height > MAX_IMAGE_DIMENSION_PX:
            raise ValueError(
                f"ImagePart: dimension {self.width}x{self.height} exceeds the estimator's "
                f"supported maximum {MAX_IMAGE_DIMENSION_PX}px — downscale before selection "
                f"(the token upper bound is derived from it)"
            )
        if len(self.data) > MAX_IMAGE_BYTES:
            raise ValueError(
                f"ImagePart: {len(self.data)} bytes exceeds MAX_IMAGE_BYTES={MAX_IMAGE_BYTES}"
            )


ContentPart = TextPart | ImagePart


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str | tuple[ContentPart, ...]


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


class ModelDownError(TransientBackendError):
    """The specific model is UNAVAILABLE — not merely flickering.

    Two triggers: the model hung past its full per-request deadline
    (:class:`DeadlineExceededError`), or the gateway redirected to the
    maintenance/outage page (a 302 → ``outage.dartmouth.edu``). Both mean
    retrying the SAME model is futile and expensive (a deadline hang costs
    another full deadline; an outage redirect will recur), so retry layers must
    NOT burn the generous fast-flap retry budget on it — they fail fast and let
    the model-fallback chain escape to a healthy peer. Subclasses
    TransientBackendError so existing transient handling (router fallback, the
    panel's transient-no-escalation path) still treats it as recoverable;
    ordinary fast flaps (generic 5xx/connection-reset) are NOT ModelDownError and
    keep their generous retries.
    """


class DeadlineExceededError(ModelDownError):
    """A :class:`ModelDownError` where the model gave no response within its full
    per-request wall-clock deadline (e.g. 360s for a reasoning model)."""


class EmptyReplyError(TransientBackendError):
    """The model ANSWERED (HTTP 200, finish_reason stop/length) but the content was
    EMPTY — the qwen ``<think>``-mode flap: it burns completion tokens reasoning and
    returns nothing. Unlike a network 5xx (a true transient blip that a retry rides
    out), an empty reply is a CONSISTENT model behavior: a couple of stochastic
    retries may recover, but retrying the SAME flapping model the full ~8x (~5 min)
    just delays the fall-through to a healthy peer / the fast paid fallback. Retry
    layers cap it low (:data:`~llmxive.backends.dartmouth._EMPTY_REPLY_MAX_RETRIES`)
    so the router escapes quickly. Still a TransientBackendError so the model-
    fallback chain + panel transient-no-escalation path treat it as recoverable."""


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


class PaidGuardDenied(PermanentBackendError):
    """The free-first paid guard DECLINED this specific model — opt-in is off, or
    the daily credit budget has no headroom for it (``credits.paid_call_allowed``
    returned false). This is an EXPECTED skip, NOT a hard refusal: it says nothing
    about other candidates, so a model-chain walker SKIPS to the next candidate
    (spec 026 slice 1A ``CandidateDisposition.SKIP``) rather than aborting.

    Subclasses PermanentBackendError so the LEGACY router walker
    (``chat_with_model_fallback``) — which already caught the paid guard's bare
    ``PermanentBackendError`` (breaking to the next peer) — keeps IDENTICAL
    behavior; the split only gives the new ``execute`` seam a typed skip signal.
    """


class UnsupportedFeatureError(PermanentBackendError):
    """This backend/model cannot serve a feature THIS request needs (e.g. image
    content on a text-only local checkpoint). Like ``PaidGuardDenied`` this is a
    CANDIDATE-ineligibility signal, not a request-level refusal: it says nothing
    about other candidates, so the chain walker SKIPS to the next one
    (``CandidateDisposition.SKIP``) instead of aborting. Without this dedicated
    type it would land on the generic ``PermanentBackendError`` branch and ABORT
    the chain (``router.disposition_of``, line 211).
    """


def render_text_content(content: str | tuple[ContentPart, ...]) -> str:
    """Render ``ChatMessage.content`` as a display/audit-safe string.

    ``str`` content passes through unchanged. Parts-tuple content joins each
    :class:`TextPart`'s text; each :class:`ImagePart` renders as a
    METADATA-only placeholder (mime, dimensions, byte length) — the raw image
    bytes are NEVER included, so callers that log or JSON-serialize this value
    (e.g. the speckit inspection-record writer) cannot leak image payloads
    into audit logs, and string ops (``+``, ``.join``, slicing) that assume a
    plain string keep working on the result.
    """
    if isinstance(content, str):
        return content
    pieces: list[str] = []
    for part in content:
        if isinstance(part, TextPart):
            pieces.append(part.text)
        elif isinstance(part, ImagePart):
            pieces.append(f"[image: {part.mime}, {part.width}x{part.height}, {len(part.data)} bytes]")
        else:  # pragma: no cover - the union is closed
            raise TypeError(f"unknown content part {type(part).__name__}")
    return "\n".join(pieces)


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
        raise DeadlineExceededError(
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
        deadline_s: float | None = None,
    ) -> ChatResponse:
        """Issue a chat completion request. ``deadline_s`` is an optional per-call
        wall-clock deadline (spec 026 ExecutionOptions); backends that cannot
        enforce it (e.g. local CPU generation) treat it as advisory."""

    @abc.abstractmethod
    def healthcheck(self) -> bool:
        """Return True iff a minimal probe succeeds (used by preflight)."""


__all__ = [
    "BackendError",
    "BackendUnavailable",
    "BaseBackend",
    "ChatMessage",
    "ChatResponse",
    "ContentPart",
    "DeadlineExceededError",
    "EmptyReplyError",
    "ImagePart",
    "ModelDownError",
    "PaidGuardDenied",
    "PermanentBackendError",
    "TextPart",
    "TransientBackendError",
    "UnsupportedFeatureError",
    "invoke_with_deadline",
    "render_text_content",
]
