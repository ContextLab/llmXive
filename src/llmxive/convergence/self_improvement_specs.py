"""The self-improvement lane's ``run_convergence`` ReviewSpec builders (FR-019,
Constitution VI). Slice 1B delivers the PROPOSAL review (`self_improvement_proposal`)
with the FR-002 two-attempt reroute wired into every lens and the lane's mandatory
routing context shared by the whole panel AND the reviser.

The PATCH review (`self_improvement_patch`) reuses the same ``LLMReviewer`` mechanism
with ``fallback_profile=None`` (required independence, FAIL CLOSED) and is a later slice.

``run_convergence`` itself is unchanged: independence is wired at reviewer CONSTRUCTION,
before the panel reaches the engine (spec line 283).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from llmxive.convergence.engine import run_convergence
from llmxive.convergence.lane_reviser import LaneProposalReviser
from llmxive.convergence.llm_reviewer import LLMReviewer
from llmxive.convergence.types import ConvergenceResult, ReviewSpec, Severity
from llmxive.model_selection.attempt_hooks import RouteAuditError, RouteReplayError
from llmxive.model_selection.types import IndependenceBaseline
from llmxive.self_improvement.invocation_identity import (
    InvocationIdentity,
    InvocationIdentityError,
    build_invocation_identity,
)
from llmxive.self_improvement.lane_log import read
from llmxive.self_improvement.route_context import (
    LaneCallCeilingExceeded,
    LaneRouteContext,
    attempt_call_ceiling,
)

PROPOSAL_STAGE = "self_improvement_proposal"
#: The proposal lens set (Self-improvement ReviewSpec table, spec line 278).
PROPOSAL_LENSES = (
    "worthwhile-improvement", "diagnosis-correctness", "tractability",
    "testability", "blast-radius-sanity",
)
#: The PATCH lens set (same table, line 278). The patch `ReviewSpec` BUILDER is a later
#: slice; the lens NAMES are declared now because the Attempt ceiling below needs N_q and
#: `AttemptConfigured` binds that ceiling IMMUTABLY (round-5 F1). The later slice MUST
#: build its panel from this tuple — if it uses a different size, the ceiling bound for
#: every Attempt today is wrong for the Attempt it governs.
PATCH_LENSES = (
    "implementation-correctness", "safety-blast-radius", "test-adequacy",
    "spec-adherence", "security-of-diff",
)
# `safety-blast-radius` is the spec's identifier as of rev 16. Through rev 15 the table
# read `safety/blast-radius`, which cannot be a lens name: the name is used verbatim as a
# ReviewSpec reviewer name AND as a prompt filename segment (`panel_<prefix>_<lens>.md`),
# so the `/` would create a subdirectory. Amended rather than mapped, so there is ONE
# identifier — see spec 025 rev 16, "Lens names are path-safe MACHINE IDENTIFIERS".
PROPOSAL_MAX_ROUNDS = 3          # table line 281 (the engine default)
#: A proposal the panel does not accept is REJECTED pre-claim (transition table line 245).
PROPOSAL_KICKBACK_STAGE = "rejected"

#: THE per-Attempt LLM-call ceiling (Policy Contract line 313) — the value bound into
#: `AttemptConfigured`. It spans EVERY stage of the Attempt, not just this panel: a stage
#: component would starve the other stages and, because the record is immutable, would
#: permanently lock out the real figure. == 90 for the canonical 5-lens panels at R=3.
LANE_ATTEMPT_CEILING = attempt_call_ceiling(
    proposal_panel=len(PROPOSAL_LENSES),
    patch_panel=len(PATCH_LENSES),
    max_rounds=PROPOSAL_MAX_ROUNDS,
)

#: What the SSoT summarizer must preserve when an oversized artifact is reduced
#: (``engine._maybe_reduce`` passes this straight through as the summarization goal).
#: It is an INSTRUCTION, not a stage name: these three things are exactly what the five
#: lenses read, so losing any of them to a summary would leave the panel judging a
#: proposal it can no longer check.
PROPOSAL_OVERFLOW_GOAL = (
    "preserve the causal claim, every cited evidence reference, and the "
    "file/test list verbatim"
)


def _kickback_routing() -> dict[Severity, str]:
    """Every severity routes to ``rejected``.

    The doc stages route different severities to different prior stages because they have
    somewhere lesser to go — a writing-class concern re-clarifies in place. A proposal has
    no such gradation: it is pre-claim work with nothing behind it, so ANY unresolved
    concern at the cap means this proposal is not pursued (transition table line 245).
    Every member is listed rather than relying on ``_nearest_routing``'s fallback, because
    "all severities are the same outcome here" is the actual policy and should read that
    way.
    """
    return dict.fromkeys(Severity, PROPOSAL_KICKBACK_STAGE)


def build_proposal_review_spec(
    *,
    backend: object,
    repo_root: Path,
    proposer_baseline: IndependenceBaseline,
    route_context: LaneRouteContext,       # REQUIRED (F3) — no unaudited lane panel
    artifact_key: str = "proposal.md",
) -> ReviewSpec:
    """The `self_improvement_proposal` panel: five lenses, each family-independent from
    the proposer with a sanctioned degrade, plus the lane reviser — all sharing ONE
    routing context so every call lands on the same Attempt's audit stream and budget."""
    reviewers = [
        LLMReviewer(
            lens=lens, stage=PROPOSAL_STAGE, backend=backend, repo_root=repo_root,
            profile="independent_review",       # attempt 1: required family independence
            fallback_profile="deep_review",     # attempt 2 on ModelUnavailable: degrade
            independence_against=proposer_baseline,
            route_context=route_context,
        )
        for lens in PROPOSAL_LENSES
    ]
    reviser = LaneProposalReviser(
        backend=backend, route_context=route_context, artifact_key=artifact_key,
    )
    return ReviewSpec(
        stage=PROPOSAL_STAGE,
        artifacts=[artifact_key],
        reviewers=reviewers,
        reviser=reviser,
        kickback_routing=_kickback_routing(),
        overflow_goal=PROPOSAL_OVERFLOW_GOAL,
        advance_stage=None,                     # the lifecycle transition is a later slice
        max_rounds=PROPOSAL_MAX_ROUNDS,
    )


@dataclass(frozen=True)
class ProposalReviewOutcome:
    """What the lane learned from one proposal review.

    ``failed_closed`` distinguishes "the panel reached a verdict" from "the lane refused to
    produce one". Both are honest outcomes; only the first carries a ``result``.

    The Attempt-lifecycle write (``proposal_verified`` / ``rejected`` / ``*_failed``) is
    deliberately NOT performed here — Slice 1A scoped Attempt-failure semantics out. This
    reports the outcome; a later slice consumes it.
    """

    result: ConvergenceResult | None
    failed_closed: bool
    failure_kind: str      # "" | "audit_fatal" | "replay" | "ceiling"
    failure_detail: str
    producer_identity: InvocationIdentity | None = None


def run_proposal_review(
    *,
    backend: object,
    repo_root: Path,
    proposer_baseline: IndependenceBaseline,
    route_context: LaneRouteContext,
    artifacts: dict[str, str],
    artifact_key: str = "proposal.md",
    producer: str | None = None,
    proposer_route_id: str | None = None,
    constitution: str | None = None,
    advisory: list[str] | None = None,
) -> ProposalReviewOutcome:
    """Run the proposal panel through the SHARED, UNMODIFIED ``run_convergence`` and own
    the lane's fail-closed classification. The engine's ``_abort_provenance``
    (``engine.py:433-448``) catches only ``BackendUnavailable``/``TransientBackendError``,
    so the three lane-fatal conditions are classified here instead of propagating raw.

    ``producer`` is forwarded to the engine's self-review exclusion. Spec 025 line 150 is
    explicit that this is NECESSARY-NOT-SUFFICIENT: ``engine.py:421`` drops reviewers whose
    LENS NAME equals the string, so it excludes nothing unless a lens is literally named
    that. Real independence comes from the family constraint on each reviewer (Task 4) —
    never treat this argument as the safeguard.

    ``proposer_route_id`` resolves the proposer's full ``InvocationIdentity`` from the same
    lane log (F7): an ``IndependenceBaseline`` records which families to avoid, not who
    actually authored the proposal. An id that does not resolve raises — a proposal whose
    author cannot be identified must not be reviewed as though it could. It is resolved
    BEFORE the panel is built, so that refusal costs nothing.

    ``BackendUnavailable``/``TransientBackendError`` are deliberately NOT caught: they are
    the engine's existing clean abort, already recorded via ``on_abort``. On the lane that
    abort ENDS the Attempt rather than parking it — a resumed process re-derives the same
    operation ids, so ``claim_route`` hands back the ORIGINAL route ids and the dispatch
    gate correctly refuses them as replays. Any retry is a NEW Attempt with a new
    ``attempt_id`` and a disjoint route-id space (spec 025 line 220).
    """
    producer_identity = None
    if proposer_route_id is not None:
        producer_identity = build_invocation_identity(
            read(route_context.repo, route_context.problem_id, config=route_context.config),
            route_id=proposer_route_id, attempt_id=route_context.attempt_id,
        )
        if producer_identity is None:
            raise InvocationIdentityError(
                f"proposer route {proposer_route_id!r} has no completed dispatch in the lane "
                "log — refusing to review a proposal with no durable author provenance"
            )
    spec = build_proposal_review_spec(
        backend=backend, repo_root=repo_root, proposer_baseline=proposer_baseline,
        route_context=route_context, artifact_key=artifact_key,
    )
    try:
        result = run_convergence(spec, artifacts, producer=producer,
                                 constitution=constitution, advisory=advisory)
    except RouteAuditError as exc:
        # FR-033a: route-fatal. NOT a ModelUnavailable → never reroutes, never advances.
        return ProposalReviewOutcome(None, True, "audit_fatal", str(exc), producer_identity)
    except RouteReplayError as exc:
        # FR-033a route-replay disposition: a failed logical call — reservation stays
        # retained, reconcile from durable dispatch state, NEVER retry as transient.
        return ProposalReviewOutcome(None, True, "replay", str(exc), producer_identity)
    except LaneCallCeilingExceeded as exc:
        return ProposalReviewOutcome(None, True, "ceiling", str(exc), producer_identity)
    return ProposalReviewOutcome(result, False, "", "", producer_identity)


__all__ = [
    "LANE_ATTEMPT_CEILING",
    "PATCH_LENSES",
    "PROPOSAL_KICKBACK_STAGE",
    "PROPOSAL_LENSES",
    "PROPOSAL_MAX_ROUNDS",
    "PROPOSAL_OVERFLOW_GOAL",
    "PROPOSAL_STAGE",
    "ProposalReviewOutcome",
    "build_proposal_review_spec",
    "run_proposal_review",
]
