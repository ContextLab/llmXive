"""Requirement-driven model selection (spec 026).

Strict separation of concerns:

    snap     = runtime_snapshot(...)          # acquisition — networked, fallible
    decision = select(requirement, snap)      # decision — pure, deterministic
    response = execute(decision.chain, ...)    # execution — retries/breakers/credits

This package is the SINGLE source of truth for "which model does this call use"
(Constitution I). See ``specs/026-model-selection-consolidation/spec.md``.

Slice 1 (this commit) provides the typed contracts + ``runtime_snapshot``.
Later slices add the pure selector, the execution adapter + credit reservation
ledger, the independence contract, and the call-site migrations.
"""

from __future__ import annotations

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
)

__all__ = [
    "CallBudget",
    "Candidate",
    "CreditGuardSnapshot",
    "ExecutionOptions",
    "IndependenceBaseline",
    "ModelChain",
    "ModelRef",
    "ModelRequirement",
    "ModelUnavailable",
    "RuntimeSnapshot",
    "runtime_snapshot",
]


def __getattr__(name: str):  # lazy: keep import of the networked layer optional
    if name == "runtime_snapshot":
        from llmxive.model_selection.snapshot import runtime_snapshot

        return runtime_snapshot
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
