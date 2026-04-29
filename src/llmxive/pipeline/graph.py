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

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

from llmxive.agents.advancement import evaluate as advancement_evaluate
from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.lifecycle import is_valid_transition
from llmxive.agents.paper_initializer import PaperInitializerAgent
from llmxive.agents.project_initializer import (
    ProjectInitializerAgent,
    transition_to_project_initialized,
)
from llmxive.agents.research_reviewer import ResearchReviewerAgent
from llmxive.agents import registry as registry_loader
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
    BackendName,
    Project,
    Stage,
)


# Map (current_stage, agent_name) — the agent invoked when a project is
# at the keyed stage. The agent's run() drives the transition to the
# next stage.
STAGE_TO_AGENT: dict[Stage, str] = {
    Stage.FLESH_OUT_COMPLETE: "project_initializer",
    Stage.PROJECT_INITIALIZED: "specifier",
    Stage.SPECIFIED: "clarifier",
    Stage.CLARIFIED: "planner",
    Stage.PLANNED: "tasker",
    Stage.TASKED: "tasker",  # tasker also drives analyze
    Stage.ANALYZE_IN_PROGRESS: "tasker",
    Stage.ANALYZED: "implementer",
    Stage.IN_PROGRESS: "implementer",
    # US3: at research_complete the project waits for at least one review
    # record to exist, then auto-transitions to research_review (handled
    # by advancement.evaluate); the dispatch table picks it up here.
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
}


# Stage transitions performed automatically by the pipeline graph after
# each agent run — for non-LLM stages (e.g., the Implementer marks tasks
# off and we transition to research_complete when all are done).
STAGE_AFTER_AGENT: dict[Stage, Stage] = {
    Stage.FLESH_OUT_COMPLETE: Stage.PROJECT_INITIALIZED,
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
    "project_initializer": ProjectInitializerAgent,
    "research_reviewer": ResearchReviewerAgent,
    "paper_initializer": PaperInitializerAgent,
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
    # LaTeX build: only checked if a main.tex exists.
    paper_source = project_dir / "paper" / "source" / "main.tex"
    if paper_source.exists():
        from llmxive.agents.latex_build import build_paper

        build_result = build_paper(project_id, repo_root=repo_root)
        if not build_result.get("ok"):
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
                "updated_at": datetime.now(timezone.utc),
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
        agent = _NON_SPECKIT_AGENTS[agent_name](entry)
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
        run_agent(agent, ctx, repo_root=repo)
    elif agent_name in _SPECKIT_AGENTS:
        speckit_agent = _SPECKIT_AGENTS[agent_name](entry)
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

    # Update project stage based on the agent that just ran.
    next_stage = _decide_next_stage(project, project_dir, repo_root=repo)
    if next_stage != project.current_stage:
        if not is_valid_transition(project.current_stage, next_stage):
            raise RuntimeError(
                f"invalid transition {project.current_stage.value} -> {next_stage.value}"
            )
        project = project.model_copy(
            update={
                "current_stage": next_stage,
                "updated_at": datetime.now(timezone.utc),
                "last_run_id": run_id,
            }
        )
    project_store.save(project, repo_root=repo)
    return project


def _decide_next_stage(
    project: Project, project_dir: Path, *, repo_root: Path | None = None
) -> Stage:
    """Pick the appropriate post-agent stage for the project."""
    if _human_input_marker(project_dir):
        return Stage.HUMAN_INPUT_NEEDED

    cur = project.current_stage
    # Implementer special-case: stay in_progress until all tasks done.
    if cur in {Stage.ANALYZED, Stage.IN_PROGRESS}:
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
    # accumulated review records.
    if cur == Stage.RESEARCH_REVIEW:
        evaluated = advancement_evaluate(project, repo_root=repo_root)
        return evaluated.current_stage

    # Paper-Reviewer (US5) — same pattern.
    if cur == Stage.PAPER_REVIEW:
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
    if cur == Stage.PAPER_ACCEPTED:
        return Stage.POSTED

    return STAGE_AFTER_AGENT.get(cur, cur)


def _collect_idea_inputs(project_dir: Path, repo: Path) -> list[str]:
    idea_dir = project_dir / "idea"
    if not idea_dir.is_dir():
        return []
    return [str(p.relative_to(repo)) for p in sorted(idea_dir.glob("*.md"))]


__all__ = ["run_one_step", "STAGE_TO_AGENT", "STAGE_AFTER_AGENT"]
