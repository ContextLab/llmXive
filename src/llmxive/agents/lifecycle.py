"""Lifecycle stage machine (T027).

Skeleton: defines the 30+ stage enum (re-exported from types.Stage) and
the allowed-transition map. Per-story extensions (T056, T067, T094,
T100) populate the map; the Advancement-Evaluator Agent consults it.
"""

from __future__ import annotations

from collections.abc import Iterable

from llmxive.types import Stage

# Stage transition map: source stage -> set of allowed target stages.
# Populated incrementally as user stories are implemented; the
# Advancement-Evaluator refuses any transition not declared here.
ALLOWED_TRANSITIONS: dict[Stage, set[Stage]] = {
    # Idea-generation phase (T056 will add details for transitions through
    # this section; for now the structural skeleton is here).
    # Allow direct BRAINSTORMED → FLESH_OUT_COMPLETE when the FleshOut
    # agent finishes in one tick. The IN_PROGRESS intermediate is an
    # optional checkpoint for long-running flesh-out work.
    Stage.BRAINSTORMED: {
        Stage.FLESH_OUT_IN_PROGRESS, Stage.FLESH_OUT_COMPLETE,
        Stage.HUMAN_INPUT_NEEDED,
        # Spec 023 / FR-014: bounded idea-retry cap exhausted → honest
        # terminal (idea rejected to the backlog; never scheduled again).
        Stage.VALIDATOR_REJECTED,
    },
    Stage.FLESH_OUT_IN_PROGRESS: {
        Stage.FLESH_OUT_COMPLETE, Stage.HUMAN_INPUT_NEEDED,
        Stage.BRAINSTORMED,  # FR-014 constrained re-brainstorm
        Stage.VALIDATOR_REJECTED,  # FR-014 cap exhausted
    },
    Stage.FLESH_OUT_COMPLETE: {
        # spec 003 / D10: research_question_validator inserted between
        # flesh_out and project_initializer. The validator emits one of
        # three outcomes:
        #   validated         → VALIDATED → PROJECT_INITIALIZED
        #   validator_revise  → FLESH_OUT_IN_PROGRESS (re-flesh_out)
        #   validator_rejected → BRAINSTORMED (re-brainstorm, bounded by
        #                        the FR-014 idea-retry cap)
        Stage.VALIDATED,
        Stage.FLESH_OUT_IN_PROGRESS,  # validator_revise rollback
        Stage.HUMAN_INPUT_NEEDED,
        Stage.BRAINSTORMED,  # scope rejection or validator_rejected rolls back
        Stage.VALIDATOR_REJECTED,  # FR-014 cap exhausted → honest terminal
        # Legacy direct path retained for backward compat (e.g., a
        # flesh_out_complete project that pre-dates the validator stage).
        Stage.PROJECT_INITIALIZED,
    },
    Stage.VALIDATED: {Stage.PROJECT_INITIALIZED, Stage.HUMAN_INPUT_NEEDED},
    # Per-project research Spec Kit pipeline (US1):
    Stage.PROJECT_INITIALIZED: {Stage.SPECIFIED},
    # The CLARIFY_IN_PROGRESS / ANALYZE_IN_PROGRESS intermediates are
    # optional checkpoints used by long-running operations; the
    # Clarifier and Tasker may transition directly to the next stable
    # stage when they complete in one tick.
    # Spec 015 F-20 Part B: the spec convergence panel (run by the clarifier
    # at SPECIFIED) emits an adaptive kickback whose target is an earlier
    # content stage — project_initialized (re-specify) or flesh_out_in_progress
    # (idea-root cause). Both are valid backward transitions.
    Stage.SPECIFIED: {
        Stage.CLARIFY_IN_PROGRESS, Stage.CLARIFIED, Stage.HUMAN_INPUT_NEEDED,
        Stage.PROJECT_INITIALIZED, Stage.FLESH_OUT_IN_PROGRESS,
    },
    Stage.CLARIFY_IN_PROGRESS: {Stage.CLARIFIED, Stage.HUMAN_INPUT_NEEDED},
    # CLARIFIED -> CLARIFIED self-loop: the plan convergence panel (run by the
    # planner at CLARIFIED) kicks back to ``clarified`` for spec-gap concerns.
    # Spec 023 defect #14: kickback routes were one stage too far forward
    # (a kickback's to_stage names the stage WHOSE AGENT must re-run, and
    # the graph runs STAGE_TO_AGENT[stage] — so 'fix the spec' must route
    # to SPECIFIED, where the clarifier + spec panel run and the
    # SpecReviser can actually edit spec.md). CLARIFIED -> SPECIFIED is
    # the plan panel's spec-gap kickback.
    Stage.CLARIFIED: {
        Stage.PLANNED, Stage.CLARIFIED, Stage.SPECIFIED,
        Stage.HUMAN_INPUT_NEEDED,
    },
    # PLANNED -> PLANNED self-loop: the tasks convergence panel (run by the
    # tasker at PLANNED) kicks back to ``planned`` to re-task on a deeper
    # unresolved concern — exactly mirroring the CLARIFIED self-loop for the
    # plan panel. (A writing-only kickback routes forward to TASKED, already
    # allowed.) Without this self-loop edge a tasks-stage kickback would crash
    # run_one_step's is_valid_transition guard.
    Stage.PLANNED: {
        Stage.PLANNED, Stage.TASKED, Stage.HUMAN_INPUT_NEEDED,
        Stage.CLARIFIED,  # spec 023 defect #14: tasks panel plan-flaw kickback (planner re-runs at CLARIFIED)
    },
    # Spec 023 defect #22: the tasks convergence panel runs at BOTH planned
    # and tasked (the tasker drives analyze from tasked). Its plan-flaw
    # kickback (REQUIREMENT+ → "clarified", defect-#14 semantics) and its
    # cap escalation must therefore be reachable from TASKED as well —
    # without these edges every kickback from tasked burned a full panel
    # run then died on "invalid transition tasked -> clarified" (observed
    # live on PROJ-552).
    Stage.TASKED: {
        Stage.ANALYZE_IN_PROGRESS, Stage.ANALYZED,
        Stage.CLARIFIED, Stage.HUMAN_INPUT_NEEDED,
    },
    Stage.ANALYZE_IN_PROGRESS: {Stage.ANALYZED, Stage.HUMAN_INPUT_NEEDED},
    Stage.ANALYZED: {Stage.IN_PROGRESS},
    # IN_PROGRESS -> PLANNED: the execution fix-loop, having exhausted every
    # model tier without a clean run, RE-PLANS (re-derive the approach with a
    # deterministic report) instead of escalating to a human (autonomous
    # exhaustion handling). HUMAN_INPUT_NEEDED is retained only for unrelated
    # legacy markers — the execution path never routes there anymore.
    # VALIDATOR_REJECTED is the terminal for a project whose analysis cannot be
    # RUN here at all: it has exhausted every model tier AND every re-plan
    # (MAX_REPLAN_ROUNDS full ladders). Re-planning it again would be an unbounded
    # loop — which is exactly what it was, burning the worker matrix on a project
    # that can never produce a real result. Rejecting is the honest outcome, and it
    # is still autonomous (never HUMAN_INPUT_NEEDED).
    Stage.IN_PROGRESS: {
        Stage.RESEARCH_COMPLETE, Stage.IN_PROGRESS,
        Stage.PLANNED, Stage.HUMAN_INPUT_NEEDED,
        Stage.VALIDATOR_REJECTED,
        # issue #1139 P1-2 / sec 3.7: execution exhaustion (all model tiers AND
        # all re-plans spent — the analysis simply cannot run in this
        # environment) now routes to AGENT_BLOCKED, a distinct, operator-clearable,
        # re-openable sink, instead of VALIDATOR_REJECTED. This keeps an
        # infra/data-blocked GOOD idea (COMPUTE_ENV / DATA_UNREACHABLE
        # FailureClass) from being counted as an idea-quality rejection.
        Stage.AGENT_BLOCKED,
    },
    # research_complete is now a brief checkpoint where the
    # specialist reviewers run before research_review, so we allow
    # the same outgoing transitions as research_review (review
    # records already exist on disk; advancement_evaluate decides).
    #
    # Spec 015 T042 / FR-034: the convergence engine is the sole
    # inter-stage revision driver. RESEARCH_REVIEW emits a
    # ``KickbackRecord`` on non-convergence whose ``to_stage`` is one
    # of the regular stable stages below; non-convergence does NOT
    # produce a transient revision stage anymore. RESEARCH_FULL_REVISION
    # / RESEARCH_REJECTED are kept (they record terminal-ish judgments
    # the engine still emits to flag the work as escalated).
    Stage.RESEARCH_COMPLETE: {
        Stage.RESEARCH_REVIEW,
        Stage.RESEARCH_ACCEPTED,
        Stage.RESEARCH_FULL_REVISION,
        Stage.RESEARCH_REJECTED,
        # Engine kickback targets (T042):
        Stage.TASKED,
        Stage.CLARIFIED,
        Stage.BRAINSTORMED,
        # Convergence-kickback cap exceeded -> honest human escalation:
        Stage.HUMAN_INPUT_NEEDED,
    },
    # Research-quality review (US3):
    Stage.RESEARCH_REVIEW: {
        Stage.RESEARCH_ACCEPTED,
        Stage.RESEARCH_FULL_REVISION,
        Stage.RESEARCH_REJECTED,
        # Engine kickback targets (T042):
        Stage.TASKED,
        Stage.CLARIFIED,
        Stage.BRAINSTORMED,
        # T042 diagnostic-mode failsafe:
        Stage.AGENT_BLOCKED,
        # Convergence-kickback cap exceeded -> honest human escalation:
        Stage.HUMAN_INPUT_NEEDED,
    },
    Stage.RESEARCH_ACCEPTED: {Stage.PAPER_DRAFTING_INIT},
    # back to IMPLEMENTATION (in_progress) to re-do the analysis with feedback —
    # research_full_revision is not a resting step — OR honest escalation when the
    # convergence engine's kickback cap is exhausted (else routing throws each tick).
    Stage.RESEARCH_FULL_REVISION: {Stage.IN_PROGRESS, Stage.HUMAN_INPUT_NEEDED},
    Stage.RESEARCH_REJECTED: {Stage.BRAINSTORMED, Stage.HUMAN_INPUT_NEEDED},
    # Paper Spec Kit pipeline (US4):
    Stage.PAPER_DRAFTING_INIT: {Stage.PAPER_SPECIFIED},
    # Spec 015 F-20 Part B: the paper_spec convergence panel (run by the
    # paper_clarifier at PAPER_SPECIFIED) kicks back to paper_drafting_init
    # (re-spec) or clarified (science-root → research side).
    Stage.PAPER_SPECIFIED: {
        Stage.PAPER_CLARIFIED, Stage.PAPER_DRAFTING_INIT, Stage.CLARIFIED,
        Stage.HUMAN_INPUT_NEEDED,
    },
    # PAPER_CLARIFIED -> PAPER_CLARIFIED self-loop: the paper_plan convergence
    # panel (run by the paper_planner at PAPER_CLARIFIED) kicks back here for
    # paper_clarified-targeted concerns.
    Stage.PAPER_CLARIFIED: {
        Stage.PAPER_PLANNED, Stage.PAPER_CLARIFIED, Stage.HUMAN_INPUT_NEEDED,
        Stage.PAPER_SPECIFIED,  # spec 023 defect #14: paper-plan spec-gap kickback
    },
    # PAPER_PLANNED -> PAPER_PLANNED self-loop: the paper_tasks convergence
    # panel (run by the paper_tasker at PAPER_PLANNED) kicks back here to
    # re-task on a deeper unresolved concern (mirrors PAPER_CLARIFIED). The
    # HUMAN_INPUT_NEEDED edge lets the kickback cap escalate cleanly.
    Stage.PAPER_PLANNED: {
        Stage.PAPER_PLANNED, Stage.PAPER_TASKED, Stage.HUMAN_INPUT_NEEDED,
        Stage.PAPER_SPECIFIED,  # spec 023 defect #14: paper-plan spec-gap kickback
        Stage.PAPER_CLARIFIED,  # paper tasks panel plan-flaw kickback target
    },
    # Spec 023 defect #22 (paper twin): see Stage.TASKED above.
    Stage.PAPER_TASKED: {
        Stage.PAPER_ANALYZED, Stage.PAPER_CLARIFIED, Stage.HUMAN_INPUT_NEEDED,
    },
    Stage.PAPER_ANALYZED: {Stage.PAPER_IN_PROGRESS},
    Stage.PAPER_IN_PROGRESS: {Stage.PAPER_COMPLETE, Stage.PAPER_IN_PROGRESS},
    # paper_complete is now a brief checkpoint where the 12 paper
    # specialists run before paper_review.
    Stage.PAPER_COMPLETE: {
        Stage.PAPER_REVIEW,
        Stage.PAPER_ACCEPTED,
        Stage.PAPER_FUNDAMENTAL_FLAWS,
        # Engine kickback targets (T042):
        Stage.PAPER_TASKED,
        Stage.PAPER_CLARIFIED,
        Stage.CLARIFIED,
        Stage.BRAINSTORMED,
    },
    # Final paper review (US5).
    #
    # Spec 015 T042 / FR-034: the 7 transient revision stages were
    # deleted; the convergence engine emits a KickbackRecord that routes
    # directly to a regular stable stage. PAPER_FUNDAMENTAL_FLAWS is
    # retained for terminal-ish "trash the project" judgments.
    Stage.PAPER_REVIEW: {
        Stage.PAPER_ACCEPTED,
        Stage.PAPER_FUNDAMENTAL_FLAWS,
        # Engine kickback targets (T042):
        Stage.PAPER_TASKED,
        Stage.PAPER_CLARIFIED,
        Stage.CLARIFIED,
        Stage.BRAINSTORMED,
        # T042 diagnostic-mode failsafe:
        Stage.AGENT_BLOCKED,
    },
    Stage.PAPER_ACCEPTED: {Stage.AWAITING_PUBLICATION_SIGNOFF},
    # Spec 015 / FR-054: PAPER_ACCEPTED -> AWAITING_PUBLICATION_SIGNOFF
    # (publisher assembles), then AWAITING_PUBLICATION_SIGNOFF -> POSTED
    # once the maintainer's sign-off record exists. PUBLISH_BLOCKED is
    # reached after 5 consecutive Zenodo failures.
    Stage.AWAITING_PUBLICATION_SIGNOFF: {
        Stage.POSTED,
        Stage.PUBLISH_BLOCKED,
        Stage.AWAITING_PUBLICATION_SIGNOFF,  # no-op self-loop until sign-off
        # Spec 023 / FR-020: a maintainer REJECTION at the sign-off gate
        # converts the stated reason into review feedback and re-enters
        # the revision loop.
        Stage.PAPER_REVIEW,
    },
    Stage.PUBLISH_BLOCKED: {Stage.PAPER_ACCEPTED},  # operator `project republish`
    Stage.PAPER_FUNDAMENTAL_FLAWS: {Stage.BRAINSTORMED},
    # Spec 015 T042: AGENT_BLOCKED is the unified failsafe sink for any
    # agent whose own retries are exhausted AND whose diagnostic mode
    # can't classify the failure into an actionable Concern. Cleared via
    # CLI `llmxive project unblock-agent` (operator must edit action
    # items first). Reusable for any agent.
    Stage.AGENT_BLOCKED: {
        Stage.PAPER_REVIEW,
        Stage.RESEARCH_REVIEW,
        Stage.PAPER_TASKED,
        Stage.PAPER_CLARIFIED,
        Stage.TASKED,
        Stage.CLARIFIED,
        Stage.BRAINSTORMED,
    },
    Stage.POSTED: set(),  # terminal
    # External-paper intake triage (spec 024): the reprocessor transforms an
    # ingested paper in place (run_one_step early-return) into a code-included
    # project (-> in_progress; the execution gate runs the existing code) or a
    # no-code follow-up idea (-> brainstormed). Both targets registered so the
    # transition is valid for any caller / completeness check.
    # Reviewed-Preprints (2026-07-01): intake now parks the paper at the TERMINAL
    # REVIEWED_PREPRINT (review-only, never modified) and spawns a SEPARATE follow-up
    # brainstorm project. BRAINSTORMED/IN_PROGRESS retained so the one-time migration
    # and any legacy in-flight intake can still route.
    Stage.PAPER_INGESTED: {
        Stage.REVIEWED_PREPRINT, Stage.BRAINSTORMED, Stage.IN_PROGRESS,
    },
    # Terminal: a reviewed preprint never advances.
    Stage.REVIEWED_PREPRINT: set(),
    # RETIRED state: auto-recovered into the pipeline (run_one_step re-plans a
    # straggler here -> PLANNED / PAPER_PLANNED). No human action is required.
    Stage.HUMAN_INPUT_NEEDED: {Stage.PLANNED, Stage.PAPER_PLANNED},
    Stage.BLOCKED: set(),
}


def is_valid_transition(src: Stage, dst: Stage) -> bool:
    return dst in ALLOWED_TRANSITIONS.get(src, set())


def successors(src: Stage) -> set[Stage]:
    return ALLOWED_TRANSITIONS.get(src, set())


def all_stages() -> Iterable[Stage]:
    return Stage


__all__ = ["ALLOWED_TRANSITIONS", "all_stages", "is_valid_transition", "successors"]
