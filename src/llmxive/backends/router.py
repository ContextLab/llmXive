"""Backend router (T020) — falls back through a chain on transient errors.

The agent registry declares a named capability ``profile`` per agent (spec 026
US5); the router resolves that profile to a concrete, backend-diverse model
chain per call via ``model_selection`` — there is no separate per-agent
backend declaration to configure.
"""

from __future__ import annotations

import enum
import hashlib
import os
from collections.abc import Iterable
from functools import lru_cache
from typing import TYPE_CHECKING

from llmxive.backends.base import (
    BackendCredentialError,
    BackendUnavailable,
    BaseBackend,
    ChatMessage,
    ChatResponse,
    ModelDownError,
    PaidGuardDenied,
    PermanentBackendError,
    TransientBackendError,
    UnsupportedFeatureError,
)
from llmxive.backends.dartmouth import DartmouthBackend
from llmxive.backends.huggingface import HuggingFaceBackend
from llmxive.backends.local import LocalBackend

if TYPE_CHECKING:
    # Type-checking only: a module-top runtime import here would cycle, since
    # importing the ``llmxive.model_selection`` PACKAGE (required to reach the
    # ``types`` submodule) runs its ``__init__``, which imports ``execute.py``,
    # which imports THIS module (``llmxive.backends.router``) for
    # ``make_backend``/``chat_one_candidate``/``disposition_of``. ``route_chat``
    # itself is likewise imported function-locally below for the same reason.
    # ``from __future__ import annotations`` (above) makes the annotations that
    # reference ``RequirementOverrides`` lazy strings, so this is safe.
    from llmxive.model_selection.attempt_hooks import ReservationAuthority, RouteAudit
    from llmxive.model_selection.types import IndependenceBaseline, RequirementOverrides

_REGISTRY: dict[str, type[BaseBackend]] = {
    "dartmouth": DartmouthBackend,
    "local": LocalBackend,
    "huggingface": HuggingFaceBackend,
}


def make_backend(name: str) -> BaseBackend:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise PermanentBackendError(f"unknown backend: {name!r}")
    if cls is DartmouthBackend:
        from llmxive.backends.dartmouth import _cloud_models_url, _ensure_api_key_env

        _ensure_api_key_env()
        # Keep outage history across agent calls, isolated by endpoint and auth.
        # No raw credential is retained in the cache key or diagnostic output.
        context = hashlib.sha256((
            _cloud_models_url() + "\0" + os.environ.get("DARTMOUTH_CHAT_API_KEY", "")
        ).encode()).hexdigest()
        return _dartmouth_backend(context)
    if cls is HuggingFaceBackend:
        from llmxive.backends.huggingface import BILL_TO_ENV, ROUTER_BASE_URL
        from llmxive.credentials import HF_TOKEN_NAME

        # As for Dartmouth: the per-model circuit breaker lives on the instance,
        # so a fresh instance per call would forget an outage and send (and
        # reserve budget for) every call again. Isolated by endpoint and the
        # environment credentials; no raw credential is retained.
        context = hashlib.sha256((
            ROUTER_BASE_URL + "\0" + os.environ.get(HF_TOKEN_NAME, "")
            + "\0" + os.environ.get(BILL_TO_ENV, "")
        ).encode()).hexdigest()
        return _huggingface_backend(context)
    return cls()


@lru_cache(maxsize=8)
def _dartmouth_backend(context: str) -> DartmouthBackend:
    return DartmouthBackend()


@lru_cache(maxsize=8)
def _huggingface_backend(context: str) -> HuggingFaceBackend:
    return HuggingFaceBackend()


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
    deadline_s: float | None = None,
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
    a model still work. ``deadline_s`` (spec 026 execute's ``ExecutionOptions``)
    is passed to real backends that accept it and degraded away first for fakes /
    backends without a deadline param. This NEVER catches backend errors —
    Transient/Permanent propagate to the chain walker; only ``TypeError``
    (signature mismatch) is handled here.
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
    if deadline_s is not None:
        full["deadline_s"] = deadline_s
    attempts.append(full)
    # Degrade deadline_s FIRST (newest/most-optional kwarg; fakes + backends without
    # a deadline param don't accept it), keeping max_tokens/temperature; then drop
    # temperature (keep the load-bearing reasoning budget longest), then max_tokens,
    # then a bare model-only / no-kwarg call.
    if deadline_s is not None:
        attempts.append({k: v for k, v in full.items() if k != "deadline_s"})
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


class CandidateDisposition(enum.Enum):
    """How a :class:`ModelChain` walker (spec 026 ``execute``) must treat a
    candidate's TERMINAL failure — the three outcomes the plan enumerates.

    - ``SKIP``: an EXPECTED non-use of this candidate (the paid guard declined it)
      — say nothing failed; try the next candidate.
    - ``RETRY_ADVANCE``: the candidate was tried and failed transiently (generic
      transient exhausted its retries, the model is down, or its breaker is open)
      — advance to the next candidate; a fully-transient exhaustion is an OUTAGE.
    - ``ABORT``: a hard permanent failure (auth, bad request, config) that walking
      more candidates cannot heal — stop the chain immediately.
    """

    SKIP = "skip"
    RETRY_ADVANCE = "retry_advance"
    ABORT = "abort"


def disposition_of(exc: BaseException) -> CandidateDisposition:
    """Classify a backend failure into a :class:`CandidateDisposition`. The typed
    ``PaidGuardDenied`` split is what lets a paid-guard denial SKIP (not ABORT):
    it is checked BEFORE its ``PermanentBackendError`` base. ``BackendUnavailable``
    (breaker open) and every transient class advance; any other permanent aborts.
    """
    if isinstance(exc, PaidGuardDenied):
        return CandidateDisposition.SKIP
    if isinstance(exc, BackendCredentialError):
        return CandidateDisposition.SKIP  # no usable credential for this backend: try a peer
    if isinstance(exc, UnsupportedFeatureError):
        return CandidateDisposition.SKIP  # candidate can't serve this feature → advance
    if isinstance(exc, BackendUnavailable):
        return CandidateDisposition.RETRY_ADVANCE  # breaker open → try next candidate
    if isinstance(exc, TransientBackendError):  # incl. ModelDown/Deadline/EmptyReply
        return CandidateDisposition.RETRY_ADVANCE
    if isinstance(exc, PermanentBackendError):  # hard refusal / config
        return CandidateDisposition.ABORT
    return CandidateDisposition.ABORT  # unknown backend error → conservative abort


def chat_one_candidate(
    backend: BaseBackend,
    messages: Iterable[ChatMessage],
    *,
    model: str | None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    deadline_s: float | None = None,
    retries: int = 3,
) -> ChatResponse:
    """Run EXACTLY ONE model with the router's per-model safeguards but NO
    fallback chain — the seam spec-026 ``execute`` walks a :class:`ModelChain`
    over (each candidate is one call to this).

    Safeguards preserved: the per-model circuit breaker + per-request deadline +
    302-fast-fail live inside ``backend.chat`` and still apply; this adds the
    bounded same-model RETRY of GENERIC transient flaps (``retries`` attempts,
    2s-per-attempt backoff). It fails fast — no retry — on the conditions where
    retrying the SAME model is futile: ``BackendUnavailable`` (breaker open),
    ``ModelDownError`` (deadline hang / 302 outage), a ``reasoning budget
    exhausted`` transient (it will re-exhaust), and any ``PermanentBackendError``
    (incl. the ``PaidGuardDenied`` skip). On terminal failure it RAISES the
    classified exception; the caller maps it with :func:`disposition_of` and
    decides skip / advance / abort. ``model=None`` makes a single
    signature-degrading call (the injected-fake test shape).

    RETRY-COST COMPOSITION (spec 026 #4 — slice-3 acceptance criterion): this makes
    up to ``retries`` provider ATTEMPTS for one candidate, but a credit reservation
    holds ONE call's ``worst_case_credits``. A paid transient could therefore cost
    up to ``retries x worst_case``. ``execute`` OWNS ``retries`` (it passes it), so
    for a PAID candidate it MUST reserve the full retry envelope
    (``worst_case_credits x retries``) up front — or pass ``retries=1`` and rely on
    advancing to the next candidate. Free candidates are unaffected.
    """
    import time as _time

    msg_list = list(messages)
    if model is None:
        return _chat_one_model(
            backend, msg_list, model=None, max_tokens=max_tokens,
            temperature=temperature, deadline_s=deadline_s,
        )
    last_transient: TransientBackendError | None = None
    for attempt in range(max(1, retries)):
        if attempt:
            _time.sleep(2.0 * attempt)
        try:
            return _chat_one_model(
                backend, msg_list, model=model, max_tokens=max_tokens,
                temperature=temperature, deadline_s=deadline_s,
            )
        except ModelDownError:
            raise  # model down/deadline/302 — retrying the same model is futile
        except TransientBackendError as exc:
            last_transient = exc
            if "reasoning budget exhausted" in str(exc):
                raise  # will re-exhaust the budget — advance instead of burning retries
            continue  # generic transient flap — retry the SAME model
        except PermanentBackendError:
            raise  # PaidGuardDenied (skip) / BackendUnavailable (breaker) / hard refusal
    assert last_transient is not None
    raise last_transient


def _walker_route(
    backend: BaseBackend,
    messages: Iterable[ChatMessage],
    *,
    model: str | None,
    max_tokens: int,
    temperature: float | None,
    overrides: RequirementOverrides | None = None,
    profile: str = "standard_generation",
    independence_against: IndependenceBaseline | None = None,
    route_audit: RouteAudit | None = None,
    reservation_authority: ReservationAuthority | None = None,
    route_id: str | None = None,
    reraise_model_unavailable: bool = False,
    excluded_models: frozenset[str] = frozenset(),
) -> ChatResponse:
    """Shared body for the retired instance-taking walkers (spec 026 slice 5):
    delegate to ``route_chat`` (select() → execute()), adapting the caller's
    injected ``backend`` into a ``backend_factory`` so it serves its OWN
    candidates (a real backend the caller built, or a test's injected fake) while
    other backends resolve via :func:`make_backend`.

    A backend whose ``name`` is unset is treated as ``dartmouth`` (the default
    serving backend), so an injected-fake reviser/reviewer test still serves the
    offline snapshot's Dartmouth chain without swapping the object it holds.

    ``overrides`` (spec 026 slice 6) forwards escalation constraints straight to
    ``route_chat``, which composes them on top of the profile's base requirement;
    ``None`` (the default) leaves every existing caller's behavior unchanged.
    ``profile`` (spec 026 slice 7 / US5) is the named capability-requirement
    profile a caller resolves from its ``AgentRegistryEntry.profile``; it
    defaults to ``"standard_generation"`` — the slice-5 provisional constant —
    so unmigrated callers keep their existing behavior.

    Outage-classification contract preserved: ``ModelUnavailable`` (ineligible /
    cold start) and ``ChainExhausted`` (transient/outage exhaustion) re-raise as
    ``BackendUnavailable`` (clean run-loop abort with state preserved, never a
    human escalation); a request-level permanent refusal propagates unchanged.

    ``independence_against``/``route_audit``/``reservation_authority``/``route_id``
    (spec 025) are forwarded straight to ``route_chat``, which already accepts all
    four; every one defaults to ``None``, so an unmigrated caller's behavior is
    byte-for-byte unchanged. ``reraise_model_unavailable`` is the ONE deviation
    from the classification contract above, and only for the caller that asks:
    FR-002's proposal reroute needs the RAW ``ModelUnavailable`` to decide whether
    to try its relaxed second leg, which a ``BackendUnavailable`` has already
    erased. ``ChainExhausted`` is never affected — see the handler.

    ``excluded_models`` omits request-local rejected producers (e.g. the model
    that just returned a malformed revision) without changing the profile, the
    capability policy or any circuit breaker. It is NOT a second selection
    path: the ids are unioned into ``RequirementOverrides.exclude_models``, so
    ``select()`` simply ranks the remaining eligible candidates.
    """
    from llmxive.model_selection.execute import ChainExhausted
    from llmxive.model_selection.route import route_chat
    from llmxive.model_selection.types import ModelUnavailable

    if excluded_models:
        from dataclasses import replace

        from llmxive.model_selection.types import RequirementOverrides as _Overrides

        overrides = (
            _Overrides(exclude_models=frozenset(excluded_models))
            if overrides is None
            else replace(
                overrides,
                exclude_models=overrides.exclude_models | frozenset(excluded_models),
            )
        )

    injected_name = getattr(backend, "name", None) or "dartmouth"

    def factory(name: str) -> BaseBackend:
        return backend if name == injected_name else make_backend(name)

    try:
        return route_chat(
            messages,
            profile=profile,
            caller_model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            backend_factory=factory,
            overrides=overrides,
            independence_against=independence_against,
            route_audit=route_audit,
            reservation_authority=reservation_authority,
            route_id=route_id,
        )
    except ModelUnavailable as exc:
        # Spec 025 FR-002: the proposal reroute needs the RAW ModelUnavailable to decide
        # whether to try its relaxed second leg. Converting first would erase the very
        # distinction the reroute turns on. Every other caller keeps the contract above.
        if reraise_model_unavailable:
            raise
        raise BackendUnavailable(
            f"model selection/execution produced no usable candidate "
            f"(outage or ineligible): {exc}"
        ) from exc
    except ChainExhausted as exc:
        # ALWAYS converted, even for a caller that asked for the raw ModelUnavailable: the
        # chain RAN and every candidate failed, which is an outage, not an eligibility
        # problem a relaxed profile could solve. Rerouting on it would burn the fallback
        # leg on the same broken backends.
        raise BackendUnavailable(
            f"model selection/execution produced no usable candidate "
            f"(outage or ineligible): {exc}"
        ) from exc


def chat_with_model_fallback(
    backend: BaseBackend,
    messages: Iterable[ChatMessage],
    *,
    model: str | None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    overrides: RequirementOverrides | None = None,
    profile: str = "standard_generation",
    independence_against: IndependenceBaseline | None = None,
    route_audit: RouteAudit | None = None,
    reservation_authority: ReservationAuthority | None = None,
    route_id: str | None = None,
    reraise_model_unavailable: bool = False,
    excluded_models: frozenset[str] = frozenset(),
) -> ChatResponse:
    """Convergence-panel / reviser reasoning call on a GIVEN backend (spec 026
    slice 5): a thin wrapper over :func:`_walker_route` → ``route_chat`` (select()
    → execute()). The peer-model walk is no longer hand-coded here — ``execute``
    walks the SELECTED ``ModelChain`` (each candidate dispatched through its own
    ``ModelRef.backend``, breaker + deadline + bounded retry preserved via the
    ``chat_one_candidate`` primitive), and the injected ``backend`` serves its own
    candidates. The reasoning-safe :data:`REASONING_MAX_TOKENS` is the default
    when the caller doesn't pin one. ``overrides`` (spec 026 slice 6) forwards
    escalation constraints to ``route_chat``; ``None`` (default) is a no-op.
    ``profile`` (spec 026 slice 7) selects the capability class; default
    ``"standard_generation"`` preserves prior behavior for unmigrated callers.

    The five spec-025 params are lane plumbing, forwarded verbatim to
    :func:`_walker_route`: ``independence_against`` (FR-002's required-family
    constraint), the mandatory ``route_audit`` sink and ``reservation_authority``
    (FR-033a/FR-033), the durable ``route_id`` that makes a replayed call
    recognizable, and ``reraise_model_unavailable`` for the reroute. All default to
    a no-op, so the research/paper pipeline is untouched.

    ``excluded_models`` omits request-local rejected producers without changing
    the profile or any circuit breaker (see :func:`_walker_route`).
    """
    return _walker_route(
        backend, messages, model=model,
        max_tokens=REASONING_MAX_TOKENS if max_tokens is None else max_tokens,
        temperature=temperature,
        overrides=overrides,
        profile=profile,
        independence_against=independence_against,
        route_audit=route_audit,
        reservation_authority=reservation_authority,
        route_id=route_id,
        reraise_model_unavailable=reraise_model_unavailable,
        excluded_models=excluded_models,
    )


def reasoning_chat(
    backend: BaseBackend,
    messages: Iterable[ChatMessage],
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    overrides: RequirementOverrides | None = None,
    profile: str = "standard_generation",
    excluded_models: frozenset[str] = frozenset(),
) -> ChatResponse:
    """THE single entry point for a reasoning/analysis LLM call (spec 026 slice 5):
    a thin wrapper over :func:`_walker_route` → ``route_chat``. Every
    claim/fill/grounding/triage/review reasoning call routes through here; the
    reasoning-safe :data:`REASONING_MAX_TOKENS` default applies unless the caller
    overrides it (a generation-style caller passes :data:`GENERATION_MAX_TOKENS`).
    Use this — never call ``backend.chat`` directly (the centralization guard test
    enforces that). ``overrides`` (spec 026 slice 6) forwards escalation
    constraints to ``route_chat``; ``None`` (default) is a no-op. ``profile``
    (spec 026 slice 7) selects the capability class for callers that resolve one
    from an ``AgentRegistryEntry``; default ``"standard_generation"`` preserves
    prior behavior for the many non-registry reasoning callers (claim/fill/
    grounding/triage) that have no profile of their own. ``excluded_models``
    omits request-local rejected producers (see :func:`_walker_route`).
    """
    return _walker_route(
        backend, messages, model=model,
        max_tokens=REASONING_MAX_TOKENS if max_tokens is None else max_tokens,
        temperature=temperature,
        overrides=overrides,
        profile=profile,
        excluded_models=excluded_models,
    )


def chat_with_fallback(
    messages: Iterable[ChatMessage],
    *,
    max_tokens: int | None = None,
    temperature: float | None = None,
    overrides: RequirementOverrides | None = None,
    profile: str = "standard_generation",
) -> ChatResponse:
    """Registry-agent routing chokepoint (spec 026 slice 5): resolve the chain
    through model SELECTION and delegate to ``execute`` — no hand-walk of the
    legacy per-model fallback table, no backend-name loop.

    Delegates to :func:`llmxive.model_selection.route.route_chat`, which acquires
    the real LKG-inclusive runtime snapshot and runs the pure ``select`` for
    ``profile`` (spec 026 slice 7: the caller's real ``AgentRegistryEntry.profile``;
    default ``"standard_generation"`` preserves the slice-5 provisional constant
    for unmigrated callers), then hands the WHOLE ``ModelChain`` to ``execute`` —
    which dispatches EACH candidate through its own ``ModelRef.backend`` and does
    the paid reservation/settlement. Backend fallback is first-class in the
    selected chain (the local candidate carries ``backend=="local"``), so there
    is no separate per-backend walk to configure and no caller-side model pin —
    every call site expresses its INTENT via ``profile``, never a raw model id
    (spec 026 slice 7; the obsolete ``default_backend`` / ``fallback_backends`` /
    ``model`` bridge parameters were removed once every caller migrated). If
    `max_tokens` is None it defaults to the GENERATION budget (131072) — Spec Kit
    agents emit large artifacts. ``overrides`` (spec 026 slice 6) forwards
    escalation constraints straight to ``route_chat``; ``None`` (default) is a
    no-op, leaving every existing caller's behavior unchanged.

    Outage-classification contract (preserved): a fully-INELIGIBLE selection
    (cold start / all-stale → ``ModelUnavailable``) or a fully-EXHAUSTED chain
    (transient/outage/paid-skip → ``ChainExhausted``) is NOT engine-actionable —
    it surfaces as ``BackendUnavailable`` so the run loop clean-aborts with state
    preserved (never a human escalation). A request-level PERMANENT refusal is
    re-raised by ``execute`` and propagates unchanged (matching the old
    primary-permanent abort).
    """
    from llmxive.model_selection.execute import ChainExhausted
    from llmxive.model_selection.route import route_chat
    from llmxive.model_selection.types import ModelUnavailable

    if max_tokens is None:
        max_tokens = GENERATION_MAX_TOKENS
    try:
        return route_chat(
            messages,
            profile=profile,
            max_tokens=max_tokens,
            temperature=temperature,
            overrides=overrides,
        )
    except (ModelUnavailable, ChainExhausted) as exc:
        raise BackendUnavailable(
            f"model selection/execution produced no usable candidate "
            f"(outage or ineligible): {exc}"
        ) from exc


__all__ = [
    "GENERATION_MAX_TOKENS",
    "REASONING_MAX_TOKENS",
    "CandidateDisposition",
    "chat_one_candidate",
    "chat_with_fallback",
    "chat_with_model_fallback",
    "disposition_of",
    "make_backend",
    "reasoning_chat",
]
