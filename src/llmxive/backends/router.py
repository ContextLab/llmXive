"""Backend router (T020) — falls back through a chain on transient errors.

The agent registry declares a default backend and an ordered list of
fallback backends per agent. The router is configured per-call from
those declarations.
"""

from __future__ import annotations

from collections.abc import Iterable

from llmxive.backends.base import (
    BackendError,
    BackendUnavailable,
    BaseBackend,
    ChatMessage,
    ChatResponse,
    ModelDownError,
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.dartmouth import DartmouthBackend
from llmxive.backends.local import LocalBackend

_REGISTRY: dict[str, type[BaseBackend]] = {
    "dartmouth": DartmouthBackend,
    "local": LocalBackend,
}


def make_backend(name: str) -> BaseBackend:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise PermanentBackendError(f"unknown backend: {name!r}")
    return cls()


# Per-backend model-fallback chain. When the primary model on a
# backend hits transient errors after retries, try these models in
# order before falling through to the next backend. This keeps
# pipeline runs alive when one Dartmouth-hosted model has a vLLM
# outage but other models on the same backend are healthy.
MODEL_FALLBACKS: dict[str, list[str]] = {
    # qwen3.5-122b is the primary free reasoning model (maintainer default). The
    # Dartmouth free models flap on a multi-day cycle, so when the primary's vLLM
    # flaps the router walks the SAME-backend peers in order before falling through
    # to the next backend, keeping runs alive. Free peers first, then the guarded
    # paid model last:
    #   1. gemma-3-27b — free, FAST, non-reasoning (degrades a qwen flap to a
    #      sub-second model instead of a 360s deadline wait).
    #   2. gpt-oss-120b — free, capable reasoning (often up; flaps).
    #   3. claude-haiku-4.5 — a CAPABLE *paid* last resort (~29 credits ≈ $0.029).
    #      GUARDED: dartmouth.chat() raises PermanentBackendError unless
    #      LLMXIVE_PAID_OPT_IN is set AND the daily credit budget has headroom;
    #      the router treats that peer-permanent as "skip to next peer", so with
    #      opt-in OFF this entry is a silent no-op.
    "qwen.qwen3.5-122b": [
        "google.gemma-3-27b-it",
        "openai.gpt-oss-120b",
        "anthropic.claude-haiku-4-5-20251001",
    ],
    # gpt-oss as primary (a few modules still pin it) degrades the same way.
    "openai.gpt-oss-120b": [
        "qwen.qwen3.5-122b",
        "google.gemma-3-27b-it",
        "anthropic.claude-haiku-4-5-20251001",
    ],
    # gemma as primary (fast default for cheap calls) → reasoning peers → paid.
    "google.gemma-3-27b-it": [
        "qwen.qwen3.5-122b",
        "openai.gpt-oss-120b",
        "anthropic.claude-haiku-4-5-20251001",
    ],
}

#: The maintainer-default model — what a caller that does NOT pin one should use.
#:
#: A REAL backend requires a model (``DartmouthBackend.chat`` takes ``model`` as a
#: REQUIRED keyword-only arg), so ``model=None`` is viable ONLY for the injected
#: fake backends whose narrower signatures ``_chat_degrading`` degrades toward.
#: Against Dartmouth a ``model=None`` call dies with ``TypeError: chat() missing 1
#: required keyword-only argument: 'model'``. Public entry points that build live,
#: real-backend units must therefore default to THIS rather than to ``None``.
DEFAULT_MODEL: str = "qwen.qwen3.5-122b"

#: Sanctioned PAID models permitted in MODEL_FALLBACKS as guarded fallbacks
#: (Constitution IV stays satisfied: each is gated by the paid opt-in + daily
#: credit-budget guard in ``backends/credits.py``, so it costs $0 and is off by
#: default). Distinct from KNOWN_FREE_MODELS, which are unconditionally free.
PAID_FALLBACK_MODELS: frozenset[str] = frozenset({"anthropic.claude-haiku-4-5-20251001"})

# ---------------------------------------------------------------------------
# Reasoning-safe token budgets — the SINGLE source of truth (was duplicated as
# ``_REASONING_MAX_TOKENS`` in 8 modules). qwen3.5-122b et al. are reasoning
# models whose hidden chain-of-thought counts against ``max_tokens``.
#   REASONING_MAX_TOKENS  — analysis/extraction/review calls: short structured
#       outputs (claims, values, entailment verdicts). 32K is ample and avoids
#       the reasoning-budget-exhaustion hang (the same bound the reviewer/reviser
#       already use).
#   GENERATION_MAX_TOKENS — calls that emit LARGE artifacts (the planner's
#       corrective re-call must emit five files). Matches chat_with_fallback's
#       default below.
# ---------------------------------------------------------------------------
REASONING_MAX_TOKENS = 32_768
GENERATION_MAX_TOKENS = 131_072


def _chat_one_model(
    backend: BaseBackend,
    msg_list: list[ChatMessage],
    *,
    model: str | None,
    max_tokens: int | None,
    temperature: float | None,
) -> ChatResponse:
    """``backend.chat`` for ONE model, degrading for fakes/legacy signatures.

    Production backends (Dartmouth/local) accept the full
    ``model/max_tokens/temperature`` kwarg set. In-test fake backends and
    legacy doubles often expose a narrower ``chat(messages, model=None)``
    signature; calling them with ``max_tokens``/``temperature`` raises
    ``TypeError``. We degrade progressively — drop ``temperature``, then
    ``max_tokens``, then ``model`` — so the SAME helper drives both the real
    peer-model fallback chain AND the injected-fake reviewer/reviser tests.

    ``model=None`` is honored (omitted from the call) so callers that don't pin
    a model still work. This NEVER catches backend errors — Transient/Permanent
    propagate to the chain walker; only ``TypeError`` (signature mismatch) is
    handled here.
    """
    base: dict[str, object] = {}
    if model is not None:
        base["model"] = model
    attempts: list[dict[str, object]] = []
    full = dict(base)
    if max_tokens is not None:
        full["max_tokens"] = max_tokens
    if temperature is not None:
        full["temperature"] = temperature
    attempts.append(full)
    # Degrade temperature first (keep the load-bearing reasoning budget longest),
    # then max_tokens, then a bare model-only / no-kwarg call.
    if temperature is not None and ("max_tokens" in full):
        attempts.append({**base, "max_tokens": max_tokens})
    attempts.append(dict(base))
    if base:
        attempts.append({})
    last_type_error: TypeError | None = None
    for kwargs in attempts:
        try:
            return backend.chat(msg_list, **kwargs)  # type: ignore[arg-type]
        except TypeError as exc:
            last_type_error = exc
            continue
    assert last_type_error is not None
    raise last_type_error


def chat_with_model_fallback(
    backend: BaseBackend,
    messages: Iterable[ChatMessage],
    *,
    model: str | None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> ChatResponse:
    """Peer-model fallback on a SINGLE, already-constructed backend instance.

    Tries ``model`` (3 retries) then each peer in ``MODEL_FALLBACKS[model]`` (1
    attempt each) on the GIVEN backend — the same SAME-BACKEND peer-model walk
    :func:`chat_with_fallback` performs per backend, but operating on an
    injected backend instance instead of constructing one by name. This is what
    the convergence panel + reviser use so a transient outage on the primary
    model (e.g. a qwen3.5-122b vLLM hang) walks to gpt-oss-120b / gemma without
    swapping the backend object the caller already holds.

    The same reasoning-safe ``max_tokens`` is passed to EVERY model in the
    chain (the peers are also reasoning models and need the budget). A
    ``reasoning budget exhausted`` transient skips the remaining same-model
    retries (the model will exhaust it again) and falls straight to the peer.

    A ``BackendUnavailable`` (the model's circuit breaker is OPEN / the model is
    down) on ANY model in the chain — INCLUDING the primary — records it and
    walks to the next peer (the model is down; try the next). It does NOT abort:
    that is the fix for the per-model breaker composing with fallback. A
    NON-Unavailable ``PermanentBackendError`` on the primary (paid-model guard, a
    hard refusal) still aborts immediately (no peer walk). When the whole chain
    is exhausted, if ANY failure was ``BackendUnavailable`` OR transient-class
    (``ModelDownError`` / ``TransientBackendError``) we raise
    ``BackendUnavailable`` (a true full-endpoint outage → the run loop's existing
    clean-abort path fires with state preserved — NEVER a human escalation);
    only an all-permanent exhaustion raises the aggregate ``BackendError``. On a
    ``model=None`` call there is no chain to walk — it is a single
    signature-degrading ``chat`` (the contract the injected-fake backends rely on;
    callers talking to a REAL backend must pin a model — see
    :data:`DEFAULT_MODEL`).
    """
    import time as _time

    msg_list = list(messages)
    if model is None:
        return _chat_one_model(
            backend, msg_list, model=None,
            max_tokens=max_tokens, temperature=temperature,
        )
    models_to_try = [model] + [m for m in MODEL_FALLBACKS.get(model, []) if m != model]
    errors: list[str] = []
    saw_unavailable = False
    saw_transient = False
    for model_idx, m in enumerate(models_to_try):
        attempts = 3 if model_idx == 0 else 1
        for attempt in range(attempts):
            if attempt:
                _time.sleep(2.0 * attempt)
            try:
                return _chat_one_model(
                    backend, msg_list, model=m,
                    max_tokens=max_tokens, temperature=temperature,
                )
            except BackendUnavailable as exc:
                # The MODEL is down (breaker OPEN). Retrying the same model is
                # pointless (it will fast-fail), so skip the remaining same-model
                # attempts and walk to the next peer — do NOT abort, even on the
                # primary. A genuinely all-down chain still aborts below (via
                # BackendUnavailable), preserving the breaker's anti-thrash role.
                saw_unavailable = True
                errors.append(f"{m}(unavailable): {exc}")
                break
            except ModelDownError as exc:
                # THIS model is down (hung past its full deadline, or a 302→outage
                # maintenance redirect) — not flickering. Retrying the SAME model
                # burns another full deadline / will just re-redirect; skip the
                # remaining same-model attempts and fall straight to the next peer.
                saw_transient = True
                errors.append(f"{m}(model-down attempt {attempt + 1}): {exc}")
                break
            except TransientBackendError as exc:
                saw_transient = True
                errors.append(f"{m}(transient attempt {attempt + 1}): {exc}")
                if "reasoning budget exhausted" in str(exc):
                    break
                if attempt == attempts - 1:
                    break
                continue
            except PermanentBackendError as exc:
                # A genuine permanent rejection (paid-model guard / hard refusal)
                # — NOT a model-down signal. On the primary this won't heal by
                # walking peers, so abort. On a peer, end this model's attempts.
                errors.append(f"{m}(permanent): {exc}")
                if model_idx == 0:
                    raise
                break
    detail = (
        "every model in chain "
        + repr(models_to_try)
        + " failed on backend "
        + repr(getattr(backend, "name", type(backend).__name__))
        + "; errors: "
        + " | ".join(errors)
    )
    # If a model-down (breaker-open) signal appeared anywhere in an all-failed
    # chain, surface it as BackendUnavailable so the run loop aborts CLEANLY on a
    # true full-endpoint outage (rather than as a recoverable BackendError).
    if saw_unavailable:
        raise BackendUnavailable(detail)
    # An all-failed chain whose failures were TRANSIENT-class (deadline hangs,
    # 302→outage.dartmouth.edu redirects, 5xx flaps on EVERY model) is a
    # full-endpoint outage that will heal on its own — the run must abort
    # cleanly with state preserved, exactly like the breaker-open case. Before
    # this clause, such an exhaustion raised plain BackendError, which the
    # stage-panel's generic engine-failure handler escalated to
    # human_input_needed — observed live on PROJ-552 (dispatch 27306941191,
    # 2026-06-10: qwen deadline-hang + gpt-oss/gemma both 302→outage). A
    # transient infrastructure outage is NOT human-actionable (bug-#8 family).
    if saw_transient:
        raise BackendUnavailable(detail)
    # All-permanent exhaustion (every peer hard-rejected) — genuinely
    # engine/config-actionable, keep the recoverable aggregate error.
    raise BackendError(detail)


def reasoning_chat(
    backend: BaseBackend,
    messages: Iterable[ChatMessage],
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> ChatResponse:
    """THE single entry point for a reasoning/analysis LLM call on a GIVEN backend.

    Every claim/fill/grounding/triage/review reasoning call routes through here
    instead of re-implementing the policy (this replaces the former per-module
    ``_chat_reasoning_safe`` copies). It delegates to
    :func:`chat_with_model_fallback`, so it automatically gets the full stack —
    peer-model fallback (qwen→gpt-oss→gemma), retry+jitter+backoff, the per-model
    circuit breaker, the per-request deadline, the deadline/302 fast-fail, and
    stub-backend signature degradation — with the reasoning-safe
    :data:`REASONING_MAX_TOKENS` default applied when the caller doesn't override
    it (a generation-style caller passes :data:`GENERATION_MAX_TOKENS`).

    ``model=None`` makes a single no-fallback call (the offline / injected-fake
    test shape); production callers pass a concrete model and thus get the peer
    walk. Use this — never call ``backend.chat`` directly (the centralization
    guard test enforces that).
    """
    return chat_with_model_fallback(
        backend,
        messages,
        model=model,
        max_tokens=REASONING_MAX_TOKENS if max_tokens is None else max_tokens,
        temperature=temperature,
    )


def chat_with_fallback(
    messages: Iterable[ChatMessage],
    *,
    default_backend: str,
    fallback_backends: list[str],
    model: str,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> ChatResponse:
    """Try default backend; on TransientBackendError, walk the fallback chain.

    If `max_tokens` is None we default to 131072 (128K) — Spec Kit agents
    (Tasker, Specifier, Planner, paper-writers) frequently exceed the
    per-model silent default (often 1024) and produce truncated output
    otherwise. qwen3.5-122b's real context is 256K (verified 2026-05-29
    via the Dartmouth model registry), so 128K leaves ample input room.

    Per backend, retries the requested `model` 3x. On persistent
    transient errors, tries each model in MODEL_FALLBACKS[model] (1
    attempt each) on the SAME backend before falling through to the
    next backend. This handles single-model vLLM outages on Dartmouth
    where other models on the same backend are still healthy.
    """
    if max_tokens is None:
        # 128K default — tokens cost time but not money on Dartmouth's
        # community plan, so we use the largest sensible budget. Per
        # the API model registry (verified 2026-05-29):
        #   qwen.qwen3.5-122b     max_input_tokens=256000  (was assumed 32K)
        #   openai.gpt-oss-120b   max_input_tokens=128000
        #   google.gemma-4-31B-it 128K context
        # ``max_output_tokens`` is unset on the vLLM-hosted models, so
        # there is no hard server-side cap; output is bounded by
        # ``max_input_tokens - input_tokens``. 128K is the highest cap
        # that fits every model in MODEL_FALLBACKS without per-model
        # branching. This is the GENERATION budget (spec/plan/tasks/paper
        # agents emit huge outputs) — the single source of truth.
        max_tokens = GENERATION_MAX_TOKENS
    chain = [default_backend, *fallback_backends]
    errors: list[str] = []
    saw_outage = False
    msg_list = list(messages)
    for name in chain:
        try:
            backend = make_backend(name)
        except PermanentBackendError as exc:
            errors.append(f"{name}(init): {exc}")
            continue
        # Try the primary model with retries, then fall back through peer
        # models on the SAME backend — :func:`chat_with_model_fallback` owns
        # that walk (and the reviewer/reviser share it). A permanent failure on
        # the primary model surfaces as PermanentBackendError; a fully-exhausted
        # transient chain surfaces as BackendUnavailable. Either way we move on
        # to the next backend in ``chain`` (matching the prior per-backend
        # semantics).
        try:
            return chat_with_model_fallback(
                backend,
                msg_list,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except BackendUnavailable as exc:
            # The backend's WHOLE model chain is in outage (breaker open /
            # transient exhaustion). Remember it: if every other backend
            # also fails, the aggregate is an OUTAGE, not an engine error.
            saw_outage = True
            errors.append(f"{name}(outage): {exc}")
            continue
        except (PermanentBackendError, BackendError) as exc:
            errors.append(f"{name}: {exc}")
            continue
    detail = (
        "every backend in chain "
        + repr(chain)
        + " failed; errors: "
        + " | ".join(errors)
    )
    # Spec 023 defect #11 (same family as the PR-#302 model-level fix, one
    # layer up): a Dartmouth-wide outage correctly surfaced as
    # BackendUnavailable from the model walk — and was then SWALLOWED here
    # (it subclasses BackendError), with the exhaustion re-raised as plain
    # BackendError once the local fallback failed too. The stage panel's
    # generic handler treated that as an engine failure. Observed live on
    # PROJ-552's plan panel (2026-06-11). An exhaustion that includes ANY
    # backend-level outage signal aborts cleanly so the project retries on
    # a later tick with state preserved.
    if saw_outage:
        raise BackendUnavailable(detail)
    raise BackendError(detail)


__all__ = [
    "GENERATION_MAX_TOKENS",
    "REASONING_MAX_TOKENS",
    "chat_with_fallback",
    "chat_with_model_fallback",
    "make_backend",
    "reasoning_chat",
]
