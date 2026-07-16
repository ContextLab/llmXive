"""Dartmouth Chat backend via langchain-dartmouth (T020).

Uses ChatDartmouth(ChatOpenAI). Models are resolved at runtime via
ChatDartmouth.list() and CloudModelListing.list() per FR-022 — never
hardcoded.
"""

from __future__ import annotations

import logging
import os
import random
import time
from collections.abc import Callable, Iterable
from typing import Any, NoReturn, TypeVar

from llmxive.backends.base import (
    BackendUnavailable,
    BaseBackend,
    ChatMessage,
    ChatResponse,
    EmptyReplyError,
    ModelDownError,
    PermanentBackendError,
    TransientBackendError,
    invoke_with_deadline,
)

# --- centralized transient-error retry (T015-class outages) --------------
#
# Dartmouth Chat occasionally goes into maintenance windows (the gateway
# starts responding with an HTML 302 redirect to outage.dartmouth.edu) or
# emits brief flickers (5xx / connection-reset / model-temporarily-
# unloaded). Without retries, a single such glitch fails the entire
# caller's call chain — calibration runs, panel-driven convergence, the
# pipeline cron, etc. all bail.
#
# Defaults: max_retries=8 + capped exponential backoff
# (5, 10, 20, 40, 60, 60, 60, 60 s) ≈ 5.25 min total wait. The Dartmouth Chat
# endpoint goes into maintenance (HTTP 302 → outage.dartmouth.edu) or hangs for
# a FEW MINUTES at a time and then comes back, so the retry window must SPAN
# those minutes — a 35 s window gave up far too soon and stranded every pipeline
# stage. The per-delay CAP (default 60 s) keeps the backoff from exploding and
# makes the client re-probe the endpoint at least once a minute, so recovery is
# detected promptly. Tunable per-instance (constructor kwargs) or via env vars:
#   DARTMOUTH_MAX_RETRIES        — int, default 8
#   DARTMOUTH_RETRY_BASE_S       — float seconds, default 5.0
#   DARTMOUTH_RETRY_MAX_DELAY_S  — float seconds, per-attempt cap, default 60.0
# A multi-minute outage is now ridden out silently; a genuinely long-running
# outage still surfaces as the final TransientBackendError after the retries
# exhaust (caller's own retry/fallback semantics unchanged — just far more
# resilient to the typical few-minute Dartmouth flap).

_DEFAULT_MAX_RETRIES = int(os.environ.get("DARTMOUTH_MAX_RETRIES", "8"))
_DEFAULT_RETRY_BASE_S = float(os.environ.get("DARTMOUTH_RETRY_BASE_S", "5.0"))
_DEFAULT_RETRY_MAX_DELAY_S = float(os.environ.get("DARTMOUTH_RETRY_MAX_DELAY_S", "60.0"))
_RETRY_MULTIPLIER = 2.0
# An EMPTY reply (the qwen <think>-mode flap) is a consistent model behavior, not a
# network blip: a couple of stochastic retries may recover, but burning the full
# 8-retry budget (~5 min) on a flapping model just delays the fall-through to a
# healthy peer / the fast paid fallback — the dominant reasoning-throughput cost.
# Cap it low so the router escapes quickly (still a few tries to catch a stochastic
# recovery). Overridable via DARTMOUTH_EMPTY_REPLY_MAX_RETRIES.
_EMPTY_REPLY_MAX_RETRIES = int(os.environ.get("DARTMOUTH_EMPTY_REPLY_MAX_RETRIES", "2"))

# --- reasoning-aware per-request wall-clock deadline ---------------------
#
# openai.gpt-oss-120b / gpt-oss are *reasoning* models: they spend completion-token
# budget on hidden <think> tokens before emitting any answer. A realistic
# full-spec (~7k-token) review prompt completes cleanly (finish=stop) in ~234s
# using ~9.7K completion tokens — but ONLY when given enough deadline. The old
# hard-coded 180s deadline abandoned such a call mid-reasoning, so reviewer /
# reviser stages on a reasoning model could NEVER complete (→ 7h zero-progress
# thrash: retried on the same model ~27 min/call). Give reasoning models a
# longer deadline (360s = measured 234s + margin); non-reasoning models (gemma,
# llama) answer immediately and keep the 180s default. Both env-overridable.
_DEFAULT_DEADLINE_S = float(os.environ.get("LLMXIVE_DARTMOUTH_DEADLINE_S", "180.0"))
_DEFAULT_REASONING_DEADLINE_S = float(
    os.environ.get("LLMXIVE_DARTMOUTH_REASONING_DEADLINE_S", "360.0")
)

# Substrings (matched case-insensitively against the model id) that mark a model
# as a REASONING model needing the longer deadline. Covers the qwen3.5 / qwen3
# and gpt-oss families served on Dartmouth's vLLM cluster.
_REASONING_MODELS: tuple[str, ...] = ("qwen3.5", "qwen3", "gpt-oss")


def _is_reasoning_model(model: str) -> bool:
    """True if *model* spends hidden completion-token budget on <think> tokens
    before answering (qwen3.5 / qwen3 / gpt-oss families)."""
    low = model.lower()
    return any(marker in low for marker in _REASONING_MODELS)


def _deadline_for_model(model: str) -> float:
    """Per-request wall-clock deadline (seconds) for *model*.

    Reasoning models get ``_DEFAULT_REASONING_DEADLINE_S`` (they reason before
    answering); everything else gets ``_DEFAULT_DEADLINE_S``. Used for BOTH the
    ``invoke_with_deadline`` timeout and the ``model_kwargs['timeout']`` so the
    two stay consistent.
    """
    if _is_reasoning_model(model):
        return _DEFAULT_REASONING_DEADLINE_S
    return _DEFAULT_DEADLINE_S


def _dartmouth_model_kwargs(model: str) -> dict[str, object]:
    """ChatDartmouth ``model_kwargs`` for *model*: a hard per-request timeout,
    plus thinking-OFF for Qwen3 reasoning models.

    Qwen3 (qwen3.5-122b) DEFAULTS to emitting hidden ``<think>`` tokens that
    consume the ENTIRE ``max_tokens`` budget before answering: every call takes
    30-50s, and when the budget is exhausted mid-reasoning the model returns ''
    (finish_reason='length'), which llmXive classifies as a transient empty reply
    and RETRIES — the empty-reply retry storms, the multi-minute per-call stalls,
    and the pipeline "throughput wall". Disabling thinking via the vLLM
    chat-template kwarg makes the SAME call ~0.9s with a direct answer (verified
    raw and via ChatDartmouth: 0.9s vs 38-50s), forwarded through ChatOpenAI's
    ``extra_body``. Opt back in per-process with ``LLMXIVE_QWEN_ENABLE_THINKING=1``
    for a stage that genuinely needs chain-of-thought. gpt-oss reasons far less and
    is left alone; non-reasoning peers (gemma/llama) ignore the kwarg.
    """
    kwargs: dict[str, object] = {"timeout": _deadline_for_model(model)}
    if "qwen" in model.lower() and os.environ.get("LLMXIVE_QWEN_ENABLE_THINKING") != "1":
        kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
    return kwargs


# --- circuit breaker (SUSTAINED-outage fast-abort) -----------------------
#
# The per-call retry/backoff above rides out SHORT flaps (minutes) — the user
# wants that. The circuit breaker is the SECOND line of defense: when the
# Dartmouth endpoint is PERSISTENTLY down, the breaker trips so the pipeline
# aborts FAST instead of thrashing for hours (observed: review/reviser calls
# retried 9x on a dead endpoint at ~27 min/call → 7h zero-progress). It is a
# NO-OP in normal operation: a single transient failure followed by a success
# never trips it. State is per-(DartmouthBackend instance, RESOLVED model): each
# model gets its OWN breaker so a single-model vLLM outage (e.g. qwen tripping)
# does NOT block a healthy peer (gpt-oss) on the same backend — which is exactly
# what lets the router's peer-model fallback route around a single down model.
# Both thresholds are constants, env-overridable.
_DEFAULT_BREAKER_MAX_CONSECUTIVE = int(
    os.environ.get("LLMXIVE_DARTMOUTH_BREAKER_MAX_CONSECUTIVE", "3")
)
_DEFAULT_BREAKER_WINDOW_S = float(
    os.environ.get("LLMXIVE_DARTMOUTH_BREAKER_WINDOW_S", "1800.0")  # 30 min
)


class _CircuitBreaker:
    """Trips OPEN on a sustained outage so callers abort fast.

    Tracks consecutive fully-failed calls (a call that exhausted the backend's
    retries and raised :class:`TransientBackendError`) and the wall-clock time
    of the first failure in the current run of failures. Trips when EITHER:

      * ``max_consecutive`` consecutive full failures accumulate, OR
      * no success occurs within ``window_s`` of the first failure
        (a slow-drip outage that never quite reaches ``max_consecutive``),

    whichever comes first. When OPEN, :meth:`call` raises
    :class:`BackendUnavailable` immediately WITHOUT invoking the inner callable
    (so the retry budget is not burned). ANY success resets the breaker fully.

    Only :class:`TransientBackendError` counts as a failure — a
    :class:`PermanentBackendError` (e.g. the paid-model guard) is not an outage
    signal and passes straight through without advancing the breaker.

    ``clock`` is injectable for deterministic tests (defaults to
    ``time.monotonic``).
    """

    def __init__(
        self,
        *,
        max_consecutive: int = _DEFAULT_BREAKER_MAX_CONSECUTIVE,
        window_s: float = _DEFAULT_BREAKER_WINDOW_S,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_consecutive = max_consecutive
        self._window_s = window_s
        self._clock = clock
        self._consecutive_failures = 0
        self._first_failure_at: float | None = None

    def _is_open(self) -> bool:
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
            f"circuit open: Dartmouth endpoint persistently unavailable after "
            f"{self._consecutive_failures} consecutive failures / {mins:.0f} min"
        )

    def call(self, fn: Callable[[], _T]) -> _T:
        """Run ``fn()`` unless the breaker is OPEN (then raise immediately).

        Records a full failure on :class:`TransientBackendError`; resets on
        success. Other exceptions (PermanentBackendError, programming bugs)
        pass through unchanged and do NOT advance the breaker.
        """
        if self._is_open():
            raise self._open_error()
        try:
            result = fn()
        except TransientBackendError:
            self._record_failure()
            raise
        # PermanentBackendError / unrelated exceptions: not an outage signal —
        # propagate without touching breaker state.
        self._reset()
        return result

    def _record_failure(self) -> None:
        if self._first_failure_at is None:
            self._first_failure_at = self._clock()
        self._consecutive_failures += 1

    def _reset(self) -> None:
        self._consecutive_failures = 0
        self._first_failure_at = None

_log = logging.getLogger(__name__)
_T = TypeVar("_T")


# Substrings (matched case-insensitively against the exception text) that mark a
# Dartmouth/vLLM failure as TRANSIENT — retried by _retry_with_backoff and, on
# exhaustion, surfaced so the router can fall through to another model. Anything
# not matched here is treated as a PermanentBackendError (no retry).
_TRANSIENT_ERROR_MARKERS: tuple[str, ...] = (
    "rate limit", "quota", "429", "timeout", "5xx",
    # Dartmouth's vLLM backend transients:
    "500", "502", "503", "504", "internal server error",
    "cannot connect to host", "connection reset", "connection refused",
    "service unavailable", "bad gateway", "gateway timeout",
    "internalservererror", "operation not permitted",
    "litellm.internalservererror",
    # A listed model can be transiently unloaded on the vLLM cluster.
    "not found", "no such model", "does not exist", "model_not_found",
    # Network-level transients:
    "temporary failure", "name resolution", "connection error",
    # HTTP 499: an upstream proxy/gateway closed the connection before the model
    # responded (Dartmouth returns this when the vLLM pod is slow to first-byte).
    # A textbook transient — retrying/falling through to a peer recovers it.
    # (engine-failure #505: was misclassified PermanentBackendError, crashing the
    # plan stage and filing a spurious engine-failure issue.)
    "client closed request", "499",
    # Connection dropped mid-stream while reading a large response (common when a
    # flaky endpoint streams a big planner/reviewer reply): requests
    # ChunkedEncodingError wrapping urllib3/http.client IncompleteRead, SSL EOF,
    # RemoteDisconnected, broken pipe, connection aborted.
    "connection broken", "incompleteread", "incomplete read",
    "chunkedencodingerror", "chunked encoding",
    "connection aborted", "broken pipe", "remotedisconnected",
    "remote end closed", "eof occurred",
    # Dartmouth maintenance redirect: 302 to outage.dartmouth.edu.
    "outage.dartmouth.edu", "moved temporarily", "302 moved", "<!doctype html",
)


def _is_transient_error_text(text: str) -> bool:
    """True if *text* (an exception's lowercased str) names a retryable
    Dartmouth/vLLM transient — see :data:`_TRANSIENT_ERROR_MARKERS`."""
    low = text.lower()
    return any(marker in low for marker in _TRANSIENT_ERROR_MARKERS)


# The gateway redirects to its maintenance page when THIS model's pod is down:
# an HTTP 302 → outage.dartmouth.edu. Unlike a generic fast flap, this is an
# unambiguous "model unavailable" signal — retrying the same model is futile, so
# it surfaces as a ModelDownError (fast-fail to a peer). Kept narrower than the
# transient set on purpose (a bare ``<!doctype html`` error page from some other
# cause stays a plain retryable transient).
_MODEL_DOWN_MARKERS = ("outage.dartmouth.edu", "302 moved", "moved temporarily")


def _is_model_down_text(text: str) -> bool:
    """True if *text* names the maintenance/outage redirect (model is DOWN)."""
    low = text.lower()
    return any(marker in low for marker in _MODEL_DOWN_MARKERS)


# Substrings that mark a Dartmouth failure as an AUTH rejection ("API key
# invalid!", a 401/403). These are DELIBERATELY kept out of _TRANSIENT_ERROR_MARKERS
# — an auth rejection is AMBIGUOUS: it can mean a genuinely bad/expired key (a real
# config error → fail fast + loud) OR a transient auth-service flap that spuriously
# rejects a VALID key (engine-failure #515-518: a ~2h Dartmouth flap on 2026-07-06).
# The two are disambiguated at classification time by _gateway_rejects_key (a live
# catalog-endpoint probe), NOT by substring — so _is_transient_error_text stays a
# pure, over-match-free function.
_AUTH_ERROR_MARKERS: tuple[str, ...] = (
    "api key invalid", "invalid api key", "unauthorized", "authentication",
    "401", "403", "not authenticated", "invalid_api_key", "authenticationerror",
    "invalid authentication", "incorrect api key",
)


def _is_auth_error_text(text: str) -> bool:
    """True if *text* (a lowercased exception str) names an auth/key rejection."""
    low = text.lower()
    return any(marker in low for marker in _AUTH_ERROR_MARKERS)


# Process-cached result of the key-validity preflight. True = the gateway
# DEFINITIVELY rejects the configured key (genuine bad/expired key). False/None =
# accepted or indeterminate ("cannot confirm the key is bad"). Only a definitive
# True is cached — an indeterminate probe (network/5xx/flap) is re-probed on the
# next auth error rather than being frozen into a wrong verdict.
_KEY_REJECTED_CACHE: bool | None = None


def _catalog_get(key: str, *, timeout: float = 30.0):  # type: ignore[no-untyped-def]
    """GET the Dartmouth chat catalog authenticated with *key*, returning the
    ``requests.Response`` (the caller inspects status / raises). THE single place
    the lazy ``requests`` import and the auth header live (Constitution I) — used
    by both the free-model catalog fetch and the key-validity preflight."""
    import requests  # type: ignore[import-untyped]  # no stubs; types-requests not installed

    return requests.get(
        _cloud_models_url(),
        headers={"Authorization": f"Bearer {key}"},
        timeout=timeout,
    )


def _gateway_rejects_key(*, force_refresh: bool = False) -> bool:
    """True ONLY if the Dartmouth chat catalog endpoint DEFINITIVELY rejects the
    configured key (HTTP 401/403) — i.e. the key is genuinely bad/expired.

    The catalog uses the SAME key + host as chat completions, so it is an exact
    proxy for "is this key accepted right now". Returns False on a 200 (accepted)
    OR on ANY indeterminate outcome (missing ``requests``, network error, 5xx,
    timeout, a flapping catalog): we only escalate an ``API key invalid!`` chat
    error to PERMANENT when we can CONFIRM the key itself is rejected. This keeps a
    transient auth-service flap (which spuriously 401s the chat path while the key
    is actually valid) from being misread as a permanent config error.

    Probes up to 3 times so a briefly-flapping catalog is not mistaken for a
    genuine rejection (a real bad key 401s consistently; a flap recovers).
    Definitive verdicts are cached for the process lifetime.
    """
    global _KEY_REJECTED_CACHE
    if _KEY_REJECTED_CACHE is not None and not force_refresh:
        return _KEY_REJECTED_CACHE
    try:
        _ensure_api_key_env()
        key = os.environ.get("DARTMOUTH_CHAT_API_KEY")
    except Exception:
        return False
    if not key:
        # No key configured at all: genuinely unusable (a real config error).
        _KEY_REJECTED_CACHE = True
        return True
    for attempt in range(3):
        try:
            resp = _catalog_get(key, timeout=15)
        except Exception:
            # Missing ``requests`` / network / timeout: indeterminate. Retry a
            # couple times, then give up as "cannot confirm bad" (False) — the
            # flap will clear next tick.
            continue
        status = resp.status_code
        if status in (401, 403):
            _KEY_REJECTED_CACHE = True
            return True
        if 200 <= status < 400:
            _KEY_REJECTED_CACHE = False
            return False
        # 5xx / 429 / other: the gateway is flapping, not rejecting the key.
        # Retry a couple times before concluding "cannot confirm bad".
        if attempt < 2:
            time.sleep(1.0)
    return False


def _raise_for_backend_error(text: str, exc: BaseException) -> NoReturn:
    """Classify a raw Dartmouth/vLLM exception and raise the typed BackendError.

    THE single classification chokepoint (Constitution I) — every chat-path
    failure routes through here so the transient/model-down/auth/permanent
    precedence is defined in exactly one place:

    * maintenance/outage redirect → :class:`ModelDownError` (fast-fail to a peer)
    * a listed transient marker    → :class:`TransientBackendError` (retry)
    * an AUTH rejection whose key the catalog still ACCEPTS (or cannot be
      confirmed bad) → :class:`TransientBackendError` — a transient auth-service
      flap (engine-failure #515-518), NOT a config error. A genuinely bad key is
      rejected by the catalog too (_gateway_rejects_key → True) and falls through
      to PERMANENT below, surfacing a loud, actionable engine-failure issue.
    * anything else                → :class:`PermanentBackendError` (no retry)
    """
    if _is_model_down_text(text):
        raise ModelDownError(str(exc)) from exc
    if _is_transient_error_text(text):
        raise TransientBackendError(str(exc)) from exc
    if _is_auth_error_text(text) and not _gateway_rejects_key():
        raise TransientBackendError(str(exc)) from exc
    raise PermanentBackendError(str(exc)) from exc


def _retry_with_backoff(
    fn: Callable[[], _T],
    *,
    max_retries: int,
    base_delay_s: float,
    description: str = "Dartmouth call",
) -> _T:
    """Call ``fn()``; on :class:`TransientBackendError`, retry with
    exponential backoff (capped per-attempt at ``_DEFAULT_RETRY_MAX_DELAY_S``)
    up to ``max_retries`` times. Permanent errors propagate immediately (no
    point retrying them). Total wait at defaults: 5+10+20+40+60+60+60+60 ≈
    5.25 min — long enough to ride out a typical few-minute Dartmouth flap.

    The last transient exception is re-raised when retries exhaust, so
    the caller's existing TransientBackendError handling still triggers
    on real outages — this just absorbs brief flickers transparently.
    """
    last_exc: TransientBackendError | None = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except TransientBackendError as exc:
            last_exc = exc
            # A ModelDownError means THIS model is unavailable (hung past its full
            # deadline, or a 302→outage maintenance redirect): retrying it on the
            # SAME model is futile and expensive (a deadline hang costs another
            # full deadline; an outage will recur). Fail fast (no inner retry) so
            # the model-fallback chain escapes to a healthy peer. Ordinary fast
            # flaps (generic 5xx/reset) are NOT ModelDownError and keep the
            # generous retry budget below.
            if isinstance(exc, ModelDownError):
                break
            # An empty reply is a consistent model behavior — cap its retries LOW so
            # the router falls through to a healthy peer / the fast paid fallback
            # quickly instead of burning the full budget on a flapping model.
            if isinstance(exc, EmptyReplyError) and attempt >= _EMPTY_REPLY_MAX_RETRIES:
                break
            if attempt >= max_retries:
                break
            computed = min(
                base_delay_s * (_RETRY_MULTIPLIER ** attempt),
                _DEFAULT_RETRY_MAX_DELAY_S,
            )
            # Equal jitter: delay = half + uniform(0, half), half = computed/2,
            # so delay ∈ [computed/2, computed]. Many lens calls retry in
            # parallel; without jitter their identical backoff schedules
            # re-synchronize into waves that hammer a just-recovering pod. The
            # jitter de-correlates them while keeping the per-attempt cap intact.
            half = computed / 2.0
            delay = half + random.uniform(0.0, half)
            _log.warning(
                "%s transient error (attempt %d/%d): %s; sleeping %.1fs",
                description, attempt + 1, max_retries + 1, exc, delay,
            )
            time.sleep(delay)
    # All retries exhausted — surface the final transient so the caller's
    # router can fall through to a peer model.
    assert last_exc is not None  # for mypy: loop exit implies last_exc was set
    raise last_exc


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


# Fail-safe set of FREE Dartmouth chat models (input/output cost-per-token
# == 0 per chat.dartmouth.edu/api/models). Used only when the live catalog
# is unreachable, so a transient listing outage never blocks a known-free
# model. The live catalog (free_chat_models) is authoritative when available.
# Synced 2026-06 with ChatDartmouth.list(): the qwen.* and google.gemma-*
# families were RETIRED from the Dartmouth catalog, so every agent that named
# them silently fell through to the weak `local` fallback. The only capable
# Free capable models on the Dartmouth catalog (verified live 2026-06-25 by real
# call — all responding): qwen3.5-122b (reasoning) is the primary default, gemma
# (fast, non-reasoning) and gpt-oss-120b (reasoning) are fallbacks. qwen + gemma
# were transiently retired/down 2026-06 (why the registry had moved to gpt-oss)
# and are back. llama / codellama stay free but small (last resort). Paid models
# (claude/gpt-5/gemini/voyage) are NEVER listed here — they route through
# PAID_FALLBACK_MODELS + the daily credit guard.
KNOWN_FREE_MODELS: frozenset[str] = frozenset(
    {
        "qwen.qwen3.5-122b",
        "google.gemma-3-27b-it",
        "google.gemma-4-31B-it",
        "openai.gpt-oss-120b",
        "meta.llama-3.2-11b-vision-instruct",
        "meta.llama-3-2-3b-instruct",
        "meta.codellama-13b-instruct-hf",
    }
)

_FREE_MODELS_CACHE: frozenset[str] | None = None


def _cloud_models_url() -> str:
    """The OpenAI-compatible model catalog endpoint for Dartmouth Chat.

    Derived from langchain-dartmouth's CLOUD_BASE_URL (overridable via the
    LCD_CLOUD_BASE_URL env var), the same host+key used for chat completions.
    """
    try:
        from langchain_dartmouth.definitions import CLOUD_BASE_URL

        base = CLOUD_BASE_URL
    except Exception:
        base = os.environ.get("LCD_CLOUD_BASE_URL", "https://chat.dartmouth.edu/api/")
    return base.rstrip("/") + "/models"


def _fetch_cloud_models() -> list[dict[str, Any]]:
    """Fetch the raw model catalog (with per-model pricing) from Dartmouth Chat.

    We query chat.dartmouth.edu/api/models directly rather than via
    ChatDartmouth.list(): that helper targets a *different* Dartmouth API
    host (api.dartmouth.edu) which rejects the chat key and returns
    non-JSON. The chat catalog authenticates with the same key as chat
    completions and exposes input/output cost-per-token under model_info.
    """
    _ensure_api_key_env()
    key = os.environ.get("DARTMOUTH_CHAT_API_KEY")
    if not key:
        raise PermanentBackendError(
            "DARTMOUTH_CHAT_API_KEY is not set (required by Dartmouth backend)"
        )
    resp = _catalog_get(key, timeout=30)
    resp.raise_for_status()
    return list((resp.json() or {}).get("data") or [])


def _model_token_costs(model_obj: dict[str, Any]) -> tuple[float | None, float | None]:
    """Return (input_cost_per_token, output_cost_per_token) for a catalog entry.

    The catalog nests pricing at different depths (internal models under
    upstream_model_info.model_info; external/paid models one level deeper),
    so we search recursively. Returns (None, None) when no pricing is present
    (embeddings/helper bots), which we deliberately do NOT treat as free.
    """
    ins: list[float] = []
    outs: list[float] = []

    def walk(o: object) -> None:
        if isinstance(o, dict):
            v = o.get("input_cost_per_token")
            if v is not None:
                ins.append(float(v))
            v = o.get("output_cost_per_token")
            if v is not None:
                outs.append(float(v))
            for val in o.values():
                walk(val)
        elif isinstance(o, list):
            for val in o:
                walk(val)

    walk(model_obj)
    return (max(ins) if ins else None, max(outs) if outs else None)


def free_chat_models(*, force_refresh: bool = False) -> frozenset[str] | None:
    """Set of Dartmouth model ids that are free (cost-per-token == 0).

    Authoritative source: the live chat catalog's explicit per-model pricing.
    Returns ``None`` when the catalog is unreachable so callers fall back to
    KNOWN_FREE_MODELS. Cached for the process lifetime.
    """
    global _FREE_MODELS_CACHE
    if _FREE_MODELS_CACHE is not None and not force_refresh:
        return _FREE_MODELS_CACHE
    try:
        models = _fetch_cloud_models()
    except Exception:
        return None
    free: set[str] = set()
    for m in models:
        mid = m.get("id")
        if not mid:
            continue
        in_cost, out_cost = _model_token_costs(m)
        if in_cost == 0 and out_cost == 0:
            free.add(str(mid))
    _FREE_MODELS_CACHE = frozenset(free)
    return _FREE_MODELS_CACHE


_MODEL_COSTS_CACHE: dict[str, tuple[float | None, float | None]] = {}


def model_token_costs(model: str) -> tuple[float | None, float | None]:
    """Catalog ``(input, output)`` USD cost-per-token for ``model``.

    Process-cached. Returns ``(None, None)`` when the catalog is
    unreachable or the model is unlisted — callers treat that as
    "cost unknown" (never as free).
    """
    if model in _MODEL_COSTS_CACHE:
        return _MODEL_COSTS_CACHE[model]
    try:
        for m in _fetch_cloud_models():
            mid = str(m.get("id") or "")
            if mid:
                _MODEL_COSTS_CACHE[mid] = _model_token_costs(m)
    except Exception:
        return (None, None)
    return _MODEL_COSTS_CACHE.get(model, (None, None))


def is_free_model(model: str) -> bool:
    """Whether ``model`` is a free Dartmouth chat model (cost-per-token == 0).

    Prefers the live catalog; on catalog outage (or for served-but-unlisted
    models) falls back to the static KNOWN_FREE_MODELS allowlist so a
    transient listing failure never blocks a known-free model.
    """
    live = free_chat_models()
    if live is not None and model in live:
        return True
    return model in KNOWN_FREE_MODELS


class DartmouthBackend(BaseBackend):
    name = "dartmouth"
    is_paid = False

    def __init__(
        self,
        *,
        model_name: str | None = None,
        max_retries: int | None = None,
        retry_base_delay_s: float | None = None,
    ) -> None:
        _ensure_api_key_env()
        if not os.environ.get("DARTMOUTH_CHAT_API_KEY"):
            raise PermanentBackendError(
                "DARTMOUTH_CHAT_API_KEY is not set (required by Dartmouth backend)"
            )
        self._model_name = model_name
        # Retry config — falls back to module defaults (env-overridable);
        # see ``_retry_with_backoff`` docstring for what gets retried.
        self._max_retries = (
            _DEFAULT_MAX_RETRIES if max_retries is None else max_retries
        )
        self._retry_base_delay_s = (
            _DEFAULT_RETRY_BASE_S
            if retry_base_delay_s is None
            else retry_base_delay_s
        )
        # Per-MODEL circuit breakers: each resolved model name gets its OWN
        # breaker (lazily created via ``_new_breaker``), so a SUSTAINED outage on
        # one model (e.g. qwen) trips ONLY that model's breaker and can't block a
        # healthy peer (gpt-oss) on the same backend instance. This is what lets
        # the router walk to a healthy peer when one model is down. No-op in
        # normal operation (single transient + success never trips). See
        # _CircuitBreaker.
        self._breakers: dict[str, _CircuitBreaker] = {}

    def _new_breaker(self) -> _CircuitBreaker:
        """Factory for a fresh per-model breaker (overridable in tests)."""
        return _CircuitBreaker()

    def _breaker_for(self, model: str) -> _CircuitBreaker:
        """The circuit breaker guarding ``model`` on this backend (lazy-created).

        Keyed by the resolved model name so each model's outage state is
        isolated — qwen tripping OPEN never short-circuits gpt-oss."""
        br = self._breakers.get(model)
        if br is None:
            br = self._new_breaker()
            self._breakers[model] = br
        return br

    def _client(self, model: str):  # type: ignore[no-untyped-def]
        try:
            from langchain_dartmouth.llms import ChatDartmouth
        except ImportError as exc:
            raise PermanentBackendError(
                "langchain-dartmouth is not installed; pip install -e ."
            ) from exc
        # 3 min per-request timeout. The router can retry the same
        # model 3x and walk through 3 fallback models, so worst-case
        # per-stage delay is bounded at 6x3=18 min instead of 6x10=60.
        # Healthy 32K-token completions on Dartmouth's vLLM cluster
        # finish in 30s-2min; anything past 3 min is a sick connection
        # we want to abandon and try a peer model on.
        # ChatDartmouth.__init__ doesn't expose `timeout` directly but
        # accepts it via model_kwargs (forwarded to underlying
        # ChatOpenAI which DOES have a timeout field). Suppress the
        # noisy "should be specified explicitly" warning since this
        # is the intended escape hatch.
        import warnings as _warnings

        model_kwargs = _dartmouth_model_kwargs(model)
        with _warnings.catch_warnings():
            _warnings.filterwarnings(
                "ignore",
                message=r".*Parameters \{[^}]*\} should be specified explicitly.*",
            )
            return ChatDartmouth(
                model_name=model,
                model_kwargs=model_kwargs,
            )

    def list_models(self) -> list[str]:
        # Query the OpenAI-compatible chat catalog directly. ChatDartmouth.list()
        # targets a different Dartmouth API host that rejects the chat key and
        # returns non-JSON; the chat catalog uses the same key as completions.
        try:
            models = _fetch_cloud_models()
        except PermanentBackendError:
            raise
        except Exception as exc:  # pragma: no cover — surfaced in preflight
            raise TransientBackendError(f"Dartmouth list_models failed: {exc}") from exc
        return [str(m["id"]) for m in models if m.get("id")]

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

        # Free-first guard (Constitution Principle IV). Dartmouth's catalog
        # mixes free self-hosted models with paid external providers (gpt-5,
        # claude, gemini, ...). Paid models are refused UNLESS the
        # credit-managed opt-in path approves the call: the process-level
        # LLMXIVE_PAID_OPT_IN master switch must be on AND the live daily
        # credit budget must have headroom (issue #295: 2000 credits/day =
        # ~$2.00 list-price equivalent, renewing daily — costing the project
        # $0 in actual money when managed within budget). The guard FAILS
        # CLOSED (balance unreachable -> refuse). See backends/credits.py.
        paid_call = not is_free_model(model)
        if paid_call:
            from llmxive.backends.credits import paid_call_allowed

            allowed, reason = paid_call_allowed(model)
            if not allowed:
                raise PermanentBackendError(f"Dartmouth: {reason}")
            _log.info("dartmouth: %s", reason)

        client = self._client(model)
        from langchain_core.messages import BaseMessage as _BaseMessage
        msg_objs: list[_BaseMessage] = []
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

        def _invoke(call_kwargs: dict[str, object]):  # type: ignore[no-untyped-def]
            # Hard-enforce a per-request wall-clock deadline. ChatDartmouth's
            # nominal `timeout` model_kwarg is forwarded as a chat-completion
            # body param, NOT as an HTTP/socket timeout, so a sick connection
            # can block indefinitely (observed in CI as a ~54-min hang). Run
            # the call on a daemon thread and abandon it past the deadline so
            # the router falls through to a peer model. The deadline is
            # reasoning-aware (longer for qwen3.5/gpt-oss, which reason before
            # answering) and matches the client's model_kwargs['timeout']. See
            # invoke_with_deadline's docstring for why ThreadPoolExecutor would
            # re-create the hang.
            return invoke_with_deadline(
                lambda: client.invoke(msg_objs, **call_kwargs),
                timeout=_deadline_for_model(model),
                description=f"Dartmouth model {model!r}",
            )

        def _do_one_attempt() -> ChatResponse:
            """One end-to-end attempt: invoke + classify + parse the reply.
            Raises :class:`TransientBackendError` on retryable failures (the
            outer :func:`_retry_with_backoff` absorbs brief ones); raises
            :class:`PermanentBackendError` on hard failures (no retry).
            ``kwargs`` is captured from the enclosing scope and may be
            mutated by the temperature-drop fallback; that's intentional
            so subsequent outer-loop attempts don't keep re-sending a
            known-rejected parameter."""
            try:
                reply = _invoke(kwargs)
            except TransientBackendError:
                raise
            except Exception as exc:
                text = str(exc).lower()
                # Some models (e.g. the gpt-5 family) reject any
                # temperature != 1. Drop it and retry once
                # (litellm drop_params behavior).
                if (
                    "temperature" in kwargs
                    and "temperature" in text
                    and ("unsupported" in text or "only temperature" in text or "support" in text)
                ):
                    retry_kwargs = {k: v for k, v in kwargs.items() if k != "temperature"}
                    try:
                        reply = _invoke(retry_kwargs)
                    except TransientBackendError:
                        raise
                    except Exception as exc2:
                        exc = exc2
                        text = str(exc2).lower()
                    else:
                        exc = None  # type: ignore[assignment]
                if exc is not None:
                    # Single classification chokepoint: model-down → transient →
                    # auth-flap-vs-genuine-bad-key → permanent (see
                    # _raise_for_backend_error).
                    _raise_for_backend_error(text, exc)

            text_out = str(reply.content)
            # Reasoning models (Qwen 3.5, gpt-oss) consume completion-budget
            # tokens on hidden <think> tokens that are stripped from
            # .content. Too-small max_tokens yields '' + finish_reason=
            # 'length' — treat as transient so the router can fall through
            # to a non-reasoning model.
            meta = getattr(reply, "response_metadata", {}) or {}
            finish_reason = meta.get("finish_reason")
            if not text_out.strip():
                reply_kwargs = getattr(reply, "additional_kwargs", {}) or {}
                refusal = reply_kwargs.get("refusal")
                if refusal:
                    # A genuine content-filter refusal — the model WON'T produce
                    # this no matter how often we ask. Skip to the next peer.
                    raise PermanentBackendError(
                        f"Dartmouth model {model!r} refused (refusal={refusal!r}, "
                        f"finish_reason={finish_reason!r})"
                    )
                # Empty content WITHOUT a refusal — `length` (reasoning budget
                # exhausted) OR `stop`/None (a transient hiccup where the model
                # returned nothing despite stopping normally). Both are TRANSIENT:
                # retry / fall through to a PEER model. Previously a `stop`+empty
                # reply was misclassified PERMANENT, abandoning the whole dartmouth
                # backend and failing the step (observed live on PROJ-018's
                # clarifier: gpt-oss-120b returned '' + finish_reason='stop',
                # refusal=None → the step died instead of retrying a peer).
                usage = meta.get("token_usage", {}) or {}
                raise EmptyReplyError(
                    f"Dartmouth model {model!r} returned empty content "
                    f"(finish_reason={finish_reason!r}, "
                    f"completion_tokens={usage.get('completion_tokens')}) "
                    "— transient empty reply; retry / fall through to a peer model"
                )

            # Free models cost 0.0; an opted-in paid call reports its real
            # list-price estimate from the catalog pricing x token usage so
            # run logs account honestly for credit consumption (#295).
            cost_estimate = 0.0
            if paid_call:
                usage = meta.get("token_usage", {}) or {}
                in_cost, out_cost = model_token_costs(model)
                cost_estimate = (
                    float(usage.get("prompt_tokens") or 0) * (in_cost or 0.0)
                    + float(usage.get("completion_tokens") or 0) * (out_cost or 0.0)
                )

            return ChatResponse(
                text=text_out,
                model=model,
                backend=self.name,
                cost_estimate_usd=cost_estimate,
            )

        # Centralized retry — absorbs brief transient failures (Dartmouth
        # maintenance windows, vLLM cluster flickers, 5xx). Permanent
        # errors propagate immediately. See ``_retry_with_backoff``.
        #
        # The retry is wrapped by THIS MODEL's circuit breaker: if the model's
        # breaker is already OPEN (sustained outage of that specific model) it
        # raises BackendUnavailable here WITHOUT burning the retry budget;
        # otherwise a fully-exhausted retry (final TransientBackendError) counts
        # toward tripping it, and any success resets it. Keyed per resolved model
        # so qwen's outage never blocks a healthy gpt-oss peer. See
        # ``_CircuitBreaker`` / ``_breaker_for``.
        return self._breaker_for(model).call(
            lambda: _retry_with_backoff(
                _do_one_attempt,
                max_retries=self._max_retries,
                base_delay_s=self._retry_base_delay_s,
                description=f"Dartmouth {model!r}",
            )
        )

    def healthcheck(self) -> bool:
        try:
            self.list_models()
            return True
        except Exception:
            return False


__all__ = [
    "KNOWN_FREE_MODELS",
    "BackendUnavailable",
    "DartmouthBackend",
    "free_chat_models",
    "is_free_model",
    "model_token_costs",
]
