"""Durable execution-failure classification (issue #1139, P1-2 / anti-pattern 4).

The execution stage already recognizes *compute-environment* (GPU/CUDA/OOM),
*data-unreachable* (renamed/gated HF dataset, no network) and *fabrication*
failures — but it threw that classification away: ``execution_status`` persisted
only free-text ``reason``/``failures`` strings, and ``_write_execution_replan_feedback``
took no class argument and always emitted the same "make it CPU-tractable" advice.
Downstream (re-plan feedback, terminal routing, dashboards) could only re-parse
strings, and a GPU-only method, an unreachable dataset, and a genuine code bug all
collapsed into one generic message and one ``VALIDATOR_REJECTED`` terminal.

This module is the SINGLE home for the failure taxonomy. The stage classifies
once (reusing its signature matchers) into a :class:`FailureClass`, persists the
enum value, and every downstream consumer branches on the durable class instead
of re-deriving it from strings.
"""

from __future__ import annotations

from enum import StrEnum


class FailureClass(StrEnum):
    """Why an execution attempt failed. ``str``-valued so it round-trips through
    the JSON state files verbatim."""

    #: GPU/CUDA/8-bit/OOM — the free CPU CI cannot satisfy it. Re-scope to CPU
    #: (smaller model, sampled data) or offload to GPU; NOT an in-place code fix.
    COMPUTE_ENV = "compute_env"
    #: External data source unreachable (renamed/removed/gated HF dataset, no
    #: network). Fix = a verified real source, never synthetic substitution.
    DATA_UNREACHABLE = "data_unreachable"
    #: The run fabricated inputs/results (random/hardcoded/"simulated metrics").
    #: Fix = obtain a real source + compute real results.
    FABRICATION = "fabrication"
    #: A genuine, implementer-fixable code bug (import error, traceback, wrong
    #: path) — the normal fix-loop can repair it in place.
    EXECUTION_BUG = "execution_bug"
    #: The run produced no runnable failure signature we recognize (empty/other).
    UNKNOWN = "unknown"

    @classmethod
    def from_signals(
        cls,
        *,
        compute_infra: bool,
        data_unavailable: bool,
        fabrication: bool,
        hollow: bool,
        has_command_failures: bool,
    ) -> FailureClass:
        """Map already-computed failure signals to a single class.

        Priority order reflects what the re-plan must address first: a
        compute-environment wall dominates (nothing else can run until it is
        re-scoped); then a missing real data source (fabrication/hollow/no-source
        all mean "needs a verified source"); then an ordinary code bug.
        """
        if compute_infra:
            return cls.COMPUTE_ENV
        if data_unavailable:
            return cls.DATA_UNREACHABLE
        if fabrication or hollow:
            return cls.FABRICATION
        if has_command_failures:
            return cls.EXECUTION_BUG
        return cls.UNKNOWN


#: Class-specific guidance the re-plan report threads to the planner. Keyed by
#: the durable :class:`FailureClass` value so the message matches the real cause
#: instead of a one-size-fits-all "make it CPU-tractable" line.
REPLAN_GUIDANCE: dict[FailureClass, str] = {
    FailureClass.COMPUTE_ENV: (
        "The method requires GPU/accelerated compute the free CI runner lacks. "
        "Re-scope it to run on CPU — a smaller model, fewer parameters, a sampled "
        "subset, or a classical baseline that answers the same question — OR keep "
        "the GPU step behind the Kaggle offload path. Do NOT keep the CUDA/8-bit "
        "requirement in the CPU code path."
    ),
    FailureClass.DATA_UNREACHABLE: (
        "The external data source could not be reached/loaded (renamed, removed, "
        "gated, or offline). Switch to a VERIFIED, programmatically reachable real "
        "source (current canonical id, a public mirror, or a different genuinely "
        "public dataset that supports the same analysis). NEVER fabricate or "
        "substitute synthetic data — a verified source is discovered and injected "
        "for you; build the analysis around it."
    ),
    FailureClass.FABRICATION: (
        "The run fabricated its inputs or results (random/hardcoded values or "
        "'simulated metrics'). Replace them with a real, verified data source and "
        "compute measured results from it. Fabricated numbers are rejected at the "
        "execution gate."
    ),
    FailureClass.EXECUTION_BUG: (
        "The analysis failed with a code error. Fix the failing command(s) shown "
        "above in place — correct the import/path/logic — keeping the same method "
        "and real data."
    ),
    FailureClass.UNKNOWN: (
        "The implementation approach needs adjustment given the errors above — "
        "re-plan with a design that avoids them, keeping what worked."
    ),
}
