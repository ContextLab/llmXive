"""Requirement-driven model selection (spec 026).

Strict separation of concerns:

    snap     = runtime_snapshot(...)          # acquisition — networked, fallible
    decision = select(requirement, snap)      # decision — pure, deterministic
    response = execute(decision.chain, ...)    # execution — retries/breakers/credits

This package is the SINGLE source of truth for "which model does this call use"
(Constitution I). See ``specs/026-model-selection-consolidation/spec.md``.

Slice 1 provides the typed contracts + ``runtime_snapshot``. Slice 2 (this
commit) adds the pure ``select`` selector, the versioned ``CapabilityPolicy``,
and the named requirement ``profiles``. Later slices add the execution adapter +
credit reservation ledger, the full independence integration, and the call-site
migrations.
"""

from __future__ import annotations

from llmxive.model_selection.attempt_hooks import (
    CandidateOutcome,
    ChainResolved,
    DispatchCompleted,
    DispatchStarted,
    DispatchUnknown,
    ReservationAuthority,
    ReservationOpened,
    RouteAudit,
    RouteAuditError,
    RouteReplayError,
    SelectionFailure,
    emit_audit,
)
from llmxive.model_selection.execute import ChainExhausted, ExecutionResult, execute
from llmxive.model_selection.policy import (
    CAPABILITY_POLICY,
    FUNDED_POLICY,
    SELECTION_POLICY_VERSION,
    CapabilityPolicy,
    FundedPolicy,
    PolicyEntry,
)
from llmxive.model_selection.profiles import (
    PROFILES,
    RequirementProfile,
    build_requirement,
    profile,
)
from llmxive.model_selection.select import select
from llmxive.model_selection.types import (
    FUNDED_BACKENDS,
    STRENGTH_LEVELS,
    ArenaScore,
    CallBudget,
    Candidate,
    CostClass,
    CreditGuardSnapshot,
    ExecutionOptions,
    FundedGuardSnapshot,
    IndependenceBaseline,
    IndependenceDim,
    ModelChain,
    ModelRef,
    ModelRequirement,
    ModelScores,
    ModelUnavailable,
    ObservedModel,
    RuntimeSnapshot,
    SnapshotProvenance,
    StrengthLevel,
    Track,
    cost_class_of,
    shift_level,
    worst_case_usd,
)

__all__ = [
    "CAPABILITY_POLICY",
    "FUNDED_BACKENDS",
    "FUNDED_POLICY",
    "PROFILES",
    "SELECTION_POLICY_VERSION",
    "STRENGTH_LEVELS",
    "ArenaScore",
    "CallBudget",
    "Candidate",
    "CandidateOutcome",
    "CapabilityPolicy",
    "ChainExhausted",
    "ChainResolved",
    "CostClass",
    "CreditGuardSnapshot",
    "DispatchCompleted",
    "DispatchStarted",
    "DispatchUnknown",
    "ExecutionOptions",
    "ExecutionResult",
    "FundedGuardSnapshot",
    "FundedPolicy",
    "IndependenceBaseline",
    "IndependenceDim",
    "ModelChain",
    "ModelRef",
    "ModelRequirement",
    "ModelScores",
    "ModelUnavailable",
    "ObservedModel",
    "PolicyEntry",
    "RequirementProfile",
    "ReservationAuthority",
    "ReservationOpened",
    "RouteAudit",
    "RouteAuditError",
    "RouteReplayError",
    "RuntimeSnapshot",
    "SelectionFailure",
    "SnapshotProvenance",
    "StrengthLevel",
    "Track",
    "build_requirement",
    "cost_class_of",
    "emit_audit",
    "execute",
    "profile",
    "route_chat",
    "runtime_snapshot",
    "select",
    "shift_level",
    "worst_case_usd",
]

def __getattr__(name: str):  # lazy: keep the networked snapshot layer optional
    if name == "runtime_snapshot":
        from llmxive.model_selection.snapshot import runtime_snapshot

        return runtime_snapshot
    if name == "route_chat":
        # Lazy for the SAME reason as runtime_snapshot: route.py imports the
        # networked snapshot layer at module scope, so eagerly exporting the
        # chokepoint here would defeat that optionality. ``from
        # llmxive.model_selection import route_chat`` resolves via PEP 562.
        from llmxive.model_selection.route import route_chat

        return route_chat
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
