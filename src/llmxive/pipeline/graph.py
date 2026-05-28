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

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from llmxive.agents import registry as registry_loader
from llmxive.agents.advancement import evaluate as advancement_evaluate
from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.idea_lifecycle import (
    BrainstormAgent,
    FleshOutAgent,
    IdeaSelectorAgent,
    ResearchQuestionValidatorAgent,
)
from llmxive.agents.lifecycle import is_valid_transition
from llmxive.agents.paper_initializer import PaperInitializerAgent
from llmxive.agents.paper_reviewer import PaperReviewerAgent
from llmxive.agents.project_initializer import (
    ProjectInitializerAgent,
)
from llmxive.agents.research_reviewer import ResearchReviewerAgent
from llmxive.agents.runner import run_agent
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


_NON_SPECKIT_AGENTS: dict[str, Callable[[AgentRegistryEntry], Agent]] = {
    "brainstorm": BrainstormAgent,
    "flesh_out": FleshOutAgent,
    "research_question_validator": ResearchQuestionValidatorAgent,
    "idea_selector": IdeaSelectorAgent,
    "project_initializer": ProjectInitializerAgent,
    "research_reviewer": ResearchReviewerAgent,
    "paper_initializer": PaperInitializerAgent,
    "paper_reviewer": PaperReviewerAgent,
}

_SPECKIT_AGENTS: dict[str, Callable[[AgentRegistryEntry], SlashCommandAgent]] = {
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
    repo = repo_root or Path(__file__).resolve().parent.parent.parent.parent
    run_id = run_id or str(uuid4())

    agent_name = STAGE_TO_AGENT.get(project.current_stage)

    # Revision states are transient: route them forward immediately
    # without invoking an agent (the next scheduled run will pick the
    # routed target up).
    if agent_name is None and project.current_stage in {
        Stage.RESEARCH_MINOR_REVISION,
        Stage.RESEARCH_FULL_REVISION,
        Stage.RESEARCH_REJECTED,
        Stage.PAPER_MINOR_REVISION,
        Stage.PAPER_MAJOR_REVISION_WRITING,
        Stage.PAPER_MAJOR_REVISION_SCIENCE,
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
        # Stages handled elsewhere (paper-review stages, terminal states):
        # ask the Advancement-Evaluator to evaluate review records.
        return advancement_evaluate(project, repo_root=repo)

    entry = registry_loader.get(agent_name, repo_root=repo)
    project_dir = repo / "projects" / project.id
    project_dir.mkdir(parents=True, exist_ok=True)

    if agent_name in _NON_SPECKIT_AGENTS:
        # Special-case for review stages: dispatch to all specialist
        # reviewers (each on a focused prompt) plus the generic
        # reviewer. The Advancement-Evaluator gates on every
        # specialist accepting (FR-028); failing to dispatch them
        # means projects can never satisfy the gate.
        agents_to_run: list[str] = []
        if project.current_stage in {Stage.RESEARCH_COMPLETE, Stage.RESEARCH_REVIEW}:
            agents_to_run = [
                n for n in registry_loader.list_names(repo_root=repo)
                if n == "research_reviewer" or n.startswith("research_reviewer_")
            ]
        elif project.current_stage in {Stage.PAPER_COMPLETE, Stage.PAPER_REVIEW}:
            agents_to_run = [
                n for n in registry_loader.list_names(repo_root=repo)
                if n == "paper_reviewer" or n.startswith("paper_reviewer_")
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
                    print(f"[graph] reviewer {an!r} failed: {exc}")
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
        speckit_agent.run(sk_ctx)
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
        # is the human-input stage (typically from flesh-out scope-reject).
        if next_stage == Stage.HUMAN_INPUT_NEEDED and not project.human_escalation_reason:
            update_fields["human_escalation_reason"] = (
                "flesh-out judged idea out of GitHub-Actions-feasible scope; "
                "idea archived under projects/<id>/idea/.archive/. Replace with "
                "a tighter brainstorm or terminate."
            )
        project = project.model_copy(update=update_fields)
        # Issue-lifecycle hook: close the linked GitHub issue when the
        # project transitions to POSTED. Best-effort — failures here do
        # not abort the pipeline.
        if next_stage == Stage.POSTED:
            try:
                from llmxive.integrations import issues as issues_mod
                issues_mod.close_issue_for_project(repo, project)
            except Exception as exc:  # pragma: no cover — telemetry only
                print(f"[graph] issue-close hook failed for {project.id}: {exc}")
    project_store.save(project, repo_root=repo)
    return project


def _decide_next_stage(
    project: Project, project_dir: Path, *, repo_root: Path | None = None
) -> Stage:
    """Pick the appropriate post-agent stage for the project."""
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

    # Research-reviewer leaves the project at research_review and lets
    # the Advancement-Evaluator decide the next stage based on the
    # accumulated review records. We treat RESEARCH_COMPLETE the same
    # way once the specialists have run (the review records already
    # exist on disk, so advancement_evaluate can decide).
    if cur in {Stage.RESEARCH_COMPLETE, Stage.RESEARCH_REVIEW}:
        evaluated = advancement_evaluate(project, repo_root=repo_root)
        return evaluated.current_stage

    # Paper-Reviewer (US5) — same pattern.
    if cur in {Stage.PAPER_COMPLETE, Stage.PAPER_REVIEW}:
        evaluated = advancement_evaluate(project, repo_root=repo_root)
        return evaluated.current_stage

    # US3 revision-state routing (T068). These states are transient —
    # they record what the reviewer pool decided, and the very next
    # scheduled run routes the project to the appropriate prior stage
    # so the right agent picks it up:
    #   research_minor_revision → tasked   (re-Tasker)
    #   research_full_revision  → clarified (back to Specifier
    #                             effectively, via Planner→Tasker)
    #   research_rejected       → brainstormed (back to Brainstorm)
    if cur == Stage.RESEARCH_MINOR_REVISION:
        return Stage.TASKED
    if cur == Stage.RESEARCH_FULL_REVISION:
        return Stage.CLARIFIED
    if cur == Stage.RESEARCH_REJECTED:
        return Stage.BRAINSTORMED

    # US5 paper-revision routing.
    if cur == Stage.PAPER_MINOR_REVISION:
        return Stage.PAPER_TASKED
    if cur == Stage.PAPER_MAJOR_REVISION_WRITING:
        return Stage.PAPER_CLARIFIED
    if cur == Stage.PAPER_MAJOR_REVISION_SCIENCE:
        return Stage.CLARIFIED  # back to research clarified
    if cur == Stage.PAPER_FUNDAMENTAL_FLAWS:
        return Stage.BRAINSTORMED
    # Spec 015 T035 / FR-036 + FR-054: PAPER_ACCEPTED no longer shortcuts directly
    # to POSTED (the publisher was unwired AND no manual DOI sign-off existed).
    # Now: PAPER_ACCEPTED -> AWAITING_PUBLICATION_SIGNOFF (the publisher assembles
    # the manuscript during this transition), then AWAITING_PUBLICATION_SIGNOFF ->
    # POSTED ONLY when the maintainer's sign-off record
    # (`.specify/memory/publication_signoff.yaml`) has been written via
    # `llmxive publish-approve`. The publisher itself also enforces this gate
    # (defense in depth) so no DOI is ever minted without a recorded approval.
    if cur == Stage.PAPER_ACCEPTED:
        return Stage.AWAITING_PUBLICATION_SIGNOFF
    if cur == Stage.AWAITING_PUBLICATION_SIGNOFF:
        from llmxive.speckit._publication_signoff import has_signoff
        if has_signoff(project_dir / ".specify" / "memory"):
            return Stage.POSTED
        return Stage.AWAITING_PUBLICATION_SIGNOFF

    return STAGE_AFTER_AGENT.get(cur, cur)


def _collect_idea_inputs(project_dir: Path, repo: Path) -> list[str]:
    idea_dir = project_dir / "idea"
    if not idea_dir.is_dir():
        return []
    return [str(p.relative_to(repo)) for p in sorted(idea_dir.glob("*.md"))]


__all__ = ["STAGE_AFTER_AGENT", "STAGE_TO_AGENT", "run_one_step"]
