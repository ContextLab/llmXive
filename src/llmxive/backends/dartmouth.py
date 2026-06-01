"""Dartmouth Chat backend via langchain-dartmouth (T020).

Uses ChatDartmouth(ChatOpenAI). Models are resolved at runtime via
ChatDartmouth.list() and CloudModelListing.list() per FR-022 — never
hardcoded.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from llmxive.backends.base import (
    BaseBackend,
    ChatMessage,
    ChatResponse,
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
            if attempt >= max_retries:
                break
            delay = min(
                base_delay_s * (_RETRY_MULTIPLIER ** attempt),
                _DEFAULT_RETRY_MAX_DELAY_S,
            )
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
# Includes models that are served-but-occasionally-unlisted (e.g. gemma-3).
KNOWN_FREE_MODELS: frozenset[str] = frozenset(
    {
        "qwen.qwen3.5-122b",
        "openai.gpt-oss-120b",
        "google.gemma-4-31B-it",
        "google.gemma-3-27b-it",
        "meta.llama-3-2-3b-instruct",
        "meta.llama-3.2-11b-vision-instruct",
        "qwen.qwen3-vl:32b",
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
    import requests  # type: ignore[import-untyped]  # no stubs; types-requests not installed

    resp = requests.get(
        _cloud_models_url(),
        headers={"Authorization": f"Bearer {key}"},
        timeout=30,
    )
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

        with _warnings.catch_warnings():
            _warnings.filterwarnings(
                "ignore", message=r".*Parameters \{'timeout'\}.*"
            )
            return ChatDartmouth(
                model_name=model, model_kwargs={"timeout": 180}
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

        # Free-only guard (Constitution Principle IV: v1 uses free backends,
        # cost_estimate_usd == 0). Dartmouth's catalog mixes free self-hosted
        # models with paid external providers (gpt-5, claude, gemini, ...);
        # calling a paid model would incur real cost the cost=0.0 invariant
        # hides. Refuse anything not confirmed free by the live pricing catalog
        # (or the KNOWN_FREE_MODELS fail-safe).
        if not is_free_model(model):
            raise PermanentBackendError(
                f"Dartmouth model {model!r} is not a free model "
                "(v1 forbids paid models — Constitution Principle IV); "
                "see chat.dartmouth.edu/api/models pricing"
            )

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
            # the call on a daemon thread and abandon it past 180s so the
            # router falls through to a peer model. See invoke_with_deadline's
            # docstring for why ThreadPoolExecutor would re-create the hang.
            return invoke_with_deadline(
                lambda: client.invoke(msg_objs, **call_kwargs),
                timeout=180.0,
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
                    if _is_transient_error_text(text):
                        raise TransientBackendError(str(exc)) from exc
                    raise PermanentBackendError(str(exc)) from exc

            text_out = str(reply.content)
            # Reasoning models (Qwen 3.5, gpt-oss) consume completion-budget
            # tokens on hidden <think> tokens that are stripped from
            # .content. Too-small max_tokens yields '' + finish_reason=
            # 'length' — treat as transient so the router can fall through
            # to a non-reasoning model.
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

        # Centralized retry — absorbs brief transient failures (Dartmouth
        # maintenance windows, vLLM cluster flickers, 5xx). Permanent
        # errors propagate immediately. See ``_retry_with_backoff``.
        return _retry_with_backoff(
            _do_one_attempt,
            max_retries=self._max_retries,
            base_delay_s=self._retry_base_delay_s,
            description=f"Dartmouth {model!r}",
        )

    def healthcheck(self) -> bool:
        try:
            self.list_models()
            return True
        except Exception:
            return False


__all__ = [
    "KNOWN_FREE_MODELS",
    "DartmouthBackend",
    "free_chat_models",
    "is_free_model",
]
