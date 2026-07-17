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

from llmxive.model_selection.policy import (
    CAPABILITY_POLICY,
    SELECTION_POLICY_VERSION,
    CapabilityPolicy,
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
    CallBudget,
    Candidate,
    CreditGuardSnapshot,
    ExecutionOptions,
    IndependenceBaseline,
    ModelChain,
    ModelRef,
    ModelRequirement,
    ModelUnavailable,
    RuntimeSnapshot,
    SnapshotProvenance,
)

__all__ = [
    "CAPABILITY_POLICY",
    "PROFILES",
    "SELECTION_POLICY_VERSION",
    "CallBudget",
    "Candidate",
    "CapabilityPolicy",
    "CreditGuardSnapshot",
    "ExecutionOptions",
    "IndependenceBaseline",
    "ModelChain",
    "ModelRef",
    "ModelRequirement",
    "ModelUnavailable",
    "PolicyEntry",
    "RequirementProfile",
    "RuntimeSnapshot",
    "SnapshotProvenance",
    "build_requirement",
    "profile",
    "runtime_snapshot",
    "select",
]


def __getattr__(name: str):  # lazy: keep import of the networked layer optional
    if name == "runtime_snapshot":
        from llmxive.model_selection.snapshot import runtime_snapshot

        return runtime_snapshot
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
