"""What every lane LLM call needs: the mandatory hooks and durable route admission.

Three things are REQUIRED on a lane call and none of them has a ``None`` default — there is
no unaudited call (FR-033a), no unbudgeted call (FR-033), and no unadmitted call (Policy
Contract line 313). The context carries all three plus the deterministic route-id
derivation that makes a replayed call recognizable as a replay.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from llmxive.git_event_log import GitLogError
from llmxive.model_selection.attempt_hooks import (
    ReservationAuthority,
    RouteAudit,
    RouteAuditError,
)
from llmxive.self_improvement.call_ledger import LaneCallCeilingExceeded, LaneCallLedger
from llmxive.self_improvement.events import Event, derive_event_id
from llmxive.self_improvement.lane_log import (
    LaneContention,
    LaneLogConfig,
    LaneRevisionConflict,
    append,
)

#: Policy Contract line 312: the implementer regenerates at most once.
IMPL_REGEN_RETRIES = 1

#: FR-002's one sanctioned reroute, mirrored from the event validator that enforces it.
_PRIMARY_PROFILE = "independent_review"
_FALLBACK_PROFILE = "deep_review"
_RELAXED_CONSTRAINTS = ["family_independence", "snapshot_freshness"]


def proposal_call_ceiling(panel_size: int, max_rounds: int) -> int:
    """``4N + R(2N + 2)`` — the proposal stage's COMPONENT of the Attempt ceiling.

    The ``2N`` term is R1 (each reviewer: a normal call plus at most one action-item
    resubmit), doubled to ``4N`` because every reviewer call may reroute. The ``+2`` is the
    reviser's at-most-two attempts per round and is NOT doubled — the producer has no
    independence constraint, so it never reroutes.

    A COMPONENT, not a limit: see :func:`attempt_call_ceiling`."""
    return 4 * panel_size + max_rounds * (2 * panel_size + 2)


def patch_call_ceiling(panel_size: int, max_rounds: int) -> int:
    """``2N + R(N + 2)`` — the patch stage's COMPONENT. Single-route (the pre-merge gate
    fails closed rather than rerouting), so no term is doubled."""
    return 2 * panel_size + max_rounds * (panel_size + 2)


def attempt_call_ceiling(*, proposal_panel: int, patch_panel: int, max_rounds: int,
                         impl_regen_retries: int = IMPL_REGEN_RETRIES) -> int:
    """The WHOLE Policy Contract line-313 expression: proposer + implementer(1 + regens) +
    the proposal component + the patch component.

    **This is the only value that may be written into ``AttemptConfigured``.** Binding a
    stage component instead is two defects at once, because that record is IMMUTABLE for the
    Attempt: the proposer's and implementer's calls would eat the proposal panel's
    allowance, and a later attempt to bind the real whole-Attempt figure would be refused by
    ``AttemptConfigMismatch`` because the smaller number got there first."""
    return (1 + (1 + impl_regen_retries)
            + proposal_call_ceiling(proposal_panel, max_rounds)
            + patch_call_ceiling(patch_panel, max_rounds))


@dataclass(frozen=True)
class LaneRouteContext:
    """The three mandatory hooks plus durable route admission for one Attempt.

    Frozen because it holds no SPEND state — the ceiling and the credit budget both live in
    the append-only log, so a restart cannot hand a fresh allowance to a new context. The
    one piece of process-local state is ``_repeats``, and it deliberately is not spend: it
    distinguishes an in-process re-issue of an identical call from a restart replay (see
    :meth:`next_operation_id`)."""

    repo: Path
    problem_id: str
    attempt_id: str
    actor: str
    clock: Callable[[], str]
    route_audit: RouteAudit
    reservation_authority: ReservationAuthority
    call_ledger: LaneCallLedger
    config: LaneLogConfig | None = None
    _repeats: dict[str, int] = field(default_factory=dict, repr=False, compare=False)

    def next_operation_id(self, base: str) -> str:
        """Resolve a caller's content-derived ``base`` into THIS call's operation id: the
        first use in a process returns it unchanged, each in-process repeat appends ``#1``,
        ``#2``, …

        Not decoration — it is what keeps the durable claim correct in both directions. A
        pure content digest gives the two properties that matter (distinct logical calls
        differ; a RESTART re-derives the same id, so the dispatch gate sees a replay), but
        two callers legitimately re-issue an IDENTICAL call inside one process: the engine
        re-invokes ``revise()`` with byte-identical arguments after a malformed reply, and a
        round with no artifact change can produce a rereview prompt identical to the
        previous round's. Those are new logical calls that already dispatched once, so they
        need new ids and their own ceiling charge — the ``+2`` per round exists for exactly
        the reviser's second attempt. Without the sequencer they would replay the first
        claim, receive the first ``route_id``, and be REFUSED at the dispatch gate."""
        seen = self._repeats.get(base, 0)
        self._repeats[base] = seen + 1
        return base if seen == 0 else f"{base}#{seen}"

    def claim_route(self, *, operation_id: str, leg: str = "primary") -> str:
        """CAS-admit ONE logical ``route_chat`` invocation against the ATTEMPT's ceiling and
        return its retry-stable ``route_id``. Raises :class:`LaneCallCeilingExceeded` when
        the Attempt is spent.

        Every lane call obtains its route id here, so admission cannot be bypassed, and the
        id is derived rather than minted: a restart, a retry on another runner, or a
        duplicate worker all re-present the SAME id, which is what lets the dispatch gate
        recognize the replay instead of dispatching a second time."""
        return self.call_ledger.claim(operation_id=operation_id, leg=leg)

    def calls_used(self) -> int:
        """The DURABLE count, from the log — never a local tally."""
        return self.call_ledger.calls_used()

    def record_reroute(self, *, operation_id: str, lens: str, primary_route_id: str,
                       fallback_route_id: str, exception_type: str, message: str) -> None:
        """Persist the explicit ``ReviewRerouted`` degradation record.

        **A persistence failure here is route-fatal.** ``lane_log.append`` raises
        ``GitLogError``/``LaneRevisionConflict``/``LaneContention``, none of which the lane
        entry point classifies — they would escape raw and bypass the contract that a
        mandatory-provenance failure is fatal (FR-033a). Every one is normalized to
        ``RouteAuditError`` so the caller can refuse to dispatch the fallback: a review that
        ran on the relaxed profile with no durable record would be claiming an independence
        it never had.

        Idempotent — the event id is derived from the primary leg, so re-recording the same
        reroute is a no-op rather than a second degradation record."""
        event = Event(
            event_id=derive_event_id(self.problem_id, f"reroute\x00{primary_route_id}"),
            event_type="ReviewRerouted", problem_id=self.problem_id, actor=self.actor,
            payload={
                "operation_id": operation_id, "lens": lens,
                "primary_profile": _PRIMARY_PROFILE, "fallback_profile": _FALLBACK_PROFILE,
                "primary_route_id": primary_route_id, "fallback_route_id": fallback_route_id,
                "primary_failure": {"exception_type": exception_type, "message": message},
                "relaxed_constraints": list(_RELAXED_CONSTRAINTS),
            },
            timestamp=self.clock(), attempt_id=self.attempt_id,
        )
        try:
            append(self.repo, event, expected_revision=None, config=self.config)
        except (GitLogError, LaneRevisionConflict, LaneContention, ValueError) as exc:
            raise RouteAuditError(
                f"the ReviewRerouted record for operation {operation_id!r} could not be made "
                f"durable ({type(exc).__name__}: {exc}) — the fallback leg must not run"
            ) from exc


__all__ = [
    "IMPL_REGEN_RETRIES",
    "LaneCallCeilingExceeded",
    "LaneRouteContext",
    "attempt_call_ceiling",
    "patch_call_ceiling",
    "proposal_call_ceiling",
]
