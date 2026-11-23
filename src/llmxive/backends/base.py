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
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TypeVar

#: Allowed image MIME types (Dartmouth's OpenAI-compatible vision endpoint).
_IMAGE_MIMES = frozenset({"image/png", "image/jpeg", "image/webp"})

#: JPEG Start-Of-Frame markers that carry dimensions (0xC0-0xCF minus the
#: non-SOF markers DHT/JPG/DAC that share that range).
_JPEG_SOF_MARKERS = frozenset(range(0xC0, 0xD0)) - {0xC4, 0xC8, 0xCC}


def _parse_png_dimensions(data: bytes) -> tuple[int, int]:
    """Parse ``(width, height)`` from a PNG's IHDR chunk (fixed offset: 8-byte
    signature, 4-byte chunk length, 4-byte ``IHDR`` type, then 4+4 bytes of
    width/height, big-endian). Raises :class:`ValueError` for anything that
    isn't a well-formed PNG header — never guesses.

    Also applies two CHEAP structural framing checks (not a CRC/pixel
    decode): the declared IHDR chunk length must actually be present in the
    buffer (data + trailing CRC), and an IEND marker must exist somewhere —
    together these reject a stub that only fakes the fixed-offset header
    bytes (e.g. a signature + IHDR type + width/height with no CRC, no
    IDAT, no IEND) that the fixed-offset read alone would happily accept.
    """
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("ImagePart: not a PNG (bad signature)")
    if len(data) < 24 or data[12:16] != b"IHDR":
        raise ValueError("ImagePart: truncated/invalid PNG (missing IHDR chunk)")
    ihdr_declared_len = int.from_bytes(data[8:12], "big")
    # The PNG spec fixes IHDR at EXACTLY 13 bytes (4 width + 4 height + 1 each
    # of bit depth, colour type, compression, filter, interlace). Requiring it
    # is cheap and definitive, and it is what makes the fixed-offset
    # width/height read below legitimate: without it a forged 0-length IHDR
    # passes the buffer check (which then only needs 20 bytes) while the
    # dimensions are read from data[16:24] — bytes lying OUTSIDE the declared
    # IHDR data, i.e. dimensions that are not the canonical header at all.
    if ihdr_declared_len != 13:
        raise ValueError(
            "ImagePart: truncated/invalid PNG (IHDR length is "
            f"{ihdr_declared_len}, but the PNG spec fixes it at 13)"
        )
    # IHDR chunk layout after the 8-byte signature: 4(length) + 4(type) +
    # <declared length> data bytes + 4(CRC). The buffer must actually
    # contain that many bytes, or this is a truncated/forged chunk.
    if len(data) < 8 + 4 + 4 + ihdr_declared_len + 4:
        raise ValueError(
            "ImagePart: truncated/invalid PNG (declared IHDR chunk length "
            f"{ihdr_declared_len} exceeds the buffer)"
        )
    if b"IEND" not in data:
        raise ValueError("ImagePart: truncated/invalid PNG (missing IEND marker)")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if width <= 0 or height <= 0:
        raise ValueError(f"ImagePart: invalid PNG dimensions {width}x{height}")
    return width, height


def _parse_jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Parse ``(width, height)`` by scanning JPEG markers for the first
    Start-Of-Frame (SOF0/SOF2/...) segment, which carries the real decoded
    dimensions. Raises :class:`ValueError` on anything truncated, malformed,
    or lacking a SOF segment — never guesses.

    Also applies a CHEAP structural framing check (not a full entropy-coded
    scan decode): an EOI (``\\xff\\xd9``) marker must exist somewhere in the
    buffer. A SOF segment alone can look completely valid — width/height
    parse cleanly — even when the file was truncated right after the
    header, before any of the actual compressed scan data / trailer; this
    check rejects that case instead of returning dimensions for a stream
    that never closes.
    """
    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        raise ValueError("ImagePart: not a JPEG (bad SOI marker)")
    i, n = 2, len(data)
    dims: tuple[int, int] | None = None
    while i < n:
        if data[i] != 0xFF:
            i += 1  # resync: not a marker byte
            continue
        j = i
        while j < n and data[j] == 0xFF:  # skip 0xFF fill bytes
            j += 1
        if j >= n:
            break
        marker = data[j]
        i = j + 1
        if marker == 0x00 or marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            continue  # standalone / stuffing marker: no length field
        if marker == 0xD9:  # EOI
            break
        if i + 2 > n:
            raise ValueError("ImagePart: truncated JPEG segment")
        seg_len = int.from_bytes(data[i : i + 2], "big")
        if seg_len < 2 or i + seg_len > n:
            raise ValueError("ImagePart: truncated/invalid JPEG segment")
        if marker in _JPEG_SOF_MARKERS:
            if seg_len < 7:
                raise ValueError("ImagePart: truncated JPEG SOF segment")
            height = int.from_bytes(data[i + 3 : i + 5], "big")
            width = int.from_bytes(data[i + 5 : i + 7], "big")
            if width <= 0 or height <= 0:
                raise ValueError(f"ImagePart: invalid JPEG dimensions {width}x{height}")
            dims = (width, height)
            break
        i += seg_len
        if marker == 0xDA:  # SOS: entropy-coded scan data follows, stop scanning
            break
    if dims is None:
        raise ValueError("ImagePart: JPEG has no SOF marker (truncated or unsupported)")
    if b"\xff\xd9" not in data:
        raise ValueError("ImagePart: truncated JPEG (missing EOI marker)")
    return dims


def _parse_webp_dimensions(data: bytes) -> tuple[int, int]:
    """Parse ``(width, height)`` from a WebP RIFF container: VP8 (lossy),
    VP8L (lossless), or VP8X (extended) chunk layouts. Raises
    :class:`ValueError` on anything truncated, malformed, or an unrecognized
    chunk type — never guesses.

    Also applies a CHEAP structural framing check (not a full chunk walk):
    the RIFF size field (bytes 4:8, little-endian) declares the byte count
    of everything after it (``WEBP`` + all chunks) — the buffer must
    actually contain that many bytes, or this is a truncated download that
    the fixed-offset VP8/VP8L/VP8X reads alone would not catch.
    """
    if len(data) < 16 or data[0:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("ImagePart: not a WebP (bad RIFF/WEBP header)")
    riff_declared_size = int.from_bytes(data[4:8], "little")
    if len(data) < 8 + riff_declared_size:
        raise ValueError(
            f"ImagePart: truncated WebP (RIFF size {riff_declared_size} exceeds "
            f"the buffer, which has only {len(data) - 8} bytes after the RIFF header)"
        )
    fourcc = data[12:16]
    if fourcc == b"VP8X":
        if len(data) < 30:
            raise ValueError("ImagePart: truncated WebP VP8X chunk")
        payload = data[20:30]
        width = int.from_bytes(payload[4:7], "little") + 1
        height = int.from_bytes(payload[7:10], "little") + 1
        return width, height
    if fourcc == b"VP8 ":
        if len(data) < 30:
            raise ValueError("ImagePart: truncated WebP VP8 chunk")
        chunk = data[20:30]
        if chunk[3:6] != b"\x9d\x01\x2a":
            raise ValueError("ImagePart: WebP VP8 chunk has a bad start code")
        width = int.from_bytes(chunk[6:8], "little") & 0x3FFF
        height = int.from_bytes(chunk[8:10], "little") & 0x3FFF
        if width <= 0 or height <= 0:
            raise ValueError(f"ImagePart: invalid WebP dimensions {width}x{height}")
        return width, height
    if fourcc == b"VP8L":
        if len(data) < 25:
            raise ValueError("ImagePart: truncated WebP VP8L chunk")
        chunk = data[20:25]
        if chunk[0] != 0x2F:
            raise ValueError("ImagePart: WebP VP8L chunk has a bad signature")
        bits = int.from_bytes(chunk[1:5], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        return width, height
    raise ValueError(f"ImagePart: unrecognized WebP chunk type {fourcc!r}")


def parse_image_dimensions(mime: str, data: bytes) -> tuple[int, int]:
    """Parse ``(width, height)`` CANONICALLY from encoded image bytes for one
    of the three allowed mimes — the provider processes the BYTES, not any
    caller-supplied metadata, so this is the only trustworthy source of
    dimensions. A defensive, total function per allowed mime: well-formed
    input returns real dimensions; anything unparseable or whose content
    doesn't match ``mime`` (each parser checks the format's own
    magic/signature bytes) raises :class:`ValueError` — it never silently
    passes through a guess.

    What is validated, precisely: the format's magic/signature bytes, cheap
    STRUCTURAL framing (PNG: the declared IHDR chunk is fully present in the
    buffer and an IEND marker exists; JPEG: an EOI marker exists; WebP: the
    RIFF size field is consistent with the buffer length), and the canonical
    dimension header itself. What is deliberately NOT validated: full
    pixel-level decodability, chunk/segment CRCs, or a complete walk of
    every chunk/segment after the header — a file can pass this check and
    still fail to decode as a real image (e.g. corrupt IDAT data past the
    header). This is a proportionate, cheap check against the specific
    failure this module guards against (a caller lying about, or a network
    truncating, the bytes the token-cost bound is derived from) — not a
    general-purpose image-integrity verifier.

    Deliberately dependency-free (stdlib only, no PIL): this module is
    imported everywhere, so it must not gain a hard imaging dependency.
    """
    if mime == "image/png":
        return _parse_png_dimensions(data)
    if mime == "image/jpeg":
        return _parse_jpeg_dimensions(data)
    if mime == "image/webp":
        return _parse_webp_dimensions(data)
    raise ValueError(f"ImagePart: unsupported mime {mime!r} (allowed: {sorted(_IMAGE_MIMES)})")


@dataclass(frozen=True)
class TextPart:
    """A text span inside a multimodal message."""

    text: str


@dataclass(frozen=True)
class ImagePart:
    """An image inside a multimodal message.

    Dimensions and payload size are BOUNDED and VERIFIED here so the token
    estimator's per-image charge is a true UPPER bound (FR-003/FR-010): an
    unbounded payload priced at a fixed constant would invalidate the cost
    bound ``select()`` reserves against.

    ``width``/``height`` are kept as explicit fields (useful for audit
    rendering — see ``render_text_content``) but they are NOT trusted: the
    provider processes ``data``'s BYTES, not this metadata, so
    :meth:`__post_init__` parses the CANONICAL dimensions from ``data`` itself
    (:func:`parse_image_dimensions`) and rejects any mismatch. Prefer
    :meth:`from_bytes`, which derives them for you instead of requiring the
    caller to get them right.
    """

    mime: str
    data: bytes
    width: int
    height: int

    @classmethod
    def from_bytes(cls, mime: str, data: bytes) -> ImagePart:
        """Preferred constructor: derive ``width``/``height`` from the encoded
        ``data`` instead of asking the caller to compute (and possibly get
        wrong, or lie about) them."""
        width, height = parse_image_dimensions(mime, data)
        return cls(mime=mime, data=data, width=width, height=height)

    def __post_init__(self) -> None:
        # Function-local: backends.base must not import model_selection at module scope.
        from llmxive.model_selection.tokens import (
            MAX_IMAGE_BYTES,
            MAX_IMAGE_DIMENSION_PX,
            MAX_IMAGE_PIXELS,
        )

        if self.mime not in _IMAGE_MIMES:
            raise ValueError(
                f"ImagePart: unsupported mime {self.mime!r} (allowed: {sorted(_IMAGE_MIMES)})"
            )
        if self.width <= 0 or self.height <= 0:
            raise ValueError("ImagePart: declared dimension must be positive")
        if not self.data:
            raise ValueError("ImagePart: empty image payload")
        if len(self.data) > MAX_IMAGE_BYTES:
            raise ValueError(
                f"ImagePart: {len(self.data)} bytes exceeds MAX_IMAGE_BYTES={MAX_IMAGE_BYTES}"
            )
        # CANONICAL dimensions come from the encoded bytes, never the caller's
        # claim — a caller could declare 1x1 for a 4000x4000 payload and this
        # is the ONLY check standing between that and an invalid cost bound.
        # This also catches a mime/content mismatch: each per-format parser
        # checks the format's own magic/signature bytes first.
        parsed_width, parsed_height = parse_image_dimensions(self.mime, self.data)
        if (parsed_width, parsed_height) != (self.width, self.height):
            raise ValueError(
                f"ImagePart: declared dimensions {self.width}x{self.height} do not match "
                f"the encoded {self.mime} data's actual dimensions "
                f"{parsed_width}x{parsed_height} — use ImagePart.from_bytes() instead of "
                "supplying width/height by hand"
            )
        if parsed_width > MAX_IMAGE_DIMENSION_PX or parsed_height > MAX_IMAGE_DIMENSION_PX:
            raise ValueError(
                f"ImagePart: dimension {parsed_width}x{parsed_height} exceeds the estimator's "
                f"supported maximum {MAX_IMAGE_DIMENSION_PX}px — downscale before selection "
                f"(the token upper bound is derived from it)"
            )
        if parsed_width * parsed_height > MAX_IMAGE_PIXELS:
            raise ValueError(
                f"ImagePart: {parsed_width}x{parsed_height} = "
                f"{parsed_width * parsed_height} pixels exceeds MAX_IMAGE_PIXELS="
                f"{MAX_IMAGE_PIXELS} — satisfying the per-side bound alone does not cap the "
                "decoded pixel count for every aspect ratio (e.g. a maximal square)"
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
    input_tokens: int | None = None  # provider-reported usage; None when not reported
    output_tokens: int | None = None


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


class PricingUnverifiable(TransientBackendError):
    """Cannot determine whether ``model`` is free or paid RIGHT NOW — the live
    pricing catalog is unreachable and there is no fresh last-known-good
    pricing observation to fall back on (or the model is served but not
    listed in an otherwise-reachable catalog).

    This is DELIBERATELY distinct from :class:`PaidGuardDenied`: that class
    means "this model VERIFIABLY costs money and the credit guard declined
    it" (a long-lived, cost-related fact). This class means "pricing is
    temporarily unknowable" (a transient AVAILABILITY condition) — it says
    nothing about cost and needs no opt-in/config change, only for the
    catalog (or a fresh LKG observation) to come back. Subclasses
    :class:`TransientBackendError` (NOT ``PermanentBackendError``) so
    ``router.disposition_of`` classifies it ``RETRY_ADVANCE`` — the walker
    tries the next candidate as an outage, not a permanent SKIP that implies
    "enable paid opt-in" — while :func:`llmxive.backends.dartmouth.is_free_model`
    still answers ``False`` for it (SC-003: an unverifiable model never
    proceeds as free)."""


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


#: The open circuit's wait grows to at most this many base cooldowns.
_MAX_COOLDOWN_FACTOR = 8
#: Default breaker thresholds, shared by every backend (Dartmouth applies env
#: overrides on top of these).
DEFAULT_BREAKER_MAX_CONSECUTIVE = 3
DEFAULT_BREAKER_WINDOW_S = 1800.0  # 30 min
DEFAULT_BREAKER_COOLDOWN_S = 900.0
_T = TypeVar("_T")


class CircuitBreaker:
    """Trips OPEN on a sustained outage so callers abort fast.

    Tracks consecutive fully-failed calls (a call that exhausted the backend's
    retries and raised :class:`TransientBackendError`) and the wall-clock time
    of the first failure in the current run of failures. Trips when EITHER:

      * ``max_consecutive`` consecutive full failures accumulate, OR
      * no success occurs within ``window_s`` of the first failure
        (a slow-drip outage that never quite reaches ``max_consecutive``),

    whichever comes first. When OPEN, :meth:`call` raises
    :class:`BackendUnavailable` immediately WITHOUT invoking the inner callable
    (so the retry budget is not burned). After a cooldown, allow one recovery
    probe while concurrent callers still fail fast. A failed probe restarts the
    cooldown; success resets the breaker. The cooldown doubles each time a real
    request is lost with no real answer in between (see ``_cooldown``). An explicit ModelDownError opens the
    circuit immediately because its full request budget has already been spent.

    Only :class:`TransientBackendError` counts as a failure — a
    :class:`PermanentBackendError` (e.g. the paid-model guard) is not an outage
    signal and passes straight through without advancing the breaker.

    ``clock`` is injectable for deterministic tests (defaults to
    ``time.monotonic``).
    """

    def __init__(
        self,
        *,
        max_consecutive: int = DEFAULT_BREAKER_MAX_CONSECUTIVE,
        window_s: float = DEFAULT_BREAKER_WINDOW_S,
        clock: Callable[[], float] = time.monotonic,
        cooldown_s: float = DEFAULT_BREAKER_COOLDOWN_S,
        liveness: Callable[[str], bool | None] | None = None,
        label: str = "Dartmouth",
    ) -> None:
        #: Backend name used in the open-circuit error message.
        self._label = label
        #: Optional cheap recovery check, called with :attr:`name` when the
        #: cooldown expires. ``True`` closes the circuit and the caller's real
        #: request proceeds with its FULL budget; ``False`` leaves it open and
        #: restarts the cooldown without burning a request; ``None`` means "no
        #: cheap check available" (a paid model, whose call must stay behind the
        #: credit guard) and falls back to probing with the real request. Left
        #: ``None`` by default, so a breaker constructed without it behaves
        #: exactly as before.
        self.liveness = liveness
        #: The resolved model this breaker guards; set by ``_breaker_for``.
        self.name = ""
        self._max_consecutive = max_consecutive
        self._window_s = window_s
        self._clock = clock
        self._cooldown_s = cooldown_s
        self._opened_at: float | None = None
        self._probe_in_flight = False
        self._lock = threading.Lock()
        self._consecutive_failures = 0
        self._first_failure_at: float | None = None
        #: Real requests lost since the last real answer. A model that answers
        #: the small liveness request and then hangs on the next real one would
        #: otherwise cost a full deadline every cooldown, for as long as the
        #: process runs; the wait doubles with each such loss instead.
        self._relapses = 0

    def _cooldown(self) -> float:
        """How long the circuit stays open now: the base cooldown, doubled for
        every real request lost since the last real answer, up to
        :data:`_MAX_COOLDOWN_FACTOR` times."""
        return self._cooldown_s * min(2 ** max(self._relapses - 1, 0), _MAX_COOLDOWN_FACTOR)

    def _is_open(self) -> bool:
        if self._opened_at is not None:
            return True
        if self._consecutive_failures >= self._max_consecutive:
            return True
        if (
            self._first_failure_at is not None
            and (self._clock() - self._first_failure_at) >= self._window_s
        ):
            return True
        return False

    def _open_error(self) -> BackendUnavailable:
        mins = self._window_s / 60.0
        return BackendUnavailable(
            f"circuit open: {self._label} endpoint persistently unavailable after "
            f"{self._consecutive_failures} consecutive failures / {mins:.0f} min"
        )

    def call(self, fn: Callable[[], _T]) -> _T:
        """Run ``fn()`` unless the breaker is OPEN (then raise immediately).

        Records a full failure on :class:`TransientBackendError`; resets on
        success. Other exceptions (PermanentBackendError, programming bugs)
        pass through unchanged and do NOT advance the breaker.
        """
        probe = False
        with self._lock:
            if self._is_open():
                now = self._clock()
                if self._opened_at is None:
                    self._opened_at = now
                if self._probe_in_flight or now - self._opened_at < self._cooldown():
                    raise self._open_error()
                self._probe_in_flight = probe = True
        if probe and self.liveness is not None:
            try:
                alive = self.liveness(self.name)
            except BaseException:  # a probe must never raise into the caller
                alive = False
            if alive is not None:
                with self._lock:
                    self._probe_in_flight = False
                    if not alive:
                        # Still sick. Restart the cooldown and fail fast, WITHOUT
                        # spending the caller's full request budget to find out.
                        self._opened_at = self._clock()
                        raise self._open_error()
                    self._reset()
                # The model answers: this is now an ordinary call, not a probe,
                # so it gets the full deadline and does not re-open the circuit
                # on a single transient failure.
                probe = False
        try:
            result = fn()
        except TransientBackendError as exc:
            with self._lock:
                self._record_failure()
                # A hard deadline / explicit model-down response has already
                # consumed a full request budget. Route around it immediately.
                if probe or isinstance(exc, ModelDownError) or self._is_open():
                    self._opened_at = self._clock()
                    self._relapses += 1
            raise
        except BaseException:
            # A failed/cancelled recovery probe must not leave the circuit stuck
            # half-open, nor cause all waiting callers to immediately retry it.
            if probe:
                with self._lock:
                    self._opened_at = self._clock()
            raise
        else:
            with self._lock:
                self._reset()
                self._relapses = 0  # a real answer, not a ping
            return result
        finally:
            if probe:
                with self._lock:
                    self._probe_in_flight = False

    def _record_failure(self) -> None:
        if self._first_failure_at is None:
            self._first_failure_at = self._clock()
        self._consecutive_failures += 1

    def _reset(self) -> None:
        self._opened_at = None
        self._consecutive_failures = 0
        self._first_failure_at = None


def openai_content(content: str | tuple[ContentPart, ...]) -> str | list[dict]:
    """Serialize canonical ChatMessage content for an OpenAI-compatible endpoint. A plain ``str``
    passes through unchanged (byte-identical payloads for every existing caller);
    a parts tuple becomes langchain's content-block list, which the
    OpenAI-compatible endpoint renders as the multimodal content array."""
    if isinstance(content, str):
        return content
    blocks: list[dict] = []
    for part in content:
        if isinstance(part, TextPart):
            blocks.append({"type": "text", "text": part.text})
        elif isinstance(part, ImagePart):
            import base64

            b64 = base64.b64encode(part.data).decode()
            blocks.append({
                "type": "image_url",
                "image_url": {"url": f"data:{part.mime};base64,{b64}"},
            })
        else:  # pragma: no cover - the union is closed
            raise PermanentBackendError(f"unknown content part {type(part).__name__}")
    return blocks


class BackendCredentialError(PermanentBackendError):
    """A backend's credential is missing or rejected (e.g. HTTP 401/403). The
    candidate cannot serve ANY request, but a peer backend may: the router SKIPs
    it instead of aborting the chain."""


__all__ = [
    "BackendCredentialError",
    "BackendError",
    "BackendUnavailable",
    "BaseBackend",
    "ChatMessage",
    "ChatResponse",
    "CircuitBreaker",
    "ContentPart",
    "DeadlineExceededError",
    "EmptyReplyError",
    "ImagePart",
    "ModelDownError",
    "PaidGuardDenied",
    "PermanentBackendError",
    "PricingUnverifiable",
    "TextPart",
    "TransientBackendError",
    "UnsupportedFeatureError",
    "invoke_with_deadline",
    "openai_content",
    "parse_image_dimensions",
    "render_text_content",
]
