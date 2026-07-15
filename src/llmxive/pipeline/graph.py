"""Pipeline orchestration graph (T058).

Maps each project lifecycle stage to the agent class that owns the
transition out of that stage. The scheduler picks the next project,
the dispatcher (`run_one_step`) instantiates the right agent for the
project's current stage, runs it under the per-project lock, then
re-evaluates the project's stage via the Advancement-Evaluator.

LangGraph itself is not yet used for v1 — a flat dispatch dict gives
us the same resume / single-step semantics with much less ceremony.
A future refactor could swap the dict for a LangGraph StateGraph
without changing public APIs.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from llmxive.agents import registry as registry_loader
from llmxive.agents.advancement import (
    REVIEW_STAGES,
    verdict_coverage,
)
from llmxive.agents.advancement import (
    evaluate as advancement_evaluate,
)
from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.idea_lifecycle import (
    BrainstormAgent,
    FleshOutAgent,
    IdeaSelectorAgent,
    ResearchQuestionValidatorAgent,
)
from llmxive.agents.implementer import LLMXiveImplementer
from llmxive.agents.lifecycle import is_valid_transition
from llmxive.agents.paper_initializer import PaperInitializerAgent
from llmxive.agents.paper_reviewer import PaperReviewerAgent
from llmxive.agents.project_initializer import (
    ProjectInitializerAgent,
)
from llmxive.agents.publisher import PaperPublisher
from llmxive.agents.research_reviewer import ResearchReviewerAgent
from llmxive.agents.runner import run_agent
from llmxive.config import (
    IMPLEMENT_BATCH_BUDGET_SECONDS,
    IMPLEMENT_TASK_BATCH,
)
from llmxive.config import repo_root as _repo_root
from llmxive.pipeline._kickback import (
    IDEA_RETRY_CAP,
    KickbackDecision,
    bump_count,
    consume_convergence_kickback,
    reset_kickback_count,
)
from llmxive.speckit._stage_panel import StagePanelEscalation, StagePanelKickback
from llmxive.speckit.clarify_cmd import ClarifierAgent
from llmxive.speckit.implement_cmd import ImplementerAgent
from llmxive.speckit.paper_clarify_cmd import PaperClarifierAgent
from llmxive.speckit.paper_implement_cmd import PaperImplementerAgent
from llmxive.speckit.paper_plan_cmd import PaperPlannerAgent
from llmxive.speckit.paper_specify_cmd import PaperSpecifierAgent
from llmxive.speckit.paper_tasks_cmd import PaperTaskerAgent
from llmxive.speckit.plan_cmd import PlannerAgent
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext
from llmxive.speckit.specify_cmd import SpecifierAgent
from llmxive.speckit.tasks_cmd import TaskerAgent
from llmxive.state import execution_status
from llmxive.state import project as project_store
from llmxive.types import (
    AgentRegistryEntry,
    Project,
    Stage,
)

logger = logging.getLogger(__name__)

# Map (current_stage, agent_name) — the agent invoked when a project is
# at the keyed stage. The agent's run() drives the transition to the
# next stage.
STAGE_TO_AGENT: dict[Stage, str] = {
    Stage.BRAINSTORMED: "flesh_out",
    Stage.FLESH_OUT_IN_PROGRESS: "flesh_out",
    # spec 003 / D10 (research_question_validator): the new validator
    # stage runs between flesh_out and project_initializer to catch
    # implementation-method narrowing and circular question framing.
    Stage.FLESH_OUT_COMPLETE: "research_question_validator",
    Stage.VALIDATED: "project_initializer",
    Stage.PROJECT_INITIALIZED: "specifier",
    Stage.SPECIFIED: "clarifier",
    Stage.CLARIFIED: "planner",
    Stage.PLANNED: "tasker",
    Stage.TASKED: "tasker",  # tasker also drives analyze
    Stage.ANALYZE_IN_PROGRESS: "tasker",
    Stage.ANALYZED: "implementer",
    Stage.IN_PROGRESS: "implementer",
    # US3: research_complete is a brief checkpoint — kick straight into
    # research_review so the specialist reviewers actually vote.
    # (Previously the project just sat at research_complete waiting for
    # a review to appear that no agent was producing.)
    Stage.RESEARCH_COMPLETE: "research_reviewer",
    Stage.RESEARCH_REVIEW: "research_reviewer",
    # US4: paper-stage Spec Kit pipeline.
    Stage.RESEARCH_ACCEPTED: "paper_initializer",
    Stage.PAPER_DRAFTING_INIT: "paper_specifier",
    Stage.PAPER_SPECIFIED: "paper_clarifier",
    Stage.PAPER_CLARIFIED: "paper_planner",
    Stage.PAPER_PLANNED: "paper_tasker",
    Stage.PAPER_TASKED: "paper_tasker",
    Stage.PAPER_ANALYZED: "paper_implementer",
    Stage.PAPER_IN_PROGRESS: "paper_implementer",
    # US5: at paper_complete the project waits for at least one
    # paper-stage review record to exist, then auto-transitions to
    # paper_review (handled by advancement.evaluate).
    Stage.PAPER_COMPLETE: "paper_reviewer",
    Stage.PAPER_REVIEW: "paper_reviewer",
    # FR-021/036/054 (discrepancy #2 / #58): the publisher runs at
    # AWAITING_PUBLICATION_SIGNOFF. It self-gates on the maintainer DOI
    # sign-off — no sign-off → no-op (stays awaiting); sign-off present →
    # final compile + Zenodo DOI + publication.yaml + transition to POSTED.
    # (PAPER_ACCEPTED → AWAITING_PUBLICATION_SIGNOFF is the pass-through flip
    # in _decide_next_stage; the publisher is the SOLE driver of → POSTED.)
    Stage.AWAITING_PUBLICATION_SIGNOFF: "paper_publisher",
}


# Maps the stage at which each doc-stage convergence panel RUNS to the
# ``stage_label`` that panel passes to ``run_stage_panel`` (and thus the key
# used in the kickback-count file). Used to reset the kickback counter once a
# panel converges and the project advances forward (F-20 Part B). The tasks /
# paper_tasks panels run at PLANNED / PAPER_PLANNED and now also emit the
# adaptive kickback sentinel (research tasker via the engine bridge; paper
# tasker via run_stage_panel), so their stages are included here — otherwise a
# converged tasks panel would never reset its kickback counter.
_STAGE_PANEL_LABEL: dict[Stage, str] = {
    Stage.SPECIFIED: "spec",
    Stage.CLARIFIED: "plan",
    Stage.PLANNED: "tasks",
    Stage.PAPER_SPECIFIED: "paper_spec",
    Stage.PAPER_CLARIFIED: "paper_plan",
    Stage.PAPER_PLANNED: "paper_tasks",
}


# Agents that do NOT advance any single project's stage; they run on a
# cron and act across the lanes (currently: just `personality`, spec 008).
# Listed here so the CLI / scheduler explicitly know to skip them in the
# stage-picker loop. Stage-independent agents are invoked directly by the
# CLI's `_cmd_run` --agent <name> branch.
STAGE_INDEPENDENT_AGENTS: set[str] = {
    "personality",
}


# Stage transitions performed automatically by the pipeline graph after
# each agent run — for non-LLM stages (e.g., the Implementer marks tasks
# off and we transition to research_complete when all are done).
STAGE_AFTER_AGENT: dict[Stage, Stage] = {
    Stage.BRAINSTORMED: Stage.FLESH_OUT_COMPLETE,
    Stage.FLESH_OUT_IN_PROGRESS: Stage.FLESH_OUT_COMPLETE,
    # spec 003 / D10: validator runs at FLESH_OUT_COMPLETE; the sentinel
    # detection in _decide_next_stage may override this default if the
    # validator emits validator_revise (back to FLESH_OUT_IN_PROGRESS) or
    # validator_rejected (back to BRAINSTORMED).
    Stage.FLESH_OUT_COMPLETE: Stage.VALIDATED,
    Stage.VALIDATED: Stage.PROJECT_INITIALIZED,
    Stage.PROJECT_INITIALIZED: Stage.SPECIFIED,
    Stage.SPECIFIED: Stage.CLARIFIED,
    Stage.CLARIFIED: Stage.PLANNED,
    Stage.PLANNED: Stage.TASKED,
    Stage.TASKED: Stage.ANALYZED,
    # IN_PROGRESS → IN_PROGRESS until all tasks are complete (handled
    # below via _all_tasks_done).
    # US4 paper-stage transitions:
    Stage.RESEARCH_ACCEPTED: Stage.PAPER_DRAFTING_INIT,
    Stage.PAPER_DRAFTING_INIT: Stage.PAPER_SPECIFIED,
    Stage.PAPER_SPECIFIED: Stage.PAPER_CLARIFIED,
    Stage.PAPER_CLARIFIED: Stage.PAPER_PLANNED,
    Stage.PAPER_PLANNED: Stage.PAPER_TASKED,
    Stage.PAPER_TASKED: Stage.PAPER_ANALYZED,
    # PAPER_IN_PROGRESS → PAPER_IN_PROGRESS until all paper tasks done
    # AND LaTeX builds AND citations clean AND proofreader clean.
}


#: Registry name of the convergence revision implementer (spec 013 / 023):
#: dispatched for a review-stage project whose saved state carries an
#: unconsumed ``revision_spec_path`` (FR-002).
_REVISION_IMPLEMENTER_NAME = "llmxive_implementer"

_NON_SPECKIT_AGENTS: dict[str, Callable[[AgentRegistryEntry], Agent]] = {
    "brainstorm": BrainstormAgent,
    "flesh_out": FleshOutAgent,
    "research_question_validator": ResearchQuestionValidatorAgent,
    "idea_selector": IdeaSelectorAgent,
    "project_initializer": ProjectInitializerAgent,
    "research_reviewer": ResearchReviewerAgent,
    "paper_initializer": PaperInitializerAgent,
    "paper_reviewer": PaperReviewerAgent,
    "paper_publisher": PaperPublisher,
    _REVISION_IMPLEMENTER_NAME: LLMXiveImplementer,
}

_SPECKIT_AGENTS: dict[str, type[SlashCommandAgent]] = {
    "specifier": SpecifierAgent,
    "clarifier": ClarifierAgent,
    "planner": PlannerAgent,
    "tasker": TaskerAgent,
    "implementer": ImplementerAgent,
    "paper_specifier": PaperSpecifierAgent,
    "paper_clarifier": PaperClarifierAgent,
    "paper_planner": PaperPlannerAgent,
    "paper_tasker": PaperTaskerAgent,
    "paper_implementer": PaperImplementerAgent,
}


def _active_tasks_md(project_dir: Path, *, track: str) -> Path | None:
    """The ``tasks.md`` of the project's ACTIVE feature dir — resolved through the
    SSoT ``feature_dir_for`` (honors the ``speckit_*_dir`` pointer) so a stale
    lower-numbered ``specs/*`` dir can NEVER shadow the real one. A plain
    ``sorted(glob)[0]`` reads the lexicographically-first dir, which froze
    PROJ-552 (a passing project sat at in_progress forever because the gate read
    a ghost ``specs/001`` while the work happened in ``specs/010``)."""
    fdir = project_store.feature_dir_for(project_dir, track=track)
    if fdir is None:
        return None
    tasks = fdir / "tasks.md"
    return tasks if tasks.is_file() else None


# A task the implementer CLAIMED done that the independent task-verifier has NOT
# yet accepted — "under review". It is NOT complete: a project must not advance
# with unverified tasks, and the count drives the implement loop. Distinct from
# `[ ]` (not started) so the dashboard + next implementer see the under-review
# state, and distinct from `[X]` (verifier-accepted, truly done).
UNDER_REVIEW_MARK = "- [~]"

#: A REAL task line: a checkbox at the start of a line (leading indent allowed for
#: subtasks). Anchored with re.M so a `- [ ]` appearing INSIDE prose — most often the
#: tasks.md's own "## Format: `- [ ] T### …`" documentation header — is NOT miscounted
#: as an open task. That literal example kept `_all_tasks_done` False forever and
#: stranded PROJ-148 at in_progress (all 60 tasks done, execution never ran) for 16
#: days. Mirrors task_verifier._TASK_LINE_RE (require a space after the box).
_TASK_LINE_RE = re.compile(r"^\s*-\s*\[([ xX~])\]\s", re.MULTILINE)


def _task_marks(text: str) -> list[str]:
    """The mark of every real checkbox task line: ``' '`` | ``'x'`` | ``'X'`` | ``'~'``."""
    return _TASK_LINE_RE.findall(text)


def _tasks_all_done(text: str) -> bool:
    marks = _task_marks(text)
    return bool(marks) and all(m in ("x", "X") for m in marks)


def _all_tasks_done(project_dir: Path) -> bool:
    tasks = _active_tasks_md(project_dir, track="research")
    if tasks is None:
        return False
    return _tasks_all_done(tasks.read_text(encoding="utf-8"))


def _all_paper_tasks_done(project_dir: Path) -> bool:
    tasks = _active_tasks_md(project_dir, track="paper")
    if tasks is None:
        return False
    return _tasks_all_done(tasks.read_text(encoding="utf-8"))


def _incomplete_task_count(project_dir: Path, *, paper: bool) -> int:
    """Count remaining unchecked (`- [ ]`) PLUS under-review (`- [~]`) tasks.

    Drives the implement-batch loop's progress guard: each speckit-implementer
    run checks off (or skips) exactly one task, so this count must strictly
    DECREASE every iteration. If it ever fails to (a task left `[ ]`), the batch
    stops rather than spinning. An `- [~]` (verifier-rejected / awaiting review)
    task is also incomplete — the project may not advance until the independent
    task-verifier accepts it. Returns a large sentinel when no tasks.md exists yet
    (treated as "not drainable this tick"). Resolves the ACTIVE feature dir (SSoT)
    so the loop drains the REAL tasks.md, not a stale ghost spec dir.

    Counts real checkbox LINES only (:data:`_TASK_LINE_RE`) — a `- [ ]` in the
    format-doc header is not an open task."""
    tasks = _active_tasks_md(project_dir, track="paper" if paper else "research")
    if tasks is None:
        return -1
    marks = _task_marks(tasks.read_text(encoding="utf-8"))
    return sum(1 for m in marks if m in (" ", "~"))


def _run_task_verification(
    project_dir: Path, already_verified: set[str], *, repo_root: Path | None = None
) -> None:
    """Independently verify (separate-LLM) the research tasks the implementer just
    claimed done THIS tick — the spec-contract consistency gate.

    Rewrites each claimed task's mark in the active tasks.md: COMPLETE → ``[X]``
    (truly done), INCOMPLETE → ``[ ]`` + a note the NEXT implementer reads (redo),
    transient failure / over-cap → ``[~]`` (under review, re-verified next tick).
    Because ``_all_tasks_done`` requires no ``[ ]`` AND no ``[~]``, a project cannot
    advance to research_complete on tasks an independent model has not accepted.

    Research-track only (paper tasks have their own finalize gates). Never raises —
    a verifier hiccup must not abort the pipeline; the work simply re-verifies next
    tick. The verifier runs OUTSIDE the implementer's prompt/session (a distinct
    ``chat_with_fallback`` call), per the user-directed design."""
    from llmxive.agents import task_verifier as _tv
    from llmxive.speckit._comments_context import TASK_VERIFIER_NOTES_FILENAME

    tasks_path = _active_tasks_md(project_dir, track="research")
    if tasks_path is None:
        return
    spec_context = ""
    try:
        spec_context = (tasks_path.parent / "spec.md").read_text(encoding="utf-8")
    except OSError:
        pass
    memory_dir = project_dir / ".specify" / "memory"
    result = _tv.run_verification_pass(
        project_dir,
        tasks_path,
        already_verified=already_verified,
        spec_context=spec_context,
        notes_path=memory_dir / TASK_VERIFIER_NOTES_FILENAME,
        state_path=memory_dir / "task_verify.yaml",
    )
    if result["accepted"] or result["rejected"] or result["deferred"]:
        logger.info(
            "task-verifier %s: accepted=%d rejected=%d deferred=%d",
            project_dir.name, result["accepted"],
            len(result["rejected"]), len(result["deferred"]),
        )


def _human_escalation_reason_from_markers(project_dir: Path) -> str | None:
    """Read the ``reason`` from whichever ``human_input_needed.yaml`` marker
    exists (research- or paper-side), for surfacing onto the Project."""
    import yaml

    for marker in (
        project_dir / ".specify" / "memory" / "human_input_needed.yaml",
        project_dir / "paper" / ".specify" / "memory" / "human_input_needed.yaml",
    ):
        if not marker.exists():
            continue
        try:
            data = yaml.safe_load(marker.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        if isinstance(data, dict):
            reason = data.get("reason")
            if isinstance(reason, str) and reason.strip():
                return reason
    return None


def _paper_complete_preconditions_met(
    project_id: str, project_dir: Path, *, repo_root: Path | None = None
) -> bool:
    """All preconditions for paper_in_progress → paper_complete.

    Per FR-026 + the paper constitution: tasks done AND LaTeX builds
    AND every paper-stage citation is verified AND proofreader flag
    list is empty.
    """
    if not _all_paper_tasks_done(project_dir):
        return False
    # F-18 hard-block: a paper artifact that still carries an
    # ``[UNVERIFIED: ...]`` citation-guard marker (a fabricated / unverifiable
    # reference) must NOT advance to paper_complete. Checked BEFORE the
    # expensive LaTeX build so an unverified-reference paper short-circuits
    # cheaply. Complements the citation-store gate below: the store tracks
    # verified Citation rows, whereas the guard rewrites unresolvable refs
    # in-place — so EITHER signal blocks advancement.
    from llmxive.agents.citation_guard import project_unverified_markers

    marker_bodies = project_unverified_markers(
        project_id, track="paper", repo_root=repo_root
    )
    if marker_bodies:
        logger.warning(
            "paper_complete gate: blocking %s — unresolved unverified-citation "
            "marker(s) in paper artifacts: %s",
            project_id, "; ".join(marker_bodies),
        )
        return False
    # LaTeX build is REQUIRED — a paper-stage project without a
    # compilable main.tex is by definition not paper_complete.
    paper_source = project_dir / "paper" / "source" / "main.tex"
    if not paper_source.exists():
        return False
    from llmxive.agents.latex_build import build_paper
    build_result = build_paper(project_id, repo_root=repo_root)
    if not build_result.get("ok"):
        return False
    # And the produced PDF MUST exist on disk. Consume the producer's OWN
    # returned ``pdf_path`` — ``build_paper`` renders to ``paper/pdf/main.pdf``
    # (pdflatex ``-output-directory``), NEVER to ``paper/source/main.pdf``. The
    # old hard-coded ``source/main.pdf`` check was a path the producer never
    # writes, so this gate was effectively unsatisfiable for real builder output
    # (issue #1139 P0: 104 compilable main.tex, 0 pdf at the checked path). Also
    # require the PDF to be at least as fresh as the source it was built from so
    # a stale carry-over PDF cannot satisfy the gate.
    pdf_path_str = build_result.get("pdf_path")
    if not pdf_path_str or not Path(pdf_path_str).is_file():
        return False
    if Path(pdf_path_str).stat().st_mtime < paper_source.stat().st_mtime:
        return False
    # Citation gate.
    from llmxive.agents.reference_validator import has_blocking_citations

    if has_blocking_citations(project_id, repo_root=repo_root):
        return False
    # Proofreader gate.
    from llmxive.agents.proofreader import proofreader_clean

    if not proofreader_clean(project_id, repo_root=repo_root):
        return False
    return True


def run_one_step(
    project: Project,
    *,
    run_id: str | None = None,
    repo_root: Path | None = None,
) -> Project:
    """Advance one project by one stage (or one task, for in_progress).

    Returns the updated project. Raises if no agent is wired for the
    project's current stage.
    """
    repo = repo_root or _repo_root()
    run_id = run_id or str(uuid4())
    entry_stage = project.current_stage  # for the POSTED issue-close hook below

    agent_name = STAGE_TO_AGENT.get(project.current_stage)

    # LEGACY RECOVERY: human_input_needed is a RETIRED resting state. The
    # autonomous exhaustion flow (model-tier escalation + deterministic re-plan)
    # replaced every path that used to park here, so a project still AT
    # human_input_needed is a straggler from before that change — and a human
    # has no way to act on it. Recover it into the pipeline: route to PLANNED
    # (PAPER_PLANNED for a paper-phase straggler), reset the fix-round +
    # model-tier counters, and drop the deterministic re-plan report so the
    # planner adjusts the approach. Human input is required ONLY for the
    # publication DOI sign-off.
    if project.current_stage == Stage.HUMAN_INPUT_NEEDED:
        _hin_dir = repo / "projects" / project.id
        _write_execution_replan_feedback(
            _hin_dir, execution_status.load(project.id, repo_root=repo) or {}
        )
        execution_status.reset_fix_loop(project.id, repo_root=repo)
        _paper_phase = (_hin_dir / "paper").is_dir() and any(
            (_hin_dir / "paper").rglob("*.tex")
        )
        recovered = project.model_copy(update={
            "current_stage": Stage.PAPER_PLANNED if _paper_phase else Stage.PLANNED,
            "human_escalation_reason": None,
            "updated_at": datetime.now(UTC),
            "last_run_id": run_id,
        })
        project_store.save(recovered, repo_root=repo)
        logger.info(
            "recovered %s from human_input_needed -> %s (autonomous re-plan)",
            project.id, recovered.current_stage.value,
        )
        return recovered

    # External-paper intake triage (spec 024). A submitted / HF-ingested paper
    # enters at PAPER_INGESTED — NOT paper_review (which is reserved for an
    # llmXive-authored paper under review; an external paper there spins the
    # authored-revise loop forever with nothing to revise). Reprocess it into the
    # pipeline via the SINGLE shared transformation (Constitution I — never a
    # per-project edit): a code-included paper back-fills spec/plan/tasks from the
    # existing code (added as a submodule) and routes to the execution gate; a
    # no-code paper becomes a brainstormed follow-up idea. The reprocessor writes
    # all artifacts + returns the project at a normal pipeline stage; the next
    # tick advances it normally.
    if project.current_stage == Stage.PAPER_INGESTED:
        from llmxive.paper_reprocess import finalize_reviewed_preprint

        # Ethics change (2026-07-01): NEVER modify an ingested paper. Mark it a
        # review-only Reviewed Preprint, peer-review it once, and spawn a SEPARATE
        # llmXive brainstorm follow-up that cites (not re-authors) the original —
        # all in this one terminal tick (REVIEWED_PREPRINT is never re-picked).
        reprocessed = finalize_reviewed_preprint(
            project, repo_root=repo, run_id=run_id
        ).model_copy(update={"last_run_id": run_id})
        project_store.save(reprocessed, repo_root=repo)
        # Themed artifacts (cover-prepended original + peer-review report). Best
        # effort: a missing LaTeX toolchain / failed arXiv fetch must not sink the
        # intake — the migration/dashboard can rebuild them later.
        try:
            from llmxive.paper_reprocess.preprint_pdf import build_preprint_pdfs

            build_preprint_pdfs(reprocessed, repo_root=repo)
        except Exception as exc:
            logger.warning("preprint PDF build failed for %s: %s", project.id, exc)
        logger.info(
            "reprocessed ingested paper %s -> %s (reviewed preprint + follow-up)",
            project.id, reprocessed.current_stage.value,
        )
        return reprocessed

    # Dedicated execution phase (spec 023 defect #25): once EVERY task is
    # written, RUN the analysis end-to-end (quickstart run-book, in the
    # per-project venv) and gate research_complete on real artifacts —
    # instead of dispatching the implementer again. A failed run records the
    # tracebacks + re-opens the failing tasks (the bounded auto-fix loop);
    # success lets _decide_next_stage advance IN_PROGRESS -> RESEARCH_COMPLETE.
    # At the per-tier fix-round cap _decide_next_stage autonomously ESCALATES
    # the model tier (resetting fix_rounds, staying IN_PROGRESS so the next
    # tick re-runs the loop with the new model) and, once all tiers are
    # exhausted, RE-PLANS deterministically (routes to PLANNED) — it never
    # parks at human_input_needed. This is what stops a hollow, never-executed
    # implementation from reaching review (PROJ-552: 68/68 'done' but empty
    # data/figures).
    _exec_project_dir = repo / "projects" / project.id
    if (
        project.current_stage == Stage.IN_PROGRESS
        and _all_tasks_done(_exec_project_dir)
    ):
        # All tasks are checked off — this is the execution GATE, not implementer
        # work. If the analysis has NOT yet passed, run it (below the fix-round
        # cap); if it ALREADY passed in a prior tick (``is_ok``), skip straight to
        # the advance. Requiring ``not is_ok`` to ENTER this block stranded a
        # project that passed the gate on a tick with no advance tick left: every
        # later tick skipped the block and fell through to a pointless implementer
        # dispatch, so it sat at in_progress with is_ok=True forever despite
        # _decide_next_stage returning research_complete (the live PROJ-567 case;
        # CI hit it too).
        if not execution_status.is_ok(project.id, repo_root=repo):
            _at_cap = (
                execution_status.fix_rounds(project.id, repo_root=repo)
                >= execution_status.MAX_EXECUTION_FIX_ROUNDS
            )
            # Below the cap → RUN the analysis (records the outcome, may flip ok).
            # At/over the cap → DO NOT re-run; let _decide_next_stage apply the
            # autonomous exhaustion flow (model escalation or deterministic
            # re-plan) on the already-recorded failure.
            if not _at_cap:
                from llmxive.execution.stage import execute_and_gate
                execute_and_gate(_exec_project_dir, repo_root=repo)
                project = project_store.load(project.id, repo_root=repo)
        next_stage = _decide_next_stage(project, _exec_project_dir, repo_root=repo)
        if next_stage != project.current_stage:
            if not is_valid_transition(project.current_stage, next_stage):
                raise RuntimeError(
                    f"invalid transition {project.current_stage.value} "
                    f"-> {next_stage.value}"
                )
            project = project.model_copy(
                update={
                    "current_stage": next_stage,
                    "updated_at": datetime.now(UTC),
                    "last_run_id": run_id,
                }
            )
        project_store.save(project, repo_root=repo)
        return project

    # Spec 015 T042 / FR-034: the 7 transient revision stages were deleted.
    # The remaining stages that need pass-through routing (no agent runs
    # for them) are: RESEARCH_FULL_REVISION / RESEARCH_REJECTED (kept for
    # terminal-ish judgments), PAPER_FUNDAMENTAL_FLAWS (same), and
    # PAPER_ACCEPTED (publisher-bound). Each of those resolves to its
    # forward stage in ``_decide_next_stage`` below.
    if agent_name is None and project.current_stage in {
        Stage.RESEARCH_FULL_REVISION,
        Stage.RESEARCH_REJECTED,
        Stage.PAPER_FUNDAMENTAL_FLAWS,
        Stage.PAPER_ACCEPTED,
    }:
        next_stage = _decide_next_stage(project, repo / "projects" / project.id, repo_root=repo)
        if not is_valid_transition(project.current_stage, next_stage):
            raise RuntimeError(
                f"invalid revision-routing transition {project.current_stage.value} -> {next_stage.value}"
            )
        project = project.model_copy(
            update={
                "current_stage": next_stage,
                "updated_at": datetime.now(UTC),
            }
        )
        project_store.save(project, repo_root=repo)
        return project

    if agent_name is None:
        # Stages handled elsewhere (terminal states, unmapped stages):
        # ask the Advancement-Evaluator to evaluate review records — and
        # PERSIST its full result (spec 023 / FR-001: an evaluated-but-
        # unsaved decision is a discarded decision).
        evaluated = advancement_evaluate(project, repo_root=repo)
        project_store.save(evaluated, repo_root=repo)
        return evaluated

    entry = registry_loader.get(agent_name, repo_root=repo)
    project_dir = repo / "projects" / project.id
    project_dir.mkdir(parents=True, exist_ok=True)

    ran_revision_implementer = False
    if agent_name in _NON_SPECKIT_AGENTS:
        # Review stages (spec 023 / US1): three mutually-exclusive moves.
        #
        #   1. An unconsumed revision work-spec exists → dispatch the
        #      revision implementer, NOT reviewers (FR-002). The
        #      implementer consumes the work-spec, clears
        #      ``revision_spec_path``, and persists its own transition.
        #   2. No work-spec, but some required specialist's verdict is
        #      missing or stale (computed against an older artifact) →
        #      dispatch ONLY those specialists (FR-004 + stale-verdict
        #      edge case), recording why.
        #   3. Complete + current verdict set → dispatch NOTHING; the
        #      Advancement-Evaluator below decides from the existing
        #      verdicts (FR-004: no redundant reviewer calls).
        #
        # The evaluator gates on every specialist accepting (FR-028);
        # failing to dispatch missing specialists means projects can
        # never satisfy the gate.
        agents_to_run: list[str] = []
        if project.current_stage in REVIEW_STAGES:
            if project.revision_spec_path:
                agents_to_run = [_REVISION_IMPLEMENTER_NAME]
                ran_revision_implementer = True
                logger.info(
                    "%s carries unconsumed revision work-spec %s — "
                    "dispatching the revision implementer instead of reviewers",
                    project.id, project.revision_spec_path,
                )
            else:
                coverage = verdict_coverage(project, repo_root=repo)
                prefix = (
                    "research_reviewer"
                    if coverage.track == "research"
                    else "paper_reviewer"
                )
                if coverage.complete_and_current:
                    logger.info(
                        "%s: complete current verdict set (%d specialists, "
                        "live_hash=%s) — skipping reviewer dispatch, "
                        "evaluating existing verdicts (FR-004)",
                        project.id, len(coverage.required),
                        (coverage.live_hash or "")[:12],
                    )
                else:
                    needed = coverage.needs_dispatch
                    if coverage.stale:
                        logger.info(
                            "%s: stale verdicts from %s (artifact changed "
                            "since review; live_hash=%s) — re-dispatching "
                            "only those specialists",
                            project.id, sorted(coverage.stale),
                            (coverage.live_hash or "")[:12],
                        )
                    agents_to_run = [
                        n for n in registry_loader.list_names(repo_root=repo)
                        if n in needed
                        # The generic (un-suffixed) reviewer runs only on a
                        # project's first-ever review round; it does not
                        # gate advancement, so re-running it on every
                        # stale/missing round is redundant load.
                        or (n == prefix and not coverage.has_any_records)
                    ]
        else:
            agents_to_run = [agent_name]

        for an in agents_to_run:
            try:
                aentry = registry_loader.get(an, repo_root=repo)
            except KeyError:
                continue
            agent_cls = _NON_SPECKIT_AGENTS.get(an)
            if agent_cls is None:
                # Specialist reviewers reuse the generic class; route by stage.
                if an.startswith("research_reviewer"):
                    agent_cls = ResearchReviewerAgent
                elif an.startswith("paper_reviewer"):
                    agent_cls = PaperReviewerAgent
                else:
                    continue
            agent = agent_cls(aentry)
            ctx = AgentContext(
                project_id=project.id,
                run_id=run_id,
                task_id=str(uuid4()),
                inputs=_collect_idea_inputs(project_dir, repo),
                metadata={
                    "title": project.title,
                    "field": project.field,
                    "principal_agent_name": "flesh_out",
                },
            )
            is_review_dispatch = project.current_stage in {
                Stage.RESEARCH_COMPLETE, Stage.RESEARCH_REVIEW,
                Stage.PAPER_COMPLETE, Stage.PAPER_REVIEW,
            }
            if is_review_dispatch:
                # Specialist reviewer failures are non-fatal — log and
                # move on so other specialists still vote.
                try:
                    run_agent(agent, ctx, repo_root=repo)
                except Exception as exc:
                    logger.warning("reviewer %r failed: %s", an, exc)
            else:
                # Single-agent stages (brainstorm, flesh_out, etc.) —
                # propagate failures so the run is marked failed.
                run_agent(agent, ctx, repo_root=repo)
    elif agent_name in _SPECKIT_AGENTS:
        # SlashCommandAgents take no constructor args; the registry
        # entry is consulted at run() time via the SlashCommandContext.
        speckit_agent = _SPECKIT_AGENTS[agent_name]()

        # IMPLEMENT-STAGE BATCHING: the implementer checks off ONE task per
        # run, but a project carries 50-60 tasks and the load-balanced scheduler
        # picks any single stage only a fraction of the time — so at one
        # task/tick NO project ever drained in_progress (the universal wall:
        # zero projects had EVER reached research_complete). When an
        # implement-stage project is picked, drain up to IMPLEMENT_TASK_BATCH
        # tasks THIS tick, bounded by IMPLEMENT_BATCH_BUDGET_SECONDS wall-clock
        # (well under every implement-cron job timeout) and a strict
        # progress guard (the remaining-task count MUST fall each pass).
        _is_implement_batch = (
            (agent_name == "implementer"
             and project.current_stage in {Stage.ANALYZED, Stage.IN_PROGRESS})
            or (agent_name == "paper_implementer"
                and project.current_stage in {Stage.PAPER_ANALYZED, Stage.PAPER_IN_PROGRESS})
        )
        _paper_track = agent_name == "paper_implementer"
        _batch_cap = IMPLEMENT_TASK_BATCH if _is_implement_batch else 1
        _deadline = time.monotonic() + IMPLEMENT_BATCH_BUDGET_SECONDS
        _processed = 0
        # TASK-VERIFIER snapshot (spec-contract consistency): the implement batch
        # below marks tasks ``[X]`` on the implementer's OWN say-so. Snapshot which
        # tasks are ALREADY verifier-accepted (``[X]`` before this tick) so the
        # post-batch verify pass independently judges ONLY the tasks claimed THIS
        # tick (plus any prior-tick ``[~]`` deferrals) — never re-judging settled work.
        _verify_already_done: set[str] = set()
        if _is_implement_batch:
            from llmxive.agents.task_verifier import claimed_done_keys
            _vt_tasks = _active_tasks_md(
                project_dir, track="paper" if _paper_track else "research"
            )
            if _vt_tasks is not None:
                _verify_already_done = claimed_done_keys(
                    _vt_tasks.read_text(encoding="utf-8")
                )
        # MODEL-TIER OVERRIDE (autonomous exhaustion handling — SHARED ladder).
        # The per-project ``model_tier`` (execution_status) is the SSoT model
        # ladder for BOTH autonomous loops:
        #   * the execution fix-loop implementer (IN_PROGRESS), and
        #   * the doc-stage convergence panels (SPECIFIED/CLARIFIED/PLANNED +
        #     paper twins): when a panel exhausts its kickback cap, the
        #     escalate block bumps the tier and re-enters the review loop, so
        #     the NEXT dispatch of the doc-stage agent must run its convergence
        #     reviser/panel on the escalated model. Threading the override into
        #     ``ctx.default_model`` flows it straight to ``build_*_reviewspec(
        #     model=ctx.default_model)`` — the same `model=` router override the
        #     execution implementer uses, gated by the same paid credit guard.
        # Tier 0 = no override = the registered default.
        _model_for_run = entry.default_model
        _exec_fix = (
            agent_name == "implementer" and project.current_stage == Stage.IN_PROGRESS
        )
        _panel_stage = project.current_stage in _STAGE_PANEL_LABEL
        if _exec_fix or _panel_stage:
            _model_for_run = execution_status.execution_model_override(
                project.id,
                default_model=entry.default_model,
                repo_root=repo,
            )
            if _model_for_run != entry.default_model:
                logger.info(
                    "model-tier escalation: dispatching %s for %s (stage=%s) "
                    "with escalated model override %r (tier %d)",
                    agent_name, project.id, project.current_stage.value,
                    _model_for_run,
                    execution_status.model_tier(project.id, repo_root=repo),
                )
        while True:
            sk_ctx = SlashCommandContext(
                project_id=project.id,
                project_dir=project_dir,
                run_id=run_id,
                task_id=str(uuid4()),
                inputs=[],
                expected_outputs=[],
                prompt_template_path=repo / entry.prompt_path,
                default_backend=entry.default_backend,
                fallback_backends=entry.fallback_backends,
                default_model=_model_for_run,
                prompt_version=entry.prompt_version,
                agent_name=entry.name,
            )
            _before = (
                _incomplete_task_count(project_dir, paper=_paper_track)
                if _is_implement_batch else 0
            )
            try:
                speckit_agent.run(sk_ctx)
            except StagePanelKickback as exc:
                # CONTROLLED non-convergence: the panel already wrote its
                # convergence_kickback.yaml sentinel. Do NOT propagate — fall through
                # to _decide_next_stage below, which CONSUMES that sentinel and routes
                # the project to the content stage to auto-retry (bounded by the
                # per-stage kickback cap → human escalation). Propagating instead
                # would skip routing entirely: the project would loop at this stage
                # forever (current_stage never advances; the cap never increments).
                logger.info("stage-panel kickback for %s: %s", project.id, exc)
                break
            except StagePanelEscalation as exc:
                # Engine failure (spec 023 / FR-016): the panel already filed a
                # tracked GitHub issue with the evidence. The project STAYS at
                # its current stage — schedulable, retried on later ticks, and
                # recovering automatically once the underlying defect is fixed.
                # (Pre-023 this fell through to a HUMAN_INPUT_NEEDED park.)
                logger.warning(
                    "stage-panel engine failure for %s (issue filed; project "
                    "stays schedulable): %s", project.id, exc,
                )
                try:
                    return project_store.load(project.id, repo_root=repo)
                except FileNotFoundError:
                    return project
            _processed += 1
            if not _is_implement_batch:
                break
            _after = _incomplete_task_count(project_dir, paper=_paper_track)
            if _after <= 0:
                break  # all tasks drained (or no tasks.md) — let the gate run
            if _after >= _before:
                # The pass didn't check off a task (parse loop / no-op). Stop
                # rather than spin — the next scheduled tick retries cleanly.
                logger.warning(
                    "implement batch: no progress for %s (remaining=%d); "
                    "stopping batch after %d task(s)",
                    project.id, _after, _processed,
                )
                break
            if _processed >= _batch_cap:
                break
            if time.monotonic() >= _deadline:
                logger.info(
                    "implement batch: wall-clock budget reached for %s after "
                    "%d task(s) (remaining=%d)", project.id, _processed, _after,
                )
                break
        if _is_implement_batch:
            logger.info(
                "implement batch: processed %d task(s) for %s this tick",
                _processed, project.id,
            )
            # INDEPENDENT TASK VERIFICATION (spec-contract consistency): a SEPARATE
            # model (outside the implementer's session) judges whether the tasks the
            # implementer just claimed done are GENUINELY satisfied by the artifacts
            # — accept → stays [X]; reject → [ ] + a note the next implementer reads;
            # transient/over-cap → [~] (under review). This is what stops a
            # self-reported-but-undone task from advancing the project (research
            # track only; paper tasks have their own finalize gates).
            if not _paper_track:
                try:
                    _run_task_verification(
                        project_dir, _verify_already_done, repo_root=repo
                    )
                except Exception as exc:  # must never abort the pipeline
                    logger.warning(
                        "task verification pass failed for %s: %s", project.id, exc
                    )
    else:
        raise RuntimeError(f"no implementation registered for agent {agent_name!r}")

    # Reload project state — agents like the Specifier persist
    # speckit_research_dir / speckit_paper_dir / artifact_hashes via
    # project_store.save() inside their write_artifacts hook. If we
    # operated on the stale `project` we'd overwrite those updates.
    try:
        project = project_store.load(project.id, repo_root=repo)
    except FileNotFoundError:
        pass

    # Review stages (spec 023 / US1, FR-001): the Advancement-Evaluator's
    # FULL result — stage, ``revision_spec_path``, kickback provenance —
    # is persisted, not reduced to a stage name. The pre-023 shape
    # (``return evaluated.current_stage`` inside ``_decide_next_stage``)
    # discarded everything but the stage: 92 papers looped at review
    # forever because their revise/accept decisions evaporated every tick
    # (issue #303 root cause).
    if entry_stage in REVIEW_STAGES:
        if ran_revision_implementer:
            # The implementer persisted its own transition (it clears
            # ``revision_spec_path`` and routes back to the review stage,
            # or applies its failsafe). Do NOT evaluate now: the stored
            # verdicts are stale relative to the just-revised artifact —
            # the next pass re-dispatches exactly the stale specialists.
            return project
        # Hold the per-project lock across evaluate+save: with a complete
        # verdict set NO agent dispatch happens, so nothing else acquired
        # it — two concurrent lanes could otherwise both evaluate and race
        # on the round dir / saved state (spec 023 concurrent-lanes edge
        # case). The loser sees LockError and retries on a later tick.
        from llmxive.agents.runner import project_lock
        with project_lock(project.id, run_id, repo_root=repo):
            evaluated = advancement_evaluate(project, repo_root=repo)
            evaluated = evaluated.model_copy(
                update={
                    "updated_at": datetime.now(UTC),
                    "last_run_id": run_id,
                }
            )
            project_store.save(evaluated, repo_root=repo)
        return evaluated

    # Update project stage based on the agent that just ran.
    next_stage = _decide_next_stage(project, project_dir, repo_root=repo)
    if next_stage != project.current_stage:
        if not is_valid_transition(project.current_stage, next_stage):
            raise RuntimeError(
                f"invalid transition {project.current_stage.value} -> {next_stage.value}"
            )
        update_fields: dict[str, Any] = {
            "current_stage": next_stage,
            "updated_at": datetime.now(UTC),
            "last_run_id": run_id,
        }
        # The Project schema requires human_escalation_reason when stage
        # is human_input_needed; supply one when the transition target
        # is the human-input stage. Prefer the reason recorded in the
        # human_input_needed.yaml marker (e.g. the convergence-kickback cap
        # escalation); fall back to the flesh-out scope-reject default.
        if next_stage == Stage.HUMAN_INPUT_NEEDED and not project.human_escalation_reason:
            update_fields["human_escalation_reason"] = (
                _human_escalation_reason_from_markers(project_dir)
                or (
                    "flesh-out judged idea out of GitHub-Actions-feasible scope; "
                    "idea archived under projects/<id>/idea/.archive/. Replace with "
                    "a tighter brainstorm or terminate."
                )
            )
        project = project.model_copy(update=update_fields)
    project_store.save(project, repo_root=repo)
    # Issue-lifecycle hook: close the linked GitHub issue when the project
    # REACHES POSTED this step — whether via a graph transition or the
    # publisher's OWN self-transition (paper_publisher sets POSTED directly
    # via project_state.update, so the graph sees no next_stage change).
    # Best-effort — failures here do not abort the pipeline.
    if project.current_stage == Stage.POSTED and entry_stage != Stage.POSTED:
        try:
            from llmxive.integrations import issues as issues_mod
            issues_mod.close_issue_for_project(repo, project)
        except Exception as exc:  # pragma: no cover — telemetry only
            logger.warning("issue-close hook failed for %s: %s", project.id, exc)
    return project


def _convergence_kickback_memory_dirs(project_dir: Path) -> list[Path]:
    """The two memory dirs a doc-stage panel may drop its sentinel into:
    the research-side and the paper-side ``.specify/memory/``."""
    return [
        project_dir / ".specify" / "memory",
        project_dir / "paper" / ".specify" / "memory",
    ]


#: Durable, project-local note carrying a downstream panel's unresolved
#: concerns to the content stage (flesh_out / brainstorm). Lives in
#: ``projects/<id>/idea/`` so the idea-phase agents find it; removed by
#: FleshOutAgent._persist once consumed so stale concerns never re-apply.
KICKBACK_FEEDBACK_FILENAME = "kickback_feedback.md"


def _write_kickback_feedback(project_dir: Path, decision: KickbackDecision) -> None:
    """Persist a consumed convergence-kickback's diagnosis for the content stage.

    The ``convergence_kickback.yaml`` sentinel (and its ``unresolved_concerns``)
    is deleted by :func:`consume_convergence_kickback` during routing, so the
    flesh-out / brainstorm agent would otherwise never see WHY the project was
    kicked back. We write the reason + each unresolved-concern body to
    ``projects/<id>/idea/kickback_feedback.md`` as a clearly-headed Markdown
    note the agent injects into its next prompt.
    """
    idea_dir = project_dir / "idea"
    idea_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Downstream review concerns (address in this revision)",
        "",
        "A downstream convergence panel kicked this project back to the idea "
        "stage. You MUST revise the idea — especially the `Methodology sketch` "
        "— to RESOLVE each concern below, not merely re-state the idea.",
        "",
        f"**Why it was kicked back**: {decision.reason}",
        "",
        "## Unresolved concerns",
        "",
    ]
    if decision.unresolved_concerns:
        lines.extend(f"- {c}" for c in decision.unresolved_concerns)
    else:
        lines.append(
            "- (no per-concern bodies were carried; see the reason above)"
        )
    (idea_dir / KICKBACK_FEEDBACK_FILENAME).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_doc_kickback_feedback(
    project_dir: Path, decision: KickbackDecision
) -> None:
    """Persist a consumed kickback's diagnosis for a DOC-stage re-dispatch.

    Spec 023 defect #19 companion: when a kickback routes to a speckit doc
    stage (specified / clarified / planned / tasked / paper twins) instead of
    the idea root, the sentinel — and with it the panel's unresolved-concern
    bodies — was consumed with NO hand-off: the re-dispatched agent (e.g. the
    clarifier revising spec.md in place) ran blind and the next panel had to
    rediscover the same residue from scratch. Write the diagnosis to
    ``.specify/memory/kickback_feedback.md``; every speckit command injects it
    via ``_comments_context.render_recent_comments_block`` and the graph
    deletes it once the panel at that stage converges (the same place the
    kickback counter resets).
    """
    memory_dir = project_dir / ".specify" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Unresolved panel concerns (address in this revision)",
        "",
        "The convergence panel for this stage could not resolve the concerns "
        "below within its round cap and kicked the project back for an "
        "IN-PLACE revision of the existing artifact. Revise the document to "
        "RESOLVE each concern — do NOT regenerate the document from scratch, "
        "and do NOT drop content that is not implicated by a concern.",
        "",
        f"**Why it was kicked back**: {decision.reason}",
        "",
        "## Unresolved concerns",
        "",
    ]
    if decision.unresolved_concerns:
        lines.extend(f"- {c}" for c in decision.unresolved_concerns)
    else:
        lines.append("- (no per-concern bodies were carried; see the reason above)")
    (memory_dir / KICKBACK_FEEDBACK_FILENAME).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _panel_is_paper(stage_label: str) -> bool:
    """Whether a convergence panel ``stage_label`` belongs to the PAPER track.

    The paper-track panels (``paper_spec`` / ``paper_plan`` / ``paper_tasks``)
    all carry the ``paper`` prefix; the research-track panels (``spec`` /
    ``plan`` / ``tasks``) do not. Used to derive the stage-appropriate RE-WORK
    stage when a convergence panel exhausts its model-escalation ladder.
    """
    return stage_label.startswith("paper")


def _panel_rework_stage(stage_label: str) -> Stage:
    """The deterministic RE-PLAN stage a convergence panel routes to once every
    model tier has exhausted its kickback cap (autonomous exhaustion handling).

    Research panels re-plan at :data:`Stage.PLANNED`; paper panels at
    :data:`Stage.PAPER_PLANNED`. Mirrors the execution path's route-to-PLANNED
    fallback — the planner re-derives the approach from the deterministic
    concerns report so the next panel sees a genuinely revised artifact rather
    than the same residue. NEVER ``human_input_needed``.
    """
    return Stage.PAPER_PLANNED if _panel_is_paper(stage_label) else Stage.PLANNED


def _write_convergence_replan_feedback(
    project_dir: Path, decision: KickbackDecision, *, paper: bool
) -> str:
    """DETERMINISTIC (no-LLM) re-plan report for a convergence panel that
    exhausted EVERY model tier without reaching unanimous acceptance.

    Mirrors :func:`_write_execution_replan_feedback`: a machine-generated
    markdown report of the UNRESOLVED panel concerns + the explicit
    adjust-the-approach instruction, written to the SAME doc-stage
    kickback-ingestion file the planner already reads
    (``.specify/memory/kickback_feedback.md`` — the paper twin uses the
    ``paper/`` memory dir). Returns the report text.

    SSoT: same ingestion channel as :func:`_write_doc_kickback_feedback`; the
    only difference is the framing (re-PLAN the approach vs. revise-in-place)
    because the model ladder is exhausted, so a fresh plan — not another
    in-place tweak by the same models — is what breaks the loop.
    """
    base = (project_dir / "paper") if paper else project_dir
    memory_dir = base / ".specify" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Re-plan: the panel could not converge — adjust the approach",
        "",
        "The convergence panel for this stage exhausted EVERY model tier (the "
        "registered default plus escalations) across its kickback cap without "
        "reaching unanimous acceptance. Rather than escalate to a human, the "
        "pipeline is RE-PLANNING this project: re-derive the implementation "
        "approach so the new plan RESOLVES each unresolved concern below — do "
        "NOT merely re-state the prior design.",
        "",
        f"**Why it could not converge**: {decision.reason}",
        "",
        "## Unresolved concerns (resolve these in the new plan)",
        "",
    ]
    if decision.unresolved_concerns:
        lines.extend(f"- {c}" for c in decision.unresolved_concerns)
    else:
        lines.append("- (no per-concern bodies were carried; see the reason above)")
    text = "\n".join(lines) + "\n"
    (memory_dir / KICKBACK_FEEDBACK_FILENAME).write_text(text, encoding="utf-8")
    return text


def _write_unverifiable_replan_feedback(
    project_dir: Path, entries: list[dict[str, Any]]
) -> str:
    """DETERMINISTIC re-plan note (NO LLM) for tasks the implementer repeatedly
    could not make pass verification (issue #1139 D6). Written to the SAME
    kickback-ingestion file the planner already reads (SSoT — no new channel)."""
    lines: list[str] = [
        "# Re-plan: task(s) could not be made to pass verification — "
        "adjust the approach",
        "",
        "The implementer repeatedly failed the verification checks for the task(s) "
        "below. They were NOT force-accepted (that fail-open was removed in "
        "issue #1139); instead the project re-plans so a DIFFERENT approach "
        "(simpler method, different tooling, or a decomposition into individually "
        "verifiable steps) can produce checkable artifacts.",
        "",
        "## Repeatedly-unverifiable tasks",
        "",
    ]
    for e in entries:
        key = str(e.get("task_key", "?"))
        reason = str(e.get("last_reason", "")).strip()
        cnt = e.get("reject_count", "?")
        lines.append(
            f"- `{key}` (rejected {cnt}x): {reason}"
            if reason else f"- `{key}` (rejected {cnt}x)"
        )
    lines += [
        "",
        "## Required change",
        "",
        "Re-plan so each promised deliverable is produced by a step whose output "
        "can be deterministically verified (a real file with the expected "
        "schema/content). Avoid the approach that produced the unverifiable work "
        "above.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    memory_dir = project_dir / ".specify" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / KICKBACK_FEEDBACK_FILENAME).write_text(text, encoding="utf-8")
    return text


def _write_execution_replan_feedback(
    project_dir: Path, rec: dict[str, Any]
) -> str:
    """DETERMINISTIC re-plan report for the execution fix-loop (NO LLM call).

    When every model tier has exhausted its fix-round cap without a clean run,
    the project re-plans (routes to PLANNED) with a machine-generated markdown
    report the Planner ingests on its next run — written to the SAME
    doc-stage kickback-ingestion file the convergence kickback uses
    (``.specify/memory/kickback_feedback.md``), so the Planner reads it via its
    existing recent-comments injection (SSoT — no new ingestion channel).

    The report contains: (a) "What worked" = the artifacts that WERE produced
    (with paths); (b) "What failed" = each failing command + its error tail;
    (c) the explicit adjust-the-approach instruction. Returns the report text.
    """
    artifacts = [str(a) for a in (rec.get("artifacts") or [])]
    failures = [str(f) for f in (rec.get("failures") or [])]
    reason = str(rec.get("reason") or "").strip()
    tier = rec.get("model_tier", 0)
    lines: list[str] = [
        "# Re-plan: the analysis could not be made to run — adjust the approach",
        "",
        "The execution fix-loop exhausted EVERY model tier (the registered "
        f"default plus escalations, last tier={tier}) without producing a clean, "
        "real run. Rather than escalate to a human, the pipeline is RE-PLANNING "
        "this project: re-derive the implementation approach using the evidence "
        "below so the new plan AVOIDS the failures that blocked the last one.",
        "",
    ]
    if reason:
        lines += [f"**Last execution summary**: {reason}", ""]
    lines += ["## What worked (artifacts that WERE produced)", ""]
    if artifacts:
        lines += [f"- `{a}`" for a in artifacts]
    else:
        lines.append("- (no real artifacts were produced)")
    lines += ["", "## What failed (commands + error tails)", ""]
    if failures:
        lines += [f"- {f}" for f in failures]
    else:
        lines.append("- (no per-command failures recorded; the run produced no "
                     "real data/figure artifacts)")
    # Class-SPECIFIC guidance (issue #1139 anti-pattern 4 / P1-2): the durable
    # failure_class the runner recorded decides the advice, instead of one generic
    # "make it CPU-tractable" line that mis-steers a data-unreachable or code-bug
    # failure. GPU→re-scope/offload, data→verified source, fabrication→real data,
    # bug→fix in place.
    from llmxive.execution.failure_class import REPLAN_GUIDANCE, FailureClass

    _fc_val = rec.get("failure_class")
    try:
        _fc = FailureClass(_fc_val) if _fc_val else FailureClass.UNKNOWN
    except ValueError:
        _fc = FailureClass.UNKNOWN
    lines += [
        "",
        "## Required change",
        f"(diagnosed failure class: **{_fc.value}**)",
        "",
        REPLAN_GUIDANCE[_fc],
        "",
    ]
    lines += _data_availability_replan_note(project_dir, rec)
    text = "\n".join(lines) + "\n"
    memory_dir = project_dir / ".specify" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / KICKBACK_FEEDBACK_FILENAME).write_text(text, encoding="utf-8")
    return text


def _data_availability_replan_note(
    project_dir: Path, rec: dict[str, Any]
) -> list[str]:
    """A DATA-AWARE addendum to the re-plan report (empty when the failure was
    not data-related).

    The generic "use a CPU-tractable alternative" instruction is blind to WHY a
    data-blocked project failed, so it lets the planner re-commit to the same
    unobtainable dataset — which fabricates again. This carries the specific
    data verdict forward, using the execution stage's verified-source discovery
    cache (``discovered_data_source.yaml``):

    - VERIFIED source exists but the run still failed (the code ignored it, e.g.
      hand-rolled a bare ``load_dataset(id)`` or invented a URL — the PROJ-843
      class): the new plan MUST wire the loader to the verified source/recipe.
    - Discovery SEARCHED and found NO accessible source (the dataset is
      access-gated — ADNI/HCP/UK-Biobank/registration-only — or not a public
      download): RE-PLAN around an OPEN dataset that answers the SAME question,
      or reframe; never re-select the gated dataset, never fabricate.
    - A data signal with no discovery cache: steer to an open, directly
      downloadable dataset for the same question; never fabricate.
    """
    blob = (str(rec.get("reason") or "") + " "
            + " ".join(str(f) for f in (rec.get("failures") or []))).lower()
    data_signal = any(k in blob for k in (
        "synthetic", "fabricat", "hollow", "no real data", "dataset", "download",
        "hfuri", "gated", "unreachable", "datasetnotfound", "data source",
    ))
    cached: dict[str, Any] | None = None
    try:
        from llmxive.execution.data_source import load_cached_source

        cached = load_cached_source(project_dir)
    except Exception:  # discovery cache is best-effort context
        cached = None
    status = (cached or {}).get("status")
    intent = str((cached or {}).get("intent") or "").strip()
    if not (data_signal or status in {"none", "error", "verified"}):
        return []

    note = ["## Required change — DATA AVAILABILITY", ""]
    if status == "verified":
        ref = str(cached.get("ref") or "").strip()
        count = cached.get("record_count")
        note += [
            "A REAL, verified data source for this project ALREADY EXISTS but the "
            "last run did not use it (it hand-rolled a loader that guessed an id/"
            "URL). The new plan MUST wire the data loader to this exact source:",
            "",
            f"- Install + load **`{ref}`**"
            + (f" (verified to load {count} real records)." if count else "."),
            "- Do NOT hand-roll a bare `load_dataset(\"<name>\")`, a guessed raw "
            "URL, or an invented mirror/baseline repo — use the verified package/"
            "recipe as the single source of the input data.",
            "",
        ]
    elif status in {"none", "error"}:
        subj = f" for **{intent[:120]}**" if intent else ""
        note += [
            f"An automated search for a programmatically-accessible real source"
            f"{subj} found NONE: the dataset is either access-gated (it needs "
            "registration / a data-use agreement, e.g. ADNI, HCP, UK Biobank, "
            "clinical records) or is not a public download. Re-downloading it "
            "will NEVER succeed on the free CI runner. Therefore:",
            "",
            "- RE-PLAN around an OPEN, directly-downloadable dataset that supports "
            "the SAME research question (candidate open repositories: OpenNeuro, "
            "UCI ML Repository, Hugging Face Datasets, Zenodo, OpenML, or a "
            "domain-specific open archive), OR reframe the question to one "
            "answerable with available open data — and say so honestly.",
            "- Do NOT re-select the same gated/private dataset, and do NOT "
            "fabricate or substitute synthetic/mock/placeholder data for it "
            "(a result on invented data is rejected by the fabrication gate).",
            "",
        ]
    else:
        note += [
            "The last run failed to obtain REAL input data. RE-PLAN around an "
            "OPEN, directly-downloadable dataset that supports the same research "
            "question (correct the dataset's canonical id, use a public mirror, "
            "or switch to an equivalent open dataset on OpenNeuro / UCI / Hugging "
            "Face / Zenodo). For a large dataset, stream a small REAL sample "
            "(`load_dataset(..., streaming=True)` and take the first N real rows, "
            "or `hf_hub_download` a single file) rather than the whole corpus. Do "
            "NOT fabricate or substitute synthetic/mock data for the real "
            "dataset — it is rejected by the fabrication gate.",
            "",
        ]
    return note


def _archive_idea_files(project_dir: Path) -> list[tuple[str, str]]:
    """Move the canonical idea .md bodies into ``idea/.archive/`` and return
    ``(filename, text)`` pairs so the constrained re-brainstorm can show the
    agent WHAT was rejected (FR-014)."""
    idea_dir = project_dir / "idea"
    archived: list[tuple[str, str]] = []
    if not idea_dir.is_dir():
        return archived
    archive_dir = idea_dir / ".archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    for md in sorted(idea_dir.glob("*.md")):
        # Don't archive diagnostic side-files; just the canonical idea body.
        if md.name in {
            "research_question_validation.md",
            KICKBACK_FEEDBACK_FILENAME,
        }:
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        md.rename(archive_dir / f"{ts}-{md.name}")
        archived.append((md.name, text))
    return archived


def _write_rebrainstorm_feedback(
    project_dir: Path,
    *,
    reason: str,
    archived: list[tuple[str, str]],
    attempt: int,
    cap: int,
) -> None:
    """Constrained re-brainstorm instruction for the next flesh-out pass
    (FR-014) — written to the same ``idea/kickback_feedback.md`` injection
    point the convergence kickbacks use (Constitution I)."""
    idea_dir = project_dir / "idea"
    idea_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Idea rejected as infeasible — propose a CONSTRAINED replacement",
        "",
        f"Regeneration attempt {attempt} of {cap}. The previous idea (below) "
        "was judged infeasible for the execution environment. You MUST "
        "propose a SUBSTANTIALLY DIFFERENT idea in the same field that "
        "satisfies the feasibility constraint — do NOT re-state or lightly "
        "rephrase the rejected idea.",
        "",
        f"**Why it was rejected**: {reason}",
        "",
        "**Feasibility constraint**: the entire study must be executable by "
        "automated agents inside GitHub-Actions-class compute — public "
        "datasets or generated data only, no human subjects, no wet lab, no "
        "GPU training runs, no paid services.",
        "",
        "## The rejected idea (for reference — do not reuse)",
        "",
    ]
    for name, text in archived:
        lines.append(f"### {name}")
        lines.append("")
        lines.append(text.strip())
        lines.append("")
    if not archived:
        lines.append("(the rejected idea body was empty or already archived)")
    (idea_dir / KICKBACK_FEEDBACK_FILENAME).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def process_scope_rejection(project: Project, project_dir: Path) -> Stage | None:
    """FR-014 infeasible-idea automation (spec 023): archive + constrained
    re-brainstorm, bounded by ``IDEA_RETRY_CAP`` → honest terminal.

    Returns the stage to route to, or None when no ``scope_rejected.yaml``
    marker is present. Public because the same path re-processes projects
    that the PRE-023 behavior parked at ``human_input_needed`` (FR-018) —
    one implementation for both entries (Constitution I).
    """
    scope_marker = project_dir / ".specify" / "memory" / "scope_rejected.yaml"
    if not scope_marker.exists():
        return None
    reason = scope_marker.read_text(encoding="utf-8", errors="replace").strip()
    archived = _archive_idea_files(project_dir)
    if not archived:
        # Already archived (e.g. by the pre-023 park path): pull the most
        # recent archive snapshot so the re-brainstorm still sees what was
        # rejected.
        archive_dir = project_dir / "idea" / ".archive"
        if archive_dir.is_dir():
            archived = [
                (p.name, p.read_text(encoding="utf-8", errors="replace"))
                for p in sorted(archive_dir.glob("*.md"))[-2:]
            ]
    scope_marker.unlink()  # consumed — a fresh rejection writes a new one
    count = bump_count(project_dir / ".specify" / "memory", "idea_scope_reject")
    if count > IDEA_RETRY_CAP:
        logger.warning(
            "%s: %d infeasible-scope rejections (cap=%d) — honest "
            "terminal VALIDATOR_REJECTED (FR-014)",
            project.id, count, IDEA_RETRY_CAP,
        )
        return Stage.VALIDATOR_REJECTED
    _write_rebrainstorm_feedback(
        project_dir,
        reason=reason or "flesh-out judged the idea out of feasible scope",
        archived=archived,
        attempt=count,
        cap=IDEA_RETRY_CAP,
    )
    logger.info(
        "%s: infeasible scope — archived idea, constrained re-brainstorm "
        "%d/%d (FR-014)", project.id, count, IDEA_RETRY_CAP,
    )
    return Stage.BRAINSTORMED


def _reset_revision_rounds(project_id: str, *, repo_root: Path) -> None:
    """Clear a project's auto-revisions round dirs + revision_history so its NEXT
    review cycle starts with a fresh ``MAX_REVISION_ROUNDS`` budget.

    Called on a FULL-revision kickback (the analysis is being redone from an
    earlier stage, so the prior per-doc revision rounds are about a now-obsolete
    artifact version). Without this, a project that exhausted its 3-round cap
    returns to research_review still exhausted → kicks back again → loops
    straight to human escalation, never getting to address concerns that only
    surfaced AFTER the early rounds (the PROJ-552 layered-review stall: rounds
    1-3 spent on placeholder docs, the real data-quality defect surfaced only at
    round 4). Bounded by the convergence-kickback cap. Never raises."""
    import shutil

    from llmxive.state import revision_history as _rh

    try:
        ar = repo_root / "specs" / "auto-revisions" / project_id
        if ar.is_dir():
            shutil.rmtree(ar, ignore_errors=True)
        hist = _rh._hist_path(project_id, repo_root=repo_root)
        if hist.is_file():
            hist.unlink()
        # The implementer's consecutive-zero-success failsafe counter is also
        # per-version — reset it so the fresh cycle starts clean.
        czr = repo_root / "state" / f"{project_id}.implementer.yaml"
        if czr.is_file():
            czr.unlink()
    except OSError as exc:
        logger.warning("revision-round reset failed for %s: %s", project_id, exc)


def _decide_next_stage(
    project: Project, project_dir: Path, *, repo_root: Path | None = None
) -> Stage:
    """Pick the appropriate post-agent stage for the project."""
    # ADAPTIVE convergence kickback (F-14 / F-20 Part B): a doc-stage panel
    # that did NOT converge drops a generic ``convergence_kickback.yaml`` record
    # carrying the content stage to roll back to. Consume it BEFORE the
    # ``human_input_needed.yaml`` check so the project auto-retries at the
    # content stage instead of stalling for a human — bounded by a per-stage
    # kickback cap that escalates to human_input_needed after repeated failures.
    for mem_dir in _convergence_kickback_memory_dirs(project_dir):
        decision = consume_convergence_kickback(mem_dir)
        if decision is None:
            continue
        # issue #1139 D3: only HONOR a convergence kickback whose panel is the one
        # that runs at the project's CURRENT stage. A sentinel whose stage_label
        # does NOT match the current stage's panel is STALE / cross-stage — it was
        # written by an earlier stage's panel (or the other track) and is only
        # being consumed now, after the project moved to a stage that has NO panel
        # (in_progress, paper_analyzed, analyzed …) or a DIFFERENT panel. Returning
        # its to_stage is exactly what produced the recorded `invalid transition
        # paper_analyzed->paper_planned` / `in_progress->clarified` / `in_progress->
        # specified` crashes (PROJ-575/601/577/606/644). consume_convergence_kickback
        # already unlinked the sentinel, so skip it and fall through to normal
        # forward routing — never drive routing from a stale cross-stage sentinel.
        if _STAGE_PANEL_LABEL.get(project.current_stage) != decision.stage_label:
            logger.warning(
                "ignoring stale/cross-stage convergence kickback for %s: sentinel "
                "panel %r does not match current stage %s (panel %r) — routing "
                "forward normally (issue #1139 invalid-transition fix)",
                project.id, decision.stage_label, project.current_stage.value,
                _STAGE_PANEL_LABEL.get(project.current_stage),
            )
            continue
        if decision.escalate:
            # AUTONOMOUS exhaustion handling (mirrors the execution path,
            # commit 3068830e3): a convergence panel NEVER parks a project at
            # human_input_needed (the sole human gate is publication DOI
            # sign-off). At the per-stage kickback cap:
            #   1. MODEL ESCALATION — bump to the next usable model tier
            #      (the shared execution_status ladder: registered default →
            #      free second-opinion → opt-in paid) so the panel/reviser
            #      retries with a stronger/different model, and re-enter the
            #      review loop at the SAME stage. ``consume_convergence_kickback``
            #      already reset the per-stage kickback count on this decision,
            #      so the retry starts from a clean count. The dispatch resolver
            #      threads the tier's model override into the doc-stage agent
            #      (and thus its convergence reviser/panel), exactly as the
            #      execution fix-loop implementer is threaded.
            #   2. ALL TIERS EXHAUSTED — RE-PLAN deterministically (no LLM):
            #      write a report of the unresolved concerns to the planner's
            #      ingestion file and route to the stage-appropriate re-work
            #      stage (research → PLANNED, paper → PAPER_PLANNED), resetting
            #      BOTH the model tier and the kickback count so the re-planned
            #      project starts clean.
            try:
                new_tier = execution_status.bump_model_tier(
                    project.id, repo_root=repo_root
                )
                logger.info(
                    "convergence panel %r hit the kickback cap for %s — "
                    "escalating to model tier %d (model=%r) and retrying the "
                    "review loop (NOT human_input_needed)",
                    decision.stage_label, project.id, new_tier,
                    execution_status.tier_model(new_tier)
                    or "<registered default>",
                )
                # Stay in the review loop at the current stage: the next tick
                # re-runs the panel with the escalated model. Returning the
                # current stage is a no-op transition (the project stays put
                # and is re-picked by the scheduler).
                return project.current_stage
            except ValueError:
                # No higher usable model tier → re-plan deterministically.
                _paper = _panel_is_paper(decision.stage_label)
                _write_convergence_replan_feedback(
                    project_dir, decision, paper=_paper
                )
                execution_status.reset_fix_loop(project.id, repo_root=repo_root)
                for _md in _convergence_kickback_memory_dirs(project_dir):
                    reset_kickback_count(_md, decision.stage_label)
                rework_stage = _panel_rework_stage(decision.stage_label)
                logger.info(
                    "convergence panel %r exhausted ALL model tiers for %s — "
                    "re-planning (deterministic concerns report written; "
                    "routing to %s; NOT human_input_needed). Last reason: %s",
                    decision.stage_label, project.id, rework_stage.value,
                    decision.reason,
                )
                return rework_stage
        try:
            target_stage = Stage(decision.to_stage or "")
        except ValueError:
            # A convergence kickback that names an INVALID stage is a ROUTING
            # BUG, not a human matter. Route to the SAFE deterministic
            # re-work fallback (research → PLANNED, paper → PAPER_PLANNED) so
            # the planner re-derives a clean approach — NEVER human_input_needed.
            rework_stage = _panel_rework_stage(decision.stage_label)
            logger.warning(
                "convergence_kickback to_stage %r is not a valid Stage "
                "(malformed routing) for %s; re-routing to %s and writing a "
                "deterministic re-plan note. Reason: %s",
                decision.to_stage, project.id, rework_stage.value,
                decision.reason,
            )
            _write_convergence_replan_feedback(
                project_dir, decision, paper=_panel_is_paper(decision.stage_label)
            )
            return rework_stage
        # Persist the panel's diagnosis where the content agent will read it.
        # When a kickback routes to a CONTENT stage (flesh_out / brainstorm),
        # the sentinel (and its concern bodies) was just DELETED by
        # consume_convergence_kickback — so without this the flesh-out agent
        # re-elaborates the SAME flawed idea and the downstream panel kicks it
        # straight back (the infinite spec↔flesh_out loop). Drop a durable,
        # human+LLM-readable markdown note the agent ingests on its next run.
        if target_stage in {Stage.FLESH_OUT_IN_PROGRESS, Stage.BRAINSTORMED}:
            _write_kickback_feedback(project_dir, decision)
        else:
            # Doc-stage target (specified / clarified / planned / tasked /
            # paper twins): the re-dispatched speckit agent revises the
            # EXISTING artifact in place and needs the panel's diagnosis
            # (spec 023 defect #19 companion — see _write_doc_kickback_feedback).
            _write_doc_kickback_feedback(project_dir, decision)
        logger.info(
            "adaptive convergence kickback: %s -> %s (count=%d, stage=%s)",
            project.id, target_stage.value, decision.count,
            decision.stage_label,
        )
        return target_stage

    # No pending convergence kickback at this stage → the panel converged this
    # tick (the project advances forward). Reset the kickback counter for the
    # panel that runs at the project's CURRENT stage so a later, legitimate
    # kickback starts from a clean count (F-20 Part B: "reset when the project
    # successfully advances PAST the kicked-back stage").
    panel_label = _STAGE_PANEL_LABEL.get(project.current_stage)
    if panel_label is not None:
        for mem_dir in _convergence_kickback_memory_dirs(project_dir):
            reset_kickback_count(mem_dir, panel_label)
        # The doc-stage kickback diagnosis is consumed: the panel at this
        # stage converged, so the persisted unresolved concerns are stale.
        (project_dir / ".specify" / "memory" / KICKBACK_FEEDBACK_FILENAME).unlink(
            missing_ok=True
        )

    # AUTONOMOUS handling of a lingering ``human_input_needed.yaml`` marker.
    # The convergence-kickback path no longer WRITES this marker (it escalates
    # the model tier then re-plans deterministically — see the escalate block
    # above). Other doc-stage caps (clarifier attempts, tasker analyze-loop,
    # paper-implement) may still drop the marker; per the user-directed rule —
    # human input is required ONLY for the publication DOI sign-off — NONE of
    # these may park the project. So instead of routing to HUMAN_INPUT_NEEDED,
    # consume the marker, write a DETERMINISTIC re-plan note from its reason,
    # and route to the stage-appropriate RE-WORK stage (research → PLANNED,
    # paper → PAPER_PLANNED) so the planner re-derives a clean approach. The
    # publication sign-off gate (awaiting_publication_signoff) is a SEPARATE
    # mechanism (signoff_gate) and never uses this marker.
    paper_marker = (
        project_dir / "paper" / ".specify" / "memory" / "human_input_needed.yaml"
    )
    research_marker = (
        project_dir / ".specify" / "memory" / "human_input_needed.yaml"
    )
    marker = (
        paper_marker if paper_marker.exists()
        else research_marker if research_marker.exists()
        else None
    )
    if marker is not None:
        is_paper = marker == paper_marker
        reason = _human_escalation_reason_from_markers(project_dir) or (
            "a bounded doc-stage loop hit its cap"
        )
        rework_stage = Stage.PAPER_PLANNED if is_paper else Stage.PLANNED
        # Reuse the deterministic re-plan ingestion file the planner reads.
        synthetic = KickbackDecision(
            to_stage=rework_stage.value,
            escalate=False,
            stage_label="paper_plan" if is_paper else "plan",
            reason=reason,
            count=0,
            unresolved_concerns=(),
        )
        _write_convergence_replan_feedback(project_dir, synthetic, paper=is_paper)
        marker.unlink(missing_ok=True)
        logger.info(
            "consumed a lingering human_input_needed marker for %s → "
            "re-planning at %s (deterministic note written; NOT "
            "human_input_needed). Reason: %s",
            project.id, rework_stage.value, reason,
        )
        return rework_stage

    # Scope-rejection from flesh-out (spec 023 / FR-014): an idea judged
    # infeasible for the execution environment is ARCHIVED and a
    # CONSTRAINED re-brainstorm is triggered automatically — the archived
    # idea + the infeasibility reason are written to
    # ``idea/kickback_feedback.md`` (the existing FleshOutAgent injection
    # point), and the project routes back to BRAINSTORMED where flesh_out
    # regenerates under the constraint. The loop is bounded by
    # ``IDEA_RETRY_CAP``; exhaustion takes the HONEST terminal
    # (``VALIDATOR_REJECTED`` — never picked again, publicly a rejected
    # idea), NEVER a human escalation. (Pre-023 this path parked the
    # project at HUMAN_INPUT_NEEDED with an instruction the system itself
    # could execute — the exact deal-breaker named in issue #303.)
    scope_stage = process_scope_rejection(project, project_dir)
    if scope_stage is not None:
        return scope_stage

    # Research-question-validator routing (spec 003 / D10):
    #   validator_revise   → roll back to FLESH_OUT_IN_PROGRESS so flesh_out
    #                        re-runs (with the [REVISED] question hint, if any)
    #   validator_rejected → roll back to BRAINSTORMED so flesh_out proposes
    #                        a fresh idea — bounded by the same FR-014
    #                        idea-retry cap (an unbounded reject→regenerate
    #                        cycle is the same defect class as scope-reject).
    # Sentinels are consumed (deleted) so subsequent ticks don't repeat the
    # routing decision. The "validated" sentinel is left in place as a
    # historical artifact (it doesn't override the default stage transition).
    validator_revise = (
        project_dir / ".specify" / "memory" / "research_question_revise.yaml"
    )
    if validator_revise.exists():
        validator_revise.unlink()
        return Stage.FLESH_OUT_IN_PROGRESS
    validator_rejected = (
        project_dir / ".specify" / "memory" / "research_question_rejected.yaml"
    )
    if validator_rejected.exists():
        validator_rejected.unlink()
        count = bump_count(
            project_dir / ".specify" / "memory", "idea_validator_reject"
        )
        if count > IDEA_RETRY_CAP:
            logger.warning(
                "%s: %d validator rejections (cap=%d) — honest terminal "
                "VALIDATOR_REJECTED (FR-014)",
                project.id, count, IDEA_RETRY_CAP,
            )
            return Stage.VALIDATOR_REJECTED
        return Stage.BRAINSTORMED

    cur = project.current_stage
    # Implementer special-case: stay in_progress until all tasks done.
    if cur == Stage.ANALYZED:
        # Lifecycle requires ANALYZED → IN_PROGRESS first; only then
        # IN_PROGRESS → RESEARCH_COMPLETE. If all tasks already done
        # (e.g. revision cycle came back with everything still
        # checked off), advance to IN_PROGRESS this tick and let the
        # next tick observe IN_PROGRESS + all-tasks-done → RESEARCH_COMPLETE.
        return Stage.IN_PROGRESS
    if cur == Stage.IN_PROGRESS:
        # issue #1139 D6: a task the implementer repeatedly cannot make pass is
        # recorded UNVERIFIABLE by the task-verifier (reopened `[ ]`, NEVER
        # force-accepted to `[X]`). Left alone, that reopened task keeps
        # _all_tasks_done False forever and the project wedges at in_progress. So
        # RE-PLAN the approach (a legal IN_PROGRESS→PLANNED edge, the same target
        # as execution exhaustion), write a deterministic note naming the tasks,
        # and clear the store so the re-planned cycle starts clean. This is the
        # honest loop-breaker that replaced the fail-open force-accept.
        from llmxive.state import unverifiable as _unverifiable

        if _unverifiable.has_unverifiable(project.id, repo_root=repo_root):
            _entries = _unverifiable.load(project.id, repo_root=repo_root)
            _write_unverifiable_replan_feedback(project_dir, _entries)
            _unverifiable.clear(project.id, repo_root=repo_root)
            logger.warning(
                "%s has %d repeatedly-unverifiable task(s) the implementer could "
                "not make pass — re-planning (IN_PROGRESS→PLANNED; NOT "
                "force-accepting incomplete work) [issue #1139 D6]",
                project.id, len(_entries),
            )
            return Stage.PLANNED
        # Spec 023 defect #25: research_complete now requires the analysis to
        # have actually RUN and produced real artifacts (execution_status.ok),
        # not just all task checkboxes ticked. Until the dedicated execution
        # phase succeeds we stay IN_PROGRESS (the run_one_step hook runs the
        # analysis / the implementer fixes re-opened tasks); past the
        # fix-round cap we escalate honestly rather than advance hollow work.
        if not _all_tasks_done(project_dir):
            return Stage.IN_PROGRESS
        if execution_status.is_ok(project.id, repo_root=repo_root):
            return Stage.RESEARCH_COMPLETE
        if (execution_status.fix_rounds(project.id, repo_root=repo_root)
                >= execution_status.MAX_EXECUTION_FIX_ROUNDS):
            # Autonomous exhaustion handling: a project NEVER parks at
            # human_input_needed for an execution failure (the sole human gate
            # is publication DOI sign-off). At the fix-round cap:
            #   1. MODEL ESCALATION — bump to the next usable model tier and
            #      RESET fix_rounds, retrying the full cap with a different
            #      (stronger/free-second-opinion/opt-in-paid) model. The project
            #      stays IN_PROGRESS; the dispatch resolver threads the tier's
            #      model override into the implementer call.
            #   2. ALL TIERS EXHAUSTED — RE-PLAN: write a DETERMINISTIC report
            #      (no LLM) of what worked + what failed + adjust-the-approach,
            #      reset BOTH fix_rounds and model_tier, and route to PLANNED.
            # FABRICATION does not escalate onto a PAID tier: the deterministic
            # fabrication guard fires on the code's OUTPUT regardless of which model
            # wrote it, so paying for a stronger model to re-fabricate is pure waste
            # (PROJ-284 reached a paid Claude tier still generating synthetic
            # brain-imaging data). Free escalation is still allowed (cheap; a
            # different free model might download real data instead of faking it);
            # once free tiers are exhausted it re-plans rather than paying.
            _latest = execution_status.load(project.id, repo_root=repo_root) or {}
            _is_fabrication = "fabricat" in (_latest.get("reason") or "").lower()
            try:
                new_tier = execution_status.bump_model_tier(
                    project.id, repo_root=repo_root, free_only=_is_fabrication
                )
                logger.info(
                    "execution fix-loop hit the cap for %s — escalating to "
                    "model tier %d (model=%r) and resetting fix_rounds%s",
                    project.id, new_tier,
                    execution_status.tier_model(new_tier) or "<registered default>",
                    " (free-only: fabrication)" if _is_fabrication else "",
                )
                return Stage.IN_PROGRESS
            except ValueError:
                # No higher usable tier → re-plan deterministically… but ONLY while
                # the OUTER loop has budget left. reset_fix_loop wipes fix_rounds AND
                # model_tier, so without a counter that survives it, a project whose
                # analysis simply cannot run climbed the whole ladder, re-planned to a
                # clean slate, and climbed it again — forever. PROJ-029 burned 843
                # implementer calls in ONE day doing exactly this, and because a
                # re-opened project still looks nearly-done, the scheduler handed it a
                # worker every tick. Past the cap the honest answer is that this
                # analysis is not executable here — a terminal rejection, not another
                # lap (and NOT human_input_needed: the sole human gate is DOI sign-off).
                rec = execution_status.load(project.id, repo_root=repo_root) or {}
                if (execution_status.replan_rounds(project.id, repo_root=repo_root)
                        >= execution_status.MAX_REPLAN_ROUNDS):
                    _fc = rec.get("failure_class") or "unknown"
                    logger.warning(
                        "execution fix-loop exhausted ALL model tiers AND all %d "
                        "re-plans for %s (%d total failed attempts, "
                        "failure_class=%s) — the analysis is not executable in "
                        "this environment; terminal AGENT_BLOCKED (an "
                        "operator-clearable, re-openable sink) rather than "
                        "VALIDATOR_REJECTED, so an infra/data-blocked GOOD idea is "
                        "NOT conflated with an idea-quality rejection "
                        "(issue #1139 P1-2 / sec 3.7)",
                        execution_status.MAX_REPLAN_ROUNDS, project.id,
                        execution_status.total_attempts(project.id, repo_root=repo_root),
                        _fc,
                    )
                    _write_execution_replan_feedback(project_dir, rec)
                    return Stage.AGENT_BLOCKED
                _write_execution_replan_feedback(project_dir, rec)
                execution_status.reset_fix_loop(project.id, repo_root=repo_root)
                logger.info(
                    "execution fix-loop exhausted ALL model tiers for %s — "
                    "re-planning (deterministic report written; routing to "
                    "PLANNED; NOT human_input_needed)",
                    project.id,
                )
                return Stage.PLANNED
        return Stage.IN_PROGRESS

    # Paper-Implementer special-case: stay paper_in_progress until ALL
    # preconditions are met (tasks done + LaTeX builds + citations
    # verified + proofreader clean).
    if cur in {Stage.PAPER_ANALYZED, Stage.PAPER_IN_PROGRESS}:
        if _paper_complete_preconditions_met(project.id, project_dir, repo_root=repo_root):
            return Stage.PAPER_COMPLETE
        return Stage.PAPER_IN_PROGRESS

    # Review stages never reach here: ``run_one_step`` evaluates AND
    # persists the Advancement-Evaluator's full result before calling
    # ``_decide_next_stage`` (spec 023 / FR-001 — the old stage-only
    # return here was the issue-#303 discard bug).

    # Spec 015 T042 / FR-034: the 7 transient revision stages were
    # DELETED. Routing decisions for any non-convergence are now made
    # by ``advancement.py``'s engine-adapter path (which emits a
    # KickbackRecord whose ``to_stage`` is one of the stable stages
    # below). Only the kept "terminal-ish judgment" stages still need
    # forward routing here:
    #   research_full_revision  → clarified
    #   research_rejected       → brainstormed
    #   paper_fundamental_flaws → brainstormed
    if cur == Stage.RESEARCH_FULL_REVISION:
        # FULL revision: the ANALYSIS itself must change (e.g. data_quality found
        # the braid index populated for only ~23% of records, or the execution
        # produced fabricated numbers — no doc-edit round fixes that). Kick back to
        # IMPLEMENTATION (in_progress), NOT all the way to clarified: research_full_
        # revision is not a resting step, and re-running the question/spec/plan is
        # overkill when the fix is to re-do the analysis. The implementer re-runs
        # under the (now fabrication-gated) execution gate. RESET the revision-round
        # budget so the regenerated analysis gets a fresh review cycle instead of
        # returning already-exhausted (which would loop straight back here).
        # Bounded by the convergence-kickback cap → human escalation.
        if repo_root is not None:
            _reset_revision_rounds(project.id, repo_root=repo_root)
        return Stage.IN_PROGRESS
    if cur == Stage.RESEARCH_REJECTED:
        return Stage.BRAINSTORMED
    if cur == Stage.PAPER_FUNDAMENTAL_FLAWS:
        return Stage.BRAINSTORMED
    # Spec 015 T035 / FR-036 + FR-054 (discrepancy #2 / #58): PAPER_ACCEPTED
    # does NOT shortcut to POSTED. PAPER_ACCEPTED -> AWAITING_PUBLICATION_SIGNOFF
    # is a pass-through flip here; at AWAITING the `paper_publisher` agent runs
    # (STAGE_TO_AGENT) and is the SOLE driver of -> POSTED: it self-gates on the
    # maintainer sign-off and only transitions after the real compile + Zenodo
    # DOI + publication.yaml succeed. We must NOT auto-advance AWAITING -> POSTED
    # here: doing so would mark a project POSTED with no DOI/publication.yaml if
    # the publisher hadn't (or couldn't) run. So AWAITING stays AWAITING until
    # the publisher itself sets POSTED (seen on the post-agent reload).
    if cur == Stage.PAPER_ACCEPTED:
        return Stage.AWAITING_PUBLICATION_SIGNOFF
    if cur == Stage.AWAITING_PUBLICATION_SIGNOFF:
        return Stage.AWAITING_PUBLICATION_SIGNOFF

    return STAGE_AFTER_AGENT.get(cur, cur)


def _collect_idea_inputs(project_dir: Path, repo: Path) -> list[str]:
    idea_dir = project_dir / "idea"
    if not idea_dir.is_dir():
        return []
    return [str(p.relative_to(repo)) for p in sorted(idea_dir.glob("*.md"))]


__all__ = ["STAGE_AFTER_AGENT", "STAGE_TO_AGENT", "run_one_step"]
