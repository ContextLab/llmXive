"""Routing chokepoint (spec 026, Phase 2 slice 5 — corrected execute()-delegation).

``route_chat`` is the SINGLE production entry that turns a call's INTENT into a
real chat WITHOUT ever projecting the selected chain back to model-id strings or
walking the legacy peer chain. It:

1. acquires the REAL, LKG-inclusive :func:`runtime_snapshot` (bounded
   negative-caching so an outage never re-fetches catalog+local+credit per call);
2. derives ``allow_paid`` from the snapshot's credit opt-in when the caller does
   not pin it (so the guarded paid tail can appear; ``execute``'s twice-checked
   guard + reservation still decide per call);
3. builds the requirement for the named ``profile`` priced against the ACTUAL
   messages (:func:`build_requirement` + :func:`call_budget_for`);
4. runs the PURE :func:`select` (requirement-sensitive freshness; a cold start —
   no live catalog AND no LKG — fails CLOSED with ``ModelUnavailable``, never a
   fall back to a static legacy chain);
5. reorders the chain with :func:`_promote_primary` so the caller's pinned model
   runs FIRST *iff* ``select`` kept it (present + eligible), and NEVER resurrects
   a live-confirmed-absent one (revert-finding #3 / US5 scenario 2);
6. delegates the WHOLE :class:`ModelChain` to :func:`execute`, which dispatches
   each candidate through ITS OWN ``ModelRef.backend`` (revert-finding #2), does
   the atomic paid reservation + retry-envelope + settlement (revert-finding #1),
   and returns the first successful :class:`ChatResponse`.

Backend fallback is therefore FIRST-CLASS through ``select``/``execute`` (the
local candidate carries ``backend=="local"``); the legacy ``default_backend`` /
``fallback_backends`` inputs are redundant and the chokepoint ignores them (spec
§29). The compat walkers in ``backends.router`` are thin wrappers over this.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections.abc import Callable, Iterable
from dataclasses import replace
from pathlib import Path

from llmxive.backends.base import BaseBackend, ChatMessage, ChatResponse, ImagePart, TextPart
from llmxive.backends.router import make_backend
from llmxive.model_selection.attempt_hooks import (
    ChainResolved,
    ReservationAuthority,
    RouteAudit,
    SelectionFailure,
    emit_audit,
)
from llmxive.model_selection.execute import execute
from llmxive.model_selection.ledger_transport import LedgerConfig
from llmxive.model_selection.policy import FundedPolicy
from llmxive.model_selection.profiles import build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.snapshot import runtime_snapshot
from llmxive.model_selection.tokens import call_budget_for
from llmxive.model_selection.types import (
    ExecutionOptions,
    IndependenceBaseline,
    ModelChain,
    ModelRef,
    ModelRequirement,
    ModelUnavailable,
    RequirementOverrides,
    RuntimeSnapshot,
    shift_level,
)

__all__ = [
    "DETERMINISTIC_NO_LLM",
    "RequirementOverrides",
    "free_peer_ids",
    "reset_snapshot_cache",
    "resolve_chain",
    "route_chat",
]

#: The registry sentinel for scaffolding agents that make NO LLM call (spec 015;
#: ``test_config_consistency.NO_LLM``). Such an agent must NEVER reach the model
#: layer — reaching ``route_chat`` with it is a programming error, so we fail fast
#: BEFORE any snapshot / select / execute work (bypasses the mechanism entirely).
DETERMINISTIC_NO_LLM = "deterministic-no-llm"

#: Bounded snapshot cache TTL (seconds). Matches the ~30s credit-balance cache: a
#: snapshot is acquired at most once per window, so a Dartmouth outage does not
#: re-hit catalog+local+credit on every routed call. The RESULT is cached whether
#: it is healthy OR a cold-start/LKG snapshot (the "bounded negative result",
#: revert-finding #6) — ``runtime_snapshot`` never raises; it degrades to
#: ``unavailable`` provenance, which ``select`` then fails closed on.
_SNAPSHOT_TTL_S = 30.0

#: Monotonic clock indirection (module-level so tests can freeze it). Never a
#: wall-clock value that would drift the TTL.
_now: Callable[[], float] = time.monotonic

#: ``(snapshot, monotonic_expiry)`` or ``None``.
_SNAPSHOT_CACHE: tuple[RuntimeSnapshot, float] | None = None


def reset_snapshot_cache() -> None:
    """Drop the bounded snapshot cache (test isolation / forced refresh)."""
    global _SNAPSHOT_CACHE
    _SNAPSHOT_CACHE = None


def _acquire_snapshot() -> RuntimeSnapshot:
    """The REAL, LKG-inclusive snapshot, served from the bounded cache when a
    prior acquisition is still within the TTL (negative caching included)."""
    global _SNAPSHOT_CACHE
    now = _now()
    cached = _SNAPSHOT_CACHE
    if cached is not None and cached[1] > now:
        return cached[0]
    snap = runtime_snapshot()
    _SNAPSHOT_CACHE = (snap, now + _SNAPSHOT_TTL_S)
    return snap


def _tighter_credits(a: int | None, b: int | None) -> int | None:
    """The TIGHTER (smaller) per-call credit ceiling: the set one when only one is
    set, else min(). None means 'no ceiling' — a set ceiling always wins."""
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b)


def _promote_primary(chain: ModelChain, caller_model: str | None) -> ModelChain:
    """Reorder ``chain.candidates`` so the caller's pinned ``caller_model`` runs
    FIRST — but ONLY if ``select`` already kept it (present + eligible). If the
    caller pinned nothing, or the model is absent from ``select``'s result (dropped
    for staleness / exclusion / independence / the paid guard, or live-confirmed
    absent), the chain is returned UNCHANGED — never resurrecting an absent model
    (revert-finding #3). Moves whole ``Candidate`` objects, so backend identity and
    pricing ride along (revert-finding #2)."""
    if not caller_model:
        return chain
    idx = next(
        (i for i, c in enumerate(chain.candidates) if c.model_ref.model_id == caller_model),
        None,
    )
    if idx is None or idx == 0:
        return chain
    cands = list(chain.candidates)
    cands.insert(0, cands.pop(idx))
    return replace(chain, candidates=tuple(cands))


def _requirement_digest(requirement: ModelRequirement) -> str:
    """Stable SHA-256 over the requirement's canonical fields — identifies WHAT
    was requested (FR-027: detect a candidate that changed the request), distinct
    from the snapshot digest (which identifies the world ``select`` ran against).
    Deterministic + cross-process-stable: sorted keys, sets flattened to sorted
    lists, no object identity/repr involved."""
    payload = {
        "capability": requirement.capability,
        "required_features": sorted(requirement.required_features),
        "min_context_tokens": requirement.min_context_tokens,
        "independence_against": {
            "models": sorted(requirement.independence_against.models),
            "families": sorted(requirement.independence_against.families),
            "vendors": sorted(requirement.independence_against.vendors),
            "endpoints": sorted(requirement.independence_against.endpoints),
        },
        "required_independence": sorted(requirement.required_independence),
        "preferred_independence": sorted(requirement.preferred_independence),
        "exclude_models": sorted(requirement.exclude_models),
        "exclude_families": sorted(requirement.exclude_families),
        "exclude_vendors": sorted(requirement.exclude_vendors),
        "exclude_endpoints": sorted(requirement.exclude_endpoints),
        "allow_paid": requirement.allow_paid,
        "require_paid": requirement.require_paid,
        "max_credits": requirement.max_credits,
        "max_catalog_age_s": requirement.max_catalog_age_s,
        "max_candidates": requirement.max_candidates,
        "require_fresh_snapshot": requirement.require_fresh_snapshot,
        "profile": requirement.profile,
        "track": requirement.track,
        "strength": requirement.strength,
        "budget_step_down": requirement.budget_step_down,
        "call_budget": [
            requirement.call_budget.max_input_tokens,
            requirement.call_budget.max_output_tokens,
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _content_digest_value(content: str | tuple[TextPart | ImagePart, ...]) -> dict:
    """Canonical, JSON-serializable projection of a :class:`ChatMessage.content`
    (spec 025 maintainer review F1): ``content`` is either a plain string OR a
    tuple of ``ContentPart``s (``TextPart`` / ``ImagePart``, both dataclasses that
    ``json.dumps`` cannot serialize directly). An ``ImagePart``'s raw bytes are
    NEVER embedded in the digest payload — only their SHA-256, so the digest stays
    small and stable regardless of image size. A future ``ContentPart`` variant
    that is neither (maintainer review finding #3, LOW) raises ``TypeError``
    instead of being silently dropped — an unhandled part silently vanishing from
    the digest would let two DIFFERENT prompts share the same digest."""
    if isinstance(content, str):
        return {"type": "text", "text": content}
    parts = []
    for part in content:
        if isinstance(part, TextPart):
            parts.append({"type": "text", "text": part.text})
        elif isinstance(part, ImagePart):
            parts.append({
                "type": "image", "mime": part.mime, "width": part.width,
                "height": part.height, "data_sha256": hashlib.sha256(part.data).hexdigest(),
            })
        else:
            raise TypeError(
                f"_content_digest_value: unhandled ContentPart type {type(part).__name__} — "
                "extend the canonical projection when a new content type is added"
            )
    return {"type": "multipart", "parts": parts}


def messages_digest(messages: list[ChatMessage]) -> str:
    """Stable SHA-256 over the routed messages (F2): identifies WHAT prompt/context
    was actually sent, distinct from the requirement/snapshot digests. Deterministic
    + cross-process-stable: a canonical ``(role, content)`` projection (multimodal
    ``content`` is projected via :func:`_content_digest_value`, never passed to
    ``json.dumps`` raw), no object identity/repr involved."""
    payload = [(m.role, _content_digest_value(m.content)) for m in messages]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _select_audited(
    requirement: ModelRequirement,
    snap: RuntimeSnapshot,
    route_audit: RouteAudit | None,
    route_id: str,
    funded_policy: FundedPolicy | None = None,
) -> ModelChain:
    """Run select; on ModelUnavailable emit a SelectionFailure audit event (so the
    proposal reroute's failed first leg is auditable, FR-002/F3) and RE-RAISE — the
    caller's fail-closed / reroute logic is unchanged. The emit itself goes through
    ``emit_audit`` (F4) so a sink failure here is normalized to ``RouteAuditError``
    and takes precedence over the ``ModelUnavailable`` being reported — an
    audit-system failure is route-fatal. ``funded_policy`` is forwarded to
    ``select`` (``None`` → the production ``FUNDED_POLICY``)."""
    try:
        return select(requirement, snap, funded_policy=funded_policy)
    except ModelUnavailable as exc:
        emit_audit(route_audit, SelectionFailure(
            route_id=route_id,
            exception_type=type(exc).__name__, message=str(exc),
            requirement_digest=_requirement_digest(requirement), snapshot_provenance=dict(snap.sources),
        ))
        raise


def resolve_chain(
    messages: Iterable[ChatMessage],
    *,
    profile: str,
    max_tokens: int,
    allow_paid: bool | None = None,
    independence_against: IndependenceBaseline | None = None,
    snapshot: RuntimeSnapshot | None = None,
    overrides: RequirementOverrides | None = None,
    route_audit: RouteAudit | None = None,
    route_id: str = "",
    funded_policy: FundedPolicy | None = None,
) -> tuple[ModelRequirement, ModelChain]:
    """THE selection decision for one call: acquire the (bounded-cache) snapshot,
    build the profile's requirement priced against ``messages``, compose
    ``overrides`` on top, and run the pure :func:`select`. Returns the final
    ``(requirement, chain)``; performs NO dispatch.

    This is the single place a profile + overrides become a chain.
    :func:`route_chat` calls it and then executes the result; a caller that only
    needs to know what the selector WOULD offer (:func:`free_peer_ids`) calls it
    too, so a preview can never disagree with the real decision.

    ``funded_policy`` is an injection seam beside ``snapshot`` (forwarded to every
    ``select`` pass; ``None`` → the production ``FUNDED_POLICY``).

    Raises :class:`ModelUnavailable` when no candidate is eligible (including
    from the leader-resolving passes) and ``ValueError`` when ``allow_paid`` is
    supplied both directly and through ``overrides``.
    """
    msg_list = list(messages)
    snap = snapshot if snapshot is not None else _acquire_snapshot()

    # allow_paid precedence (spec 026 slice 6, round-2 #1): no silent precedence.
    if allow_paid is not None and overrides is not None and overrides.allow_paid is not None:
        raise ValueError(
            "allow_paid supplied both directly and through overrides — pass exactly one"
        )
    if overrides is not None and overrides.allow_paid is not None:
        allow_paid_eff = overrides.allow_paid
    elif allow_paid is not None:
        allow_paid_eff = allow_paid
    else:
        allow_paid_eff = snap.credit.paid_opt_in

    call_budget = call_budget_for(msg_list, max_tokens)
    base = build_requirement(
        profile,
        call_budget,
        independence_against=independence_against,
        allow_paid=allow_paid_eff,
    )
    if overrides is None:
        requirement = base
    else:
        requirement = replace(
            base,
            require_paid=base.require_paid or overrides.require_paid,
            exclude_models=base.exclude_models | overrides.exclude_models,
            max_credits=_tighter_credits(base.max_credits, overrides.max_credits),
        )
        if base.strength is not None:
            requirement = replace(requirement, strength=shift_level(base.strength, overrides.level_delta))
        # LEADER EXCLUSION (pure, no I/O): resolve who would lead, then exclude
        # exactly that model — once for ``exclude_leader``, ``exclude_leaders``
        # times for a deeper rung (each pass drops the leader of what remains).
        # If a pass raises ModelUnavailable it propagates immediately — there is
        # no leader left to exclude and the deciding pass never runs.
        for _ in range(max(int(overrides.exclude_leader), overrides.exclude_leaders)):
            leader = _select_audited(
                requirement, snap, route_audit, route_id, funded_policy=funded_policy
            ).candidates[0].model_ref.model_id
            requirement = replace(
                requirement, exclude_models=requirement.exclude_models | {leader}
            )
    chain = _select_audited(requirement, snap, route_audit, route_id, funded_policy=funded_policy)   # THE decision
    return requirement, chain


def free_peer_ids(
    profile: str,
    *,
    exclude_models: frozenset[str] = frozenset(),
    overrides: RequirementOverrides | None = None,
    snapshot: RuntimeSnapshot | None = None,
) -> tuple[str, ...]:
    """The model ids the selector would offer ``profile`` with paid admission OFF
    and ``exclude_models`` prohibited — i.e. the verified-FREE candidates a
    request-local retry could still use, in chain order. ``()`` when there are
    none (including a paid-only rung, where ``require_paid`` with paid off
    admits nothing).

    A pure preview over the same :func:`resolve_chain` the real call uses; no
    model is contacted. "Free" here is the snapshot's priced fact (unknown price
    is never free), never a hardcoded allowlist.
    """
    base = overrides if overrides is not None else RequirementOverrides()
    free_only = replace(
        base, allow_paid=False, exclude_models=base.exclude_models | frozenset(exclude_models)
    )
    try:
        _, chain = resolve_chain(
            [], profile=profile, max_tokens=1, overrides=free_only, snapshot=snapshot
        )
    except ModelUnavailable:
        return ()
    return tuple(c.model_ref.model_id for c in chain.candidates)


def route_chat(
    messages: Iterable[ChatMessage],
    *,
    profile: str = "standard_generation",
    caller_model: str | None = None,
    max_tokens: int,
    temperature: float | None = None,
    deadline_s: float | None = None,
    allow_paid: bool | None = None,
    independence_against: IndependenceBaseline | None = None,
    retries: int = 3,
    backend_factory: Callable[[str], BaseBackend] = make_backend,
    snapshot: RuntimeSnapshot | None = None,
    ledger_repo: Path | None = None,
    ledger_config: LedgerConfig | None = None,
    overrides: RequirementOverrides | None = None,
    reservation_authority: ReservationAuthority | None = None,
    route_audit: RouteAudit | None = None,
    prompt_digest: str | None = None,
    context_digest: str | None = None,
    route_id: str | None = None,
    funded_ledger_config: LedgerConfig | None = None,
    funded_policy: FundedPolicy | None = None,
) -> ChatResponse:
    """Route one chat call through select()→execute() and return its response.

    ``caller_model`` is the model the call site pinned (used ONLY to promote it to
    the front when ``select`` kept it — see :func:`_promote_primary`); it is NOT a
    fallback chain and NEVER a resurrection. ``snapshot`` is an injection seam
    (tests / an owner above the per-call router); when ``None`` the bounded cache
    acquires the real one. Raises :class:`ModelUnavailable` (fail closed) when
    ``select`` finds no eligible candidate, ``ChainExhausted`` when the chain runs
    and none succeeds, re-raises a request-level permanent refusal unchanged, and
    ``ValueError`` on the fail-fast budget check (also raised when both the
    standalone ``allow_paid`` param AND ``overrides.allow_paid`` are supplied
    non-None — spec 026 slice 6, no silent precedence). ``overrides`` composes ON
    TOP of the named profile's base requirement (never replaces it): ``exclude_models``
    unions, ``max_credits`` tightens, ``require_paid`` ORs; ``overrides.allow_paid``
    (when set) wins over both the standalone param and the snapshot's opt-in.

    ``reservation_authority`` and ``route_audit`` (spec 025) are OPTIONAL hooks
    forwarded straight to :func:`execute`. Both default ``None`` — a no-op, so
    behavior is byte-for-byte unchanged when the lane does not inject them.
    ``route_audit``, when given, additionally observes THIS function directly: a
    ``select`` call that raises ``ModelUnavailable`` emits ``SelectionFailure``
    (then re-raises unchanged — the reroute logic that catches it is a later
    slice), and the final resolved chain emits ``ChainResolved`` before dispatch.
    A single ``route_id`` is threaded through both events plus :func:`execute`'s
    own outbox (F1), so the lane can correlate every event this ONE logical call
    produced. It defaults to a fresh ``uuid.uuid4().hex`` when not supplied; a
    caller MAY inject a durable id instead (spec 025 slice 1 — a retried logical
    invocation replays the identical event ids rather than minting new ones).
    ``prompt_digest`` / ``context_digest`` default to a digest of the actual
    routed ``messages`` (via :func:`messages_digest`) when not supplied —
    ``ChainResolved`` carries them (with the requirement/snapshot digests + full
    provenance + the winning candidates' ``ModelRef``s) so the lane can
    reconstruct an ``InvocationIdentity`` without re-deriving it (F2). Both digests
    are computed ONLY when ``route_audit`` is given — the default no-hook path
    computes neither, so a multimodal ``content`` payload never has to survive a
    digest projection it does not need.

    **Additional raises when the spec-025 hooks are engaged (distinct retry
    semantics — do NOT collapse either into an ordinary transient backend
    failure).** ``RouteAuditError`` propagates from :func:`execute` (or from the
    ``SelectionFailure``/``ChainResolved`` emits here) when the MANDATORY
    ``route_audit`` sink fails: it is ROUTE-FATAL — the logical call is aborted
    without silently changing which model ran, and because it is NOT a
    ``ModelUnavailable`` it never triggers a reroute. ``RouteReplayError``
    propagates when this ``(route_id, candidate)`` already crossed the atomic
    dispatch-claim boundary (a retried/concurrent replay): the backend was NOT
    re-invoked and any paid reservation is RETAINED by the original dispatch. It
    MUST NOT be retried as a transient backend failure — reconcile from durable
    dispatch state (an unresolved ``dispatch_started`` → ``dispatch_unknown``),
    never re-dispatch (FR-033a).

    **Funded (Hugging Face) candidates (spec 027).** ``funded_policy`` is forwarded
    to :func:`resolve_chain` (``None`` → ``FUNDED_POLICY``); ``funded_ledger_config``
    to :func:`execute` (``None`` → the production funded ledger from the env, failing
    closed without its anchor). The snapshot's funded guard prices each funded hold,
    which needs neither ``allow_paid`` nor the paid opt-in; an exhausted allowance
    skips the funded candidates (outage path, never a human escalation).
    """
    # deterministic-no-llm bypasses snapshot / select / execute ENTIRELY: a no-llm
    # agent that reached the model layer is a programming error → fail fast before
    # touching the mechanism (US5 AC3, layer 2). Registry dispatch (graph.py) is
    # layer 1 and must never let such an agent get here in the first place.
    if profile == DETERMINISTIC_NO_LLM or caller_model == DETERMINISTIC_NO_LLM:
        raise ValueError(
            "route_chat called with the 'deterministic-no-llm' sentinel — a no-LLM "
            "agent must never reach model selection/execution"
        )

    route_id = route_id or uuid.uuid4().hex
    msg_list = list(messages)
    # Production ledger source (review finding 1): the reservation ledger lives on a
    # protected ref in the MAIN repo (bootstrapped at repo_root() by `cli` /
    # infra/credit-ledger-ops.md), so a routed PAID candidate can open an
    # authoritative reservation instead of being skipped with "no ledger configured".
    # Default to it when the caller doesn't inject one; tests pass an explicit
    # ledger_repo (e.g. a tmp git ledger) as the injection seam. Free-only chains
    # never read it (execute touches a ledger ONLY when a paid or funded candidate
    # exists; funded holds live on their own ref, refs/llmxive/funded-ledger),
    # and execute still fails CLOSED on an unbootstrapped anchor.
    if ledger_repo is None:
        from llmxive.config import repo_root

        ledger_repo = repo_root()
    # Acquired here (not only inside resolve_chain) so the SAME snapshot's funded
    # guard prices any funded hold execute opens.
    snap = snapshot if snapshot is not None else _acquire_snapshot()
    requirement, chain = resolve_chain(
        msg_list,
        profile=profile,
        max_tokens=max_tokens,
        allow_paid=allow_paid,
        independence_against=independence_against,
        snapshot=snap,
        overrides=overrides,
        route_audit=route_audit,
        route_id=route_id,
        funded_policy=funded_policy,
    )
    chain = _promote_primary(chain, caller_model)

    # ChainResolved (spec 025): emitted once, after the final decision, before any
    # dispatch, via emit_audit (F4) — a sink failure here is pre-dispatch and
    # route-fatal, so it is normalized to RouteAuditError and propagates. The
    # prompt/context digests are computed ONLY inside this branch (maintainer
    # review finding #1): the default no-hook path must never touch
    # ``messages_digest`` at all, so a multimodal ``content`` never needs to
    # survive a digest projection it does not need.
    if route_audit is not None:
        winning_refs: tuple[ModelRef, ...] = tuple(c.model_ref for c in chain.candidates)
        pdig = prompt_digest if prompt_digest is not None else messages_digest(msg_list)
        cdig = context_digest if context_digest is not None else messages_digest(msg_list)
        emit_audit(route_audit, ChainResolved(
            route_id=route_id,
            requirement_digest=_requirement_digest(requirement),
            prompt_digest=pdig,
            context_digest=cdig,
            snapshot_digest=chain.snapshot_digest,
            snapshot_provenance=chain.snapshot_provenance,
            selection_policy_version=chain.selection_policy_version,
            resolved_at=chain.resolved_at.isoformat(),
            explanation=chain.explanation,
            candidates=winning_refs,
        ))

    options = ExecutionOptions(
        max_tokens=max_tokens, temperature=temperature, deadline_s=deadline_s
    )
    result = execute(
        chain,
        msg_list,
        options=options,
        backend_factory=backend_factory,
        retries=retries,
        ledger_repo=ledger_repo,
        ledger_config=ledger_config,
        route_id=route_id,
        reservation_authority=reservation_authority,
        route_audit=route_audit,
        funded_ledger_config=funded_ledger_config,
        funded_guard=snap.funded,
    )
    return result.response
