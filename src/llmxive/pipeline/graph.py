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
from llmxive.config import repo_root as _repo_root
from llmxive.pipeline._kickback import (
    CONVERGENCE_KICKBACK_CAP,
    KickbackDecision,
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


def _all_tasks_done(project_dir: Path) -> bool:
    candidates = sorted(project_dir.glob("specs/*/tasks.md"))
    if not candidates:
        return False
    text = candidates[0].read_text(encoding="utf-8")
    has_any = "[ ]" in text or "[X]" in text or "[x]" in text
    return has_any and "[ ]" not in text


def _all_paper_tasks_done(project_dir: Path) -> bool:
    candidates = sorted((project_dir / "paper").glob("specs/*/tasks.md"))
    if not candidates:
        return False
    text = candidates[0].read_text(encoding="utf-8")
    has_any = "[ ]" in text or "[X]" in text or "[x]" in text
    return has_any and "[ ]" not in text


def _human_input_marker(project_dir: Path) -> bool:
    return (
        (project_dir / ".specify" / "memory" / "human_input_needed.yaml").exists()
        or (project_dir / "paper" / ".specify" / "memory" / "human_input_needed.yaml").exists()
    )


def _write_human_escalation_marker(
    memory_dir: Path, reason: str, stage_label: str
) -> None:
    """Drop a ``human_input_needed.yaml`` recording why the project escalated
    (convergence-kickback cap exceeded or unroutable target). The reason is
    also surfaced onto the Project's ``human_escalation_reason`` field by
    ``run_one_step`` (read back from this marker)."""
    import yaml

    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "human_input_needed.yaml").write_text(
        yaml.safe_dump({"reason": reason, "stage": stage_label}), encoding="utf-8"
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
    # And the produced PDF MUST exist on disk (latex_build sometimes
    # reports ok without producing the artifact).
    paper_pdf = project_dir / "paper" / "source" / "main.pdf"
    if not paper_pdf.exists():
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
            default_model=entry.default_model,
            prompt_version=entry.prompt_version,
            agent_name=entry.name,
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
        except StagePanelEscalation as exc:
            # Engine failure: the panel wrote human_input_needed.yaml. Fall
            # through so _decide_next_stage routes to HUMAN_INPUT_NEEDED rather
            # than crashing the entire run loop with an unhandled exception.
            logger.warning("stage-panel escalation for %s: %s", project.id, exc)
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
    the research-side and the paper-side ``.specify/memory/`` (mirrors
    ``_human_input_marker``)."""
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
        if decision.escalate:
            reason = (
                f"Convergence kickback cap exceeded: the {decision.stage_label!r} "
                f"convergence panel kicked the project back "
                f"{decision.count} time(s) (cap={CONVERGENCE_KICKBACK_CAP}) without "
                f"reaching unanimous acceptance. A human must intervene. "
                f"Last reason: {decision.reason}"
            )
            _write_human_escalation_marker(mem_dir, reason, decision.stage_label)
            return Stage.HUMAN_INPUT_NEEDED
        try:
            target_stage = Stage(decision.to_stage or "")
        except ValueError:
            logger.warning(
                "convergence_kickback to_stage %r is not a valid Stage; "
                "escalating %s to human_input_needed",
                decision.to_stage, project.id,
            )
            _write_human_escalation_marker(
                mem_dir,
                f"convergence kickback named unknown stage "
                f"{decision.to_stage!r}; cannot auto-route. {decision.reason}",
                decision.stage_label,
            )
            return Stage.HUMAN_INPUT_NEEDED
        # Persist the panel's diagnosis where the content agent will read it.
        # When a kickback routes to a CONTENT stage (flesh_out / brainstorm),
        # the sentinel (and its concern bodies) was just DELETED by
        # consume_convergence_kickback — so without this the flesh-out agent
        # re-elaborates the SAME flawed idea and the downstream panel kicks it
        # straight back (the infinite spec↔flesh_out loop). Drop a durable,
        # human+LLM-readable markdown note the agent ingests on its next run.
        if target_stage in {Stage.FLESH_OUT_IN_PROGRESS, Stage.BRAINSTORMED}:
            _write_kickback_feedback(project_dir, decision)
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

    if _human_input_marker(project_dir):
        return Stage.HUMAN_INPUT_NEEDED

    # Scope-rejection from flesh-out: the brainstorm agent does NOT
    # currently re-propose a different idea for an existing project (it
    # only seeds new projects), so rolling back to BRAINSTORMED creates
    # an infinite loop where flesh-out keeps re-rejecting the same body.
    # Instead, archive the rejected idea file and escalate the project to
    # HUMAN_INPUT_NEEDED — a human (or a future brainstorm-replace agent)
    # can then either propose a new idea body or terminate the project.
    # The marker is kept (not deleted) so the human-input UI can see why.
    scope_marker = project_dir / ".specify" / "memory" / "scope_rejected.yaml"
    if scope_marker.exists():
        # Archive the rejected idea so the human-input handler (or a
        # follow-up brainstorm-replace pass) sees clearly which idea was
        # rejected without it remaining in idea/<slug>.md.
        idea_dir = project_dir / "idea"
        if idea_dir.is_dir():
            archive_dir = idea_dir / ".archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            for md in sorted(idea_dir.glob("*.md")):
                # Don't archive diagnostic side-files; just the canonical
                # idea body. We move only non-diagnostic .md files.
                if md.name in {
                    "research_question_validation.md",
                }:
                    continue
                target = archive_dir / f"{ts}-{md.name}"
                md.rename(target)
        return Stage.HUMAN_INPUT_NEEDED

    # Research-question-validator routing (spec 003 / D10):
    #   validator_revise   → roll back to FLESH_OUT_IN_PROGRESS so flesh_out
    #                        re-runs (with the [REVISED] question hint, if any)
    #   validator_rejected → roll back to BRAINSTORMED so brainstorm proposes
    #                        a fresh idea
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
        if _all_tasks_done(project_dir):
            return Stage.RESEARCH_COMPLETE
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
        return Stage.CLARIFIED
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
