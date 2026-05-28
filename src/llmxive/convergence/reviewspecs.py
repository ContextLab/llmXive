"""Per-stage ReviewSpec registry (spec 015 T048, FR-027–031).

``reviewspec_for(stage) -> ReviewSpec | None`` is the SSoT lookup the engine
consults to drive each reviewable step. EXEMPT stages return ``None`` (no
convergence loop). See ``contracts/reviewspec-registry.md`` for the full table.

For stages whose **panel prompts haven't been authored yet** (T049–T053) or whose
**agent wiring hasn't landed** (T054–T059), this registry installs TODO-placeholder
reviewers/reviser that conform to the Protocol but raise a clear pointer to the
follow-up task when invoked - fail-loud rather than silently produce empty
verdicts. Each placeholder names the task that will replace it.
"""

from __future__ import annotations

from .types import Concern, ConcernResponse, ReviewSpec, Severity

# --- EXEMPT stages (FR-029): no convergence loop runs here ---------------

EXEMPT_STAGES: frozenset[str] = frozenset({
    "project_initializer",
    "paper_initializer",
    "paper_publisher",
    "task_atomizer",
    "task_joiner",
    "status_reporter",
    "repository_hygiene",
})


# --- TODO placeholders ----------------------------------------------------


class _TodoReviewer:
    """Protocol-conformant placeholder. Raises a clear, actionable error when
    the engine invokes it, naming the task that will replace it."""

    def __init__(self, lens_name: str, *, prompt_task: str, wiring_task: str) -> None:
        self.name = lens_name
        self._prompt_task = prompt_task
        self._wiring_task = wiring_task

    def _err(self, phase: str) -> NotImplementedError:
        return NotImplementedError(
            f"reviewer '{self.name}' is a registry placeholder - its prompt is authored "
            f"in {self._prompt_task} and the agent wiring lands in {self._wiring_task}. "
            f"The engine's {phase} phase was invoked before either landed."
        )

    def identify(self, artifacts, *, constitution, advisory):  # type: ignore[no-untyped-def]
        raise self._err("R1 identify")

    def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):  # type: ignore[no-untyped-def]
        raise self._err("R3 re-review")


class _TodoReviser:
    """Protocol-conformant placeholder Reviser."""

    def __init__(self, name: str, *, wiring_task: str) -> None:
        self.name = name
        self._wiring_task = wiring_task

    def revise(  # type: ignore[no-untyped-def]
        self, artifacts: dict[str, str], concerns: list[Concern],
    ) -> tuple[dict[str, str], list[ConcernResponse]]:
        raise NotImplementedError(
            f"reviser '{self.name}' is a registry placeholder - the agent wiring "
            f"lands in {self._wiring_task}. The engine's R2 revise phase was invoked "
            f"before that wiring landed."
        )


def _todo_reviewers(lenses: list[str], *, prompt_task: str, wiring_task: str) -> list[_TodoReviewer]:
    return [_TodoReviewer(lens, prompt_task=prompt_task, wiring_task=wiring_task) for lens in lenses]


# --- Per-stage ReviewSpec table (FR-027/FR-028 + contracts/reviewspec-registry.md) ---


def _spec_idea() -> ReviewSpec:
    return ReviewSpec(
        stage="flesh_out_complete",
        artifacts=["idea/*.md"],
        reviewers=_todo_reviewers(
            ["rq_validity", "novelty", "feasibility", "idea_quality"],
            prompt_task="T049", wiring_task="T054",
        ),
        reviser=_TodoReviser("flesh_out", wiring_task="T054"),
        kickback_routing={
            Severity.WRITING: "brainstormed",
            Severity.REQUIREMENT: "brainstormed",
            Severity.METHODOLOGY: "brainstormed",
            Severity.SCIENCE: "brainstormed",
            Severity.FATAL: "brainstormed",
        },
        overflow_goal="preserve the full argument chain + idea-source citations verbatim",
        advance_stage="validated",
        constitution_input=False,  # constitution doesn't exist yet at idea stage
    )


def _spec_research_spec() -> ReviewSpec:
    """Spec convergence unit (specifier + clarifier collapsed; reviewed ONCE after clarify)."""
    return ReviewSpec(
        stage="clarified",
        artifacts=["specs/*/spec.md"],
        reviewers=_todo_reviewers(
            ["requirements_coverage", "internal_consistency", "testability", "scope"],
            prompt_task="T050", wiring_task="T054",
        ),
        reviser=_TodoReviser("specifier+clarifier", wiring_task="T054"),
        kickback_routing={
            Severity.WRITING: "project_initialized",
            Severity.REQUIREMENT: "project_initialized",
            Severity.METHODOLOGY: "flesh_out_in_progress",  # idea-root cause
            Severity.SCIENCE: "flesh_out_in_progress",
            Severity.FATAL: "flesh_out_in_progress",
        },
        overflow_goal="preserve every FR/SC id + the source idea verbatim",
        advance_stage="planned",
        constitution_input=True,
    )


def _spec_research_plan() -> ReviewSpec:
    return ReviewSpec(
        stage="planned",
        artifacts=["specs/*/plan.md", "specs/*/research.md", "specs/*/data-model.md",
                   "specs/*/quickstart.md", "specs/*/contracts/*"],
        reviewers=_todo_reviewers(
            ["methodology", "spec_coverage", "data_resources", "plan_consistency"],
            prompt_task="T051", wiring_task="T056",
        ),
        reviser=_TodoReviser("planner", wiring_task="T056"),
        kickback_routing={
            Severity.WRITING: "planned",  # re-plan
            Severity.REQUIREMENT: "clarified",  # spec gap
            Severity.METHODOLOGY: "clarified",
            Severity.SCIENCE: "clarified",
            Severity.FATAL: "clarified",
        },
        overflow_goal="preserve every FR/SC id and every spec constraint verbatim",
        advance_stage="tasked",
        constitution_input=True,
    )


def _spec_research_tasks() -> ReviewSpec:
    return ReviewSpec(
        stage="tasked",
        artifacts=["specs/*/tasks.md"],
        reviewers=_todo_reviewers(
            ["coverage", "ordering", "executability", "constraint_preservation"],
            prompt_task="T052", wiring_task="T057",
        ),
        reviser=_TodoReviser("tasker", wiring_task="T057"),
        kickback_routing={
            Severity.WRITING: "tasked",
            Severity.REQUIREMENT: "planned",  # plan flaw
            Severity.METHODOLOGY: "planned",
            Severity.SCIENCE: "planned",
            Severity.FATAL: "planned",
        },
        overflow_goal="preserve every FR/SC/task id verbatim",
        advance_stage="analyzed",
        constitution_input=True,
    )


def _spec_research_unit() -> ReviewSpec:
    """Existing 8-panel research review (formalized as R1/R3 here)."""
    return ReviewSpec(
        stage="research_review",
        artifacts=["code/**", "data/**", "results.md"],
        reviewers=_todo_reviewers(
            ["idea_quality", "creativity", "implementation_correctness",
             "implementation_completeness", "code_quality", "data_quality",
             "filesystem_hygiene", "research_reviewer"],  # generic + 7 specialists
            prompt_task="reuse-existing", wiring_task="T058",
        ),
        reviser=_TodoReviser("implementer", wiring_task="T058"),
        kickback_routing={
            Severity.WRITING: "research_review",  # code-level fixed in loop
            Severity.CODE: "research_review",
            Severity.REQUIREMENT: "tasked",  # missing task
            Severity.METHODOLOGY: "planned",  # unsound methodology
            Severity.SCIENCE: "brainstormed",  # trivial RQ → idea
            Severity.FATAL: "brainstormed",
        },
        overflow_goal="preserve all numeric results + the code/data tree names",
        advance_stage="research_accepted",
        constitution_input=True,
    )


def _spec_paper_spec() -> ReviewSpec:
    return ReviewSpec(
        stage="paper_clarified",
        artifacts=["paper/specs/*/spec.md"],
        reviewers=_todo_reviewers(
            ["reader_scenario_coverage", "claims_supported",
             "required_sections_figures", "scope_vs_research"],
            prompt_task="T053", wiring_task="T055",
        ),
        reviser=_TodoReviser("paper_specifier+paper_clarifier", wiring_task="T055"),
        kickback_routing={
            Severity.WRITING: "paper_drafting_init",
            Severity.REQUIREMENT: "paper_drafting_init",
            Severity.METHODOLOGY: "clarified",  # science-root → research side
            Severity.SCIENCE: "clarified",
            Severity.FATAL: "clarified",
        },
        overflow_goal="preserve every FR/SC id + the research spec verbatim",
        advance_stage="paper_planned",
        constitution_input=True,
    )


def _spec_paper_plan() -> ReviewSpec:
    return ReviewSpec(
        stage="paper_planned",
        artifacts=["paper/specs/*/plan.md", "paper/specs/*/research.md",
                   "paper/specs/*/data-model.md", "paper/specs/*/quickstart.md",
                   "paper/specs/*/contracts/*"],
        reviewers=_todo_reviewers(
            ["paper_structure", "spec_section_coverage", "plan_constitution_consistency"],
            prompt_task="T053", wiring_task="T056",
        ),
        reviser=_TodoReviser("paper_planner", wiring_task="T056"),
        kickback_routing={
            Severity.WRITING: "paper_planned",
            Severity.REQUIREMENT: "paper_clarified",
            Severity.METHODOLOGY: "paper_clarified",
            Severity.SCIENCE: "paper_clarified",
            Severity.FATAL: "paper_clarified",
        },
        overflow_goal="preserve every FR/SC id + paper plan constraints verbatim",
        advance_stage="paper_tasked",
        constitution_input=True,
    )


def _spec_paper_tasks() -> ReviewSpec:
    return ReviewSpec(
        stage="paper_tasked",
        artifacts=["paper/specs/*/tasks.md"],
        reviewers=_todo_reviewers(
            ["coverage", "ordering", "executability", "constraint_preservation"],
            prompt_task="T053", wiring_task="T057",
        ),
        reviser=_TodoReviser("paper_tasker", wiring_task="T057"),
        kickback_routing={
            Severity.WRITING: "paper_tasked",
            Severity.REQUIREMENT: "paper_planned",
            Severity.METHODOLOGY: "paper_planned",
            Severity.SCIENCE: "paper_planned",
            Severity.FATAL: "paper_planned",
        },
        overflow_goal="preserve every paper-task id verbatim",
        advance_stage="paper_analyzed",
        constitution_input=True,
    )


def _spec_paper_implement() -> ReviewSpec:
    """Existing 12-panel paper review (formalized as R1/R3 here)."""
    return ReviewSpec(
        stage="paper_review",
        artifacts=["paper/source/**.tex", "paper/figures/**", "paper/pdf/**"],
        reviewers=_todo_reviewers(
            ["paper_reviewer", "claim_accuracy", "logical_consistency",
             "statistical_analysis", "scientific_evidence", "figure_critic",
             "jargon_police", "overreach", "safety_ethics", "code_quality",
             "data_quality", "text_formatting", "writing_quality"],
            prompt_task="reuse-existing", wiring_task="T059",
        ),
        reviser=_TodoReviser("paper_implementer", wiring_task="T059"),
        kickback_routing={
            Severity.WRITING: "paper_clarified",  # major revision writing
            Severity.CODE: "paper_review",  # in-loop fix
            Severity.REQUIREMENT: "paper_clarified",
            Severity.METHODOLOGY: "clarified",  # science-root → research side
            Severity.SCIENCE: "clarified",
            Severity.FATAL: "brainstormed",
        },
        overflow_goal=("preserve every section heading, numeric claim, citation, "
                       "ref/label, and figure caption verbatim"),
        advance_stage="paper_accepted",
        constitution_input=True,
    )


_REGISTRY: dict[str, ReviewSpec] = {}


def _build_registry() -> dict[str, ReviewSpec]:
    """Build the per-stage map lazily so importing this module is side-effect-free."""
    if _REGISTRY:
        return _REGISTRY
    builders = (
        _spec_idea, _spec_research_spec, _spec_research_plan, _spec_research_tasks,
        _spec_research_unit, _spec_paper_spec, _spec_paper_plan, _spec_paper_tasks,
        _spec_paper_implement,
    )
    for b in builders:
        spec = b()
        _REGISTRY[spec.stage] = spec
    return _REGISTRY


def reviewspec_for(stage: str) -> ReviewSpec | None:
    """Return the per-step ``ReviewSpec``, or ``None`` for EXEMPT / non-reviewable
    stages. The mapping mirrors ``contracts/reviewspec-registry.md``."""
    if stage in EXEMPT_STAGES:
        return None
    return _build_registry().get(stage)


def reviewable_stages() -> list[str]:
    """All stages with a real ReviewSpec (sorted, deterministic ordering)."""
    return sorted(_build_registry().keys())


__all__ = ["EXEMPT_STAGES", "reviewable_stages", "reviewspec_for"]
