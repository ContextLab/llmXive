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
    Stage.CLARIFIED: {Stage.PLANNED, Stage.CLARIFIED, Stage.HUMAN_INPUT_NEEDED},
    # PLANNED -> PLANNED self-loop: the tasks convergence panel (run by the
    # tasker at PLANNED) kicks back to ``planned`` to re-task on a deeper
    # unresolved concern — exactly mirroring the CLARIFIED self-loop for the
    # plan panel. (A writing-only kickback routes forward to TASKED, already
    # allowed.) Without this self-loop edge a tasks-stage kickback would crash
    # run_one_step's is_valid_transition guard.
    Stage.PLANNED: {Stage.PLANNED, Stage.TASKED, Stage.HUMAN_INPUT_NEEDED},
    Stage.TASKED: {Stage.ANALYZE_IN_PROGRESS, Stage.ANALYZED},
    Stage.ANALYZE_IN_PROGRESS: {Stage.ANALYZED, Stage.HUMAN_INPUT_NEEDED},
    Stage.ANALYZED: {Stage.IN_PROGRESS},
    Stage.IN_PROGRESS: {Stage.RESEARCH_COMPLETE, Stage.IN_PROGRESS, Stage.HUMAN_INPUT_NEEDED},
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
    },
    Stage.RESEARCH_ACCEPTED: {Stage.PAPER_DRAFTING_INIT},
    Stage.RESEARCH_FULL_REVISION: {Stage.CLARIFIED},  # back to clarified with feedback
    Stage.RESEARCH_REJECTED: {Stage.BRAINSTORMED},
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
    },
    # PAPER_PLANNED -> PAPER_PLANNED self-loop: the paper_tasks convergence
    # panel (run by the paper_tasker at PAPER_PLANNED) kicks back here to
    # re-task on a deeper unresolved concern (mirrors PAPER_CLARIFIED). The
    # HUMAN_INPUT_NEEDED edge lets the kickback cap escalate cleanly.
    Stage.PAPER_PLANNED: {
        Stage.PAPER_PLANNED, Stage.PAPER_TASKED, Stage.HUMAN_INPUT_NEEDED,
    },
    Stage.PAPER_TASKED: {Stage.PAPER_ANALYZED},
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
    Stage.HUMAN_INPUT_NEEDED: set(),  # exit only via human action
    Stage.BLOCKED: set(),
}


def is_valid_transition(src: Stage, dst: Stage) -> bool:
    return dst in ALLOWED_TRANSITIONS.get(src, set())


def successors(src: Stage) -> set[Stage]:
    return ALLOWED_TRANSITIONS.get(src, set())


def all_stages() -> Iterable[Stage]:
    return Stage


__all__ = ["ALLOWED_TRANSITIONS", "all_stages", "is_valid_transition", "successors"]
