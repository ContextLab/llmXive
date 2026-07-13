"""Per-stage ReviewSpec registry (spec 015 T048, FR-027-031).

``reviewspec_for(stage) -> ReviewSpec | None`` is the SSoT lookup the engine
consults to drive each reviewable step. EXEMPT stages return ``None`` (no
convergence loop). See ``contracts/reviewspec-registry.md`` for the full table.

For stages whose **panel prompts haven't been authored yet** (T049-T053) or whose
**agent wiring hasn't landed** (T054-T059), this registry installs TODO-placeholder
reviewers/reviser that conform to the Protocol but raise a clear pointer to the
follow-up task when invoked - fail-loud rather than silently produce empty
verdicts. Each placeholder names the task that will replace it.
"""

from __future__ import annotations

from typing import cast

from llmxive.backends.router import DEFAULT_MODEL

from .types import Concern, ConcernResponse, Reviewer, ReviewSpec, Severity

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

    def revise(
        self, artifacts: dict[str, str], concerns: list[Concern],
    ) -> tuple[dict[str, str], list[ConcernResponse]]:
        raise NotImplementedError(
            f"reviser '{self.name}' is a registry placeholder - the agent wiring "
            f"lands in {self._wiring_task}. The engine's R2 revise phase was invoked "
            f"before that wiring landed."
        )


def _todo_reviewers(lenses: list[str], *, prompt_task: str, wiring_task: str) -> list[Reviewer]:
    """Build placeholder reviewers. Return type is ``list[Reviewer]`` (not
    ``list[_TodoReviewer]``) because ``list`` is invariant — ``ReviewSpec.reviewers``
    expects ``list[Reviewer]`` and ``_TodoReviewer`` structurally satisfies the
    Protocol."""
    return [_TodoReviewer(lens, prompt_task=prompt_task, wiring_task=wiring_task) for lens in lenses]


def _wire_live_panel(
    base: ReviewSpec, *, backend: object, repo_root: object, model: str | None,
) -> None:
    """Replace ``base``'s static ``_TodoReviewer`` placeholders with a live
    ``LLMReviewer`` panel — one reviewer per lens (FR-027/FR-028; completes the
    T054-T059 panel-side wiring the ``build_*_reviewspec`` docstrings reference).

    No-op when ``backend`` is None so callers that only exercise the static
    reviser / kickback routing (some unit fixtures) keep the placeholders and
    don't accidentally require a real backend."""
    if backend is None:
        return
    from pathlib import Path as _Path

    from .llm_reviewer import build_panel

    lenses: list[str] = [
        str(getattr(r, "lens", None) or getattr(r, "name", "")) for r in base.reviewers
    ]
    # ``build_panel`` returns ``list[LLMReviewer]``; ``ReviewSpec.reviewers`` is
    # ``list[Reviewer]`` (invariant). LLMReviewer structurally satisfies the
    # Reviewer Protocol, so the cast is sound (mirrors ``_todo_reviewers``).
    panel = build_panel(
        stage=base.stage,
        lenses=lenses,
        backend=backend,
        repo_root=_Path(str(repo_root)),
        model=model,
    )
    base.reviewers = cast("list[Reviewer]", panel)


# --- Per-stage ReviewSpec table (FR-027/FR-028 + contracts/reviewspec-registry.md) ---


def _spec_idea() -> ReviewSpec:
    """Idea convergence unit (4-lens panel + FleshOutReviser).

    The reviser is wired LIVE via :func:`build_idea_reviewspec` — the
    placeholder ``_TodoReviser`` here keeps the static registry
    Protocol-conformant for callers that don't have a backend to bind
    (matching the pattern used for every other reviewable stage's static
    spec; ``build_*_reviewspec`` swaps in the LLM-bound reviser)."""
    return ReviewSpec(
        stage="flesh_out_complete",
        artifacts=["idea/*.md"],
        reviewers=_todo_reviewers(
            ["rq_validity", "novelty", "feasibility", "idea_quality"],
            prompt_task="T049", wiring_task="T054",
        ),
        reviser=_TodoReviser(
            "flesh_out",
            wiring_task="build_idea_reviewspec (FleshOutReviser, FR-027)",
        ),
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
            ["requirements_coverage", "internal_consistency", "testability", "scope",
             "scientific_soundness"],
            prompt_task="T050", wiring_task="T054",
        ),
        reviser=_TodoReviser("specifier+clarifier", wiring_task="T054"),
        # Spec 023 defect #19 (the PROJ-552 regeneration loop): a kickback's
        # to_stage names the stage WHOSE AGENT must re-run (defect #14
        # semantics). The old WRITING/REQUIREMENT route "project_initialized"
        # re-ran the SPECIFIER, which minted a fresh specs/NNN dir and
        # regenerated the whole document — destroying all in-panel revision
        # progress and presenting the panel a brand-new doc with a fresh crop
        # of nits (observed live: dirs 004→010, concern counts oscillating
        # 24→10→3→5→4→1→11 instead of converging). Writing/requirement
        # residue is a spec.md-level defect: route to "specified" so the
        # CLARIFIER re-runs and the spec panel (whose SpecReviser edits
        # spec.md IN PLACE) gets another bounded round on the SAME document.
        # Only idea-root causes (methodology/science/fatal) regenerate.
        kickback_routing={
            Severity.WRITING: "specified",  # in-place clarify + re-review
            Severity.REQUIREMENT: "specified",
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
            ["methodology", "spec_coverage", "data_resources", "plan_consistency",
             "scientific_soundness"],
            prompt_task="T051", wiring_task="T056",
        ),
        reviser=_TodoReviser("planner", wiring_task="T056"),
        # Spec 023 defect #14: a kickback's to_stage names the stage WHOSE
        # AGENT must re-run (the graph dispatches STAGE_TO_AGENT[to_stage]).
        # The old map was one stage too far forward: "clarified" re-ran the
        # PLANNER against the same defective spec — a spec-gap concern could
        # never be repaired (observed live: PROJ-552 hit the kickback cap
        # re-flagging a spec.md factual error the plan reviser is forbidden
        # from editing). Re-plan = "clarified" (planner runs there); fix the
        # spec = "specified" (clarifier + spec panel run there and the
        # SpecReviser CAN edit spec.md).
        kickback_routing={
            Severity.WRITING: "clarified",  # re-plan
            Severity.REQUIREMENT: "specified",  # spec gap -> spec panel re-runs
            Severity.METHODOLOGY: "specified",
            Severity.SCIENCE: "specified",
            Severity.FATAL: "specified",
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
        # Spec 023 defect #14 (see the plan panel above): a plan flaw is
        # fixed by the PLANNER, which runs at "clarified" — "planned" runs
        # the tasker against the same defective plan.
        kickback_routing={
            Severity.WRITING: "tasked",
            Severity.REQUIREMENT: "clarified",  # plan flaw -> planner re-runs
            Severity.METHODOLOGY: "clarified",
            Severity.SCIENCE: "clarified",
            Severity.FATAL: "clarified",
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
        # Spec 023 defect #19 (paper twin of the research-spec fix above):
        # "paper_drafting_init" re-ran the PAPER SPECIFIER — fresh
        # paper/specs/NNN dir + full regeneration. Writing/requirement
        # residue is a paper-spec.md-level defect: route to
        # "paper_specified" so the paper clarifier + paper-spec panel
        # revise the SAME document in place.
        kickback_routing={
            Severity.WRITING: "paper_specified",  # in-place clarify + re-review
            Severity.REQUIREMENT: "paper_specified",
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
        # Spec 023 defect #14 (paper side): re-plan = "paper_clarified"
        # (paper planner runs there); paper-spec gap = "paper_specified"
        # (paper clarifier + paper-spec panel run there).
        kickback_routing={
            Severity.WRITING: "paper_clarified",  # re-plan
            Severity.REQUIREMENT: "paper_specified",  # paper-spec gap
            Severity.METHODOLOGY: "paper_specified",
            Severity.SCIENCE: "paper_specified",
            Severity.FATAL: "paper_specified",
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
        # Spec 023 defect #14: a paper-plan flaw is fixed by the paper
        # PLANNER, which runs at "paper_clarified".
        kickback_routing={
            Severity.WRITING: "paper_tasked",
            Severity.REQUIREMENT: "paper_clarified",  # paper-plan flaw
            Severity.METHODOLOGY: "paper_clarified",
            Severity.SCIENCE: "paper_clarified",
            Severity.FATAL: "paper_clarified",
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
    # NOTE: research_review + paper_review are added by the lazy
    # build helpers at the bottom of this module — they exist for
    # symmetry and reviewspec_for(...) lookup, even though their
    # "reviser" is the engine-adapter (kickback-only, reviser=None).
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
    stages. The mapping mirrors ``contracts/reviewspec-registry.md``.

    The returned spec uses TODO-placeholder revisers/reviewers; callers that
    need a LIVE spec (with real LLM-backed revisers) should use the
    ``build_*_reviewspec`` helpers in ``llmxive.convergence.revisers`` —
    e.g. :func:`build_spec_reviewspec` for the ``clarified`` stage."""
    if stage in EXEMPT_STAGES:
        return None
    return _build_registry().get(stage)


def reviewable_stages() -> list[str]:
    """All stages with a real ReviewSpec (sorted, deterministic ordering)."""
    return sorted(_build_registry().keys())


def build_idea_reviewspec(
    *,
    backend: object,
    repo_root: object,
    project_id: str,
    model: str = DEFAULT_MODEL,
) -> ReviewSpec:
    """Build a LIVE ``ReviewSpec`` for the idea convergence unit (FR-027).

    The returned spec has a real :class:`FleshOutReviser` as its
    ``.reviser`` — the rest of the spec (reviewers, kickback routing,
    advance_stage, etc.) is identical to the static
    ``reviewspec_for("flesh_out_complete")``. Panel reviewers remain
    ``_TodoReviewer`` placeholders until panel-side wiring lands (the
    same pattern every other ``build_*_reviewspec`` helper uses).

    Idea is the EARLIEST reviewable stage; ``constitution_input`` stays
    ``False`` because the constitution doesn't exist yet at this stage
    (FR-030 — see the invariant test in
    ``tests/integration/test_invariants.py``)."""
    from .revisers.flesh_out_reviser import FleshOutReviser

    base = _spec_idea()
    base.reviser = FleshOutReviser(
        backend=backend,
        repo_root=repo_root,  # type: ignore[arg-type]
        project_id=project_id,
        model=model,
    )
    _wire_live_panel(base, backend=backend, repo_root=repo_root, model=model)
    return base


def build_spec_reviewspec(
    *,
    backend: object,
    repo_root: object,
    project_id: str,
    model: str = DEFAULT_MODEL,
) -> ReviewSpec:
    """Build a LIVE ``ReviewSpec`` for the spec convergence unit (T054).

    The returned spec has a real :class:`SpecReviser` as its ``.reviser`` —
    the rest of the spec (reviewers, kickback routing, advance_stage, etc.)
    is identical to the static ``reviewspec_for("clarified")``. Panel
    reviewers remain ``_TodoReviewer`` placeholders until T058 wires the
    spec panel.

    Importing locally so this module stays import-clean for callers that
    never touch the live reviser path.
    """
    # Local import: keeps ``revisers/`` out of the import graph for callers
    # who only need the static registry (and avoids any future cycle if a
    # reviser ever needs to import from this module).
    from .revisers.spec_reviser import SpecReviser

    base = _spec_research_spec()
    base.reviser = SpecReviser(
        backend=backend,
        repo_root=repo_root,  # type: ignore[arg-type]
        project_id=project_id,
        model=model,
    )
    _wire_live_panel(base, backend=backend, repo_root=repo_root, model=model)
    return base


def build_paper_spec_reviewspec(
    *,
    backend: object,
    repo_root: object,
    project_id: str,
    model: str = DEFAULT_MODEL,
) -> ReviewSpec:
    """Build a LIVE ``ReviewSpec`` for the paper-spec convergence unit (T055).

    Mirrors :func:`build_spec_reviewspec` for the paper track. Returns a
    ReviewSpec with a real :class:`PaperSpecReviser` bound; reviewer-side
    placeholders stay until T058 wires the paper-spec panel."""
    from .revisers.paper_spec_reviser import PaperSpecReviser

    base = _spec_paper_spec()
    base.reviser = PaperSpecReviser(
        backend=backend,
        repo_root=repo_root,  # type: ignore[arg-type]
        project_id=project_id,
        model=model,
    )
    _wire_live_panel(base, backend=backend, repo_root=repo_root, model=model)
    return base


def build_plan_reviewspec(
    *,
    backend: object,
    repo_root: object,
    project_id: str,
    model: str = DEFAULT_MODEL,
) -> ReviewSpec:
    """Build a LIVE ``ReviewSpec`` for the research-plan convergence unit (T056).

    The reviser edits MULTIPLE design docs (plan.md + research.md +
    data-model.md + quickstart.md + contracts/*); see :class:`PlanReviser`."""
    from .revisers.plan_reviser import PlanReviser

    base = _spec_research_plan()
    base.reviser = PlanReviser(
        backend=backend,
        repo_root=repo_root,  # type: ignore[arg-type]
        project_id=project_id,
        model=model,
    )
    _wire_live_panel(base, backend=backend, repo_root=repo_root, model=model)
    return base


def build_paper_plan_reviewspec(
    *,
    backend: object,
    repo_root: object,
    project_id: str,
    model: str = DEFAULT_MODEL,
) -> ReviewSpec:
    """Build a LIVE ``ReviewSpec`` for the paper-plan convergence unit (T056).

    Paper-track twin of :func:`build_plan_reviewspec`; see :class:`PaperPlanReviser`."""
    from .revisers.plan_reviser import PaperPlanReviser

    base = _spec_paper_plan()
    base.reviser = PaperPlanReviser(
        backend=backend,
        repo_root=repo_root,  # type: ignore[arg-type]
        project_id=project_id,
        model=model,
    )
    _wire_live_panel(base, backend=backend, repo_root=repo_root, model=model)
    return base


def build_tasks_reviewspec(
    *,
    backend: object,
    repo_root: object,
    project_id: str,
    model: str = DEFAULT_MODEL,
) -> ReviewSpec:
    """Build a LIVE ``ReviewSpec`` for the research-tasks convergence unit (T057).

    Reviser is the tasker's Mode-B (full-document rewrite); see
    :class:`TasksReviser`. Deterministic guards (≥10 ``T###``, FR-010
    ordering, FR-012 constraint preservation) run BEFORE the panel as a
    pre-filter — they are not the reviser's job."""
    from .revisers.tasks_reviser import TasksReviser

    base = _spec_research_tasks()
    base.reviser = TasksReviser(
        backend=backend,
        repo_root=repo_root,  # type: ignore[arg-type]
        project_id=project_id,
        model=model,
    )
    _wire_live_panel(base, backend=backend, repo_root=repo_root, model=model)
    return base


def build_paper_tasks_reviewspec(
    *,
    backend: object,
    repo_root: object,
    project_id: str,
    model: str = DEFAULT_MODEL,
) -> ReviewSpec:
    """Build a LIVE ``ReviewSpec`` for the paper-tasks convergence unit (T057).

    Paper-track twin of :func:`build_tasks_reviewspec`; see :class:`PaperTasksReviser`."""
    from .revisers.tasks_reviser import PaperTasksReviser

    base = _spec_paper_tasks()
    base.reviser = PaperTasksReviser(
        backend=backend,
        repo_root=repo_root,  # type: ignore[arg-type]
        project_id=project_id,
        model=model,
    )
    _wire_live_panel(base, backend=backend, repo_root=repo_root, model=model)
    return base


def build_implement_reviewspec(
    *,
    backend: object,
    repo_root: object,
    project_id: str,
    project_root: object | None = None,
    model: str = DEFAULT_MODEL,
) -> ReviewSpec:
    """Build a LIVE ``ReviewSpec`` for the research-implement convergence unit (T058).

    The reviser is :class:`ImplementerReviser` (multi-artifact code edit +
    post-revise filesystem re-verification per discrepancy #49). The
    reviewers (8-panel: idea_quality / creativity /
    implementation_correctness / implementation_completeness / code_quality
    / data_quality / filesystem_hygiene / research_reviewer) are REUSED
    from the existing prompts under ``agents/prompts/research_reviewer*.md``
    — their wiring as live Reviewer Protocol-conformant instances also
    lands here. (Today this returns TodoReviewers; T058 follow-up wiring
    is the panel-side completion.)"""
    from .revisers.implementer_reviser import ImplementerReviser

    base = _spec_research_unit()
    base.reviser = ImplementerReviser(
        backend=backend,
        repo_root=repo_root,  # type: ignore[arg-type]
        project_id=project_id,
        project_root=project_root,  # type: ignore[arg-type]
        model=model,
    )
    _wire_live_panel(base, backend=backend, repo_root=repo_root, model=model)
    return base


def build_paper_implement_reviewspec(
    *,
    backend: object,
    repo_root: object,
    project_id: str,
    model: str = DEFAULT_MODEL,
) -> ReviewSpec:
    """Build a LIVE ``ReviewSpec`` for the paper-implement convergence unit (T059).

    The reviser is :class:`PaperImplementReviser` (multi-artifact paper-side
    edit; dispatches to sub-agents internally based on each concern's
    lens). The reviewers (12-panel) are REUSED from
    ``agents/prompts/paper_reviewer*.md``; live Reviewer-Protocol wiring
    of the panel lands as the T059 follow-up."""
    from .revisers.paper_implement_reviser import PaperImplementReviser

    base = _spec_paper_implement()
    base.reviser = PaperImplementReviser(
        backend=backend,
        repo_root=repo_root,  # type: ignore[arg-type]
        project_id=project_id,
        model=model,
    )
    _wire_live_panel(base, backend=backend, repo_root=repo_root, model=model)
    return base


# --- Spec 015 T042: research-review and paper-review review-stage specs ---
#
# The 8-panel research-review stage + the 12-panel paper-review stage
# share a key property: they have NO in-loop reviser. Every non-accept
# verdict immediately kicks back. The "reviser" slot is therefore the
# SOLE-WRITER adapter
# :func:`llmxive.convergence.revision_adapter.kickback_to_revision_spec`,
# invoked by the calling agent (advancement.py / implementer.py) AFTER
# the engine emits a KickbackRecord.
#
# The static ``_spec_research_unit()`` + ``_spec_paper_implement()``
# defined earlier in this module hold the panel + kickback-routing
# tables that the build_*_reviewspec helpers below clone. T042 sets the
# ``reviser`` slot to None on the cloned spec so the engine's
# R1→kickback path fires on any R1 concerns.


def build_research_review_reviewspec(
    *,
    backend: object | None = None,
    repo_root: object | None = None,
    project_id: str | None = None,
    model: str = DEFAULT_MODEL,
) -> ReviewSpec:
    """Build the LIVE ``ReviewSpec`` for the research-review convergence
    unit (T042 WS3 / FR-034).

    Returns the 8-panel ``_spec_research_unit()`` template with the
    reviser slot set to None — the engine treats that as "kickback on
    any R1 concerns". The calling agent
    (``llmxive.agents.advancement.evaluate``) feeds the resulting
    KickbackRecord through
    :func:`llmxive.convergence.revision_adapter.kickback_to_revision_spec`
    to write the auto-revisions round dir the implementer picks up.

    ``backend`` / ``repo_root`` / ``project_id`` / ``model`` are
    accepted for API parity with the other ``build_*`` helpers."""
    _ = (backend, repo_root, project_id, model)
    base = _spec_research_unit()
    base.reviser = None
    base.max_rounds = 1
    return base


def build_paper_review_reviewspec(
    *,
    backend: object | None = None,
    repo_root: object | None = None,
    project_id: str | None = None,
    model: str = DEFAULT_MODEL,
) -> ReviewSpec:
    """Build the LIVE ``ReviewSpec`` for the paper-review convergence
    unit (T042 WS4 / FR-034).

    Returns the 12-panel ``_spec_paper_implement()`` template with the
    reviser slot set to None — the engine treats that as "kickback on
    any R1 concerns". The calling agent
    (``llmxive.agents.advancement.evaluate``) feeds the resulting
    KickbackRecord through
    :func:`llmxive.convergence.revision_adapter.kickback_to_revision_spec`
    to write the auto-revisions round dir the implementer picks up.

    ``backend`` / ``repo_root`` / ``project_id`` / ``model`` are
    accepted for API parity with the other ``build_*`` helpers."""
    _ = (backend, repo_root, project_id, model)
    base = _spec_paper_implement()
    base.reviser = None
    base.max_rounds = 1
    return base


__all__ = [
    "EXEMPT_STAGES",
    "build_idea_reviewspec",
    "build_implement_reviewspec",
    "build_paper_implement_reviewspec",
    "build_paper_plan_reviewspec",
    "build_paper_review_reviewspec",
    "build_paper_spec_reviewspec",
    "build_paper_tasks_reviewspec",
    "build_plan_reviewspec",
    "build_research_review_reviewspec",
    "build_spec_reviewspec",
    "build_tasks_reviewspec",
    "reviewable_stages",
    "reviewspec_for",
]
