"""DOC-stage convergence-panel wiring tests (spec-015 / #239).

These prove that the reviewable DOC stages — spec / plan / paper_spec /
paper_plan / paper_tasks — now INVOKE their live multi-lens convergence
panel in-cmd (they previously advanced with NO panel review), and that:

(a) the panel is invoked and, on an all-accept verdict, the stage advances
    (``write_artifacts`` returns normally + no kickback marker is written);
(b) on a fail verdict the panel does NOT converge, a
    ``human_input_needed.yaml`` kickback marker is written, and the stage
    does NOT advance (``StagePanelKickback`` is raised).

Each test uses a FAKE backend (the audit-aware pattern from
``test_panels_research.py`` / ``test_panels_paper.py``) that drives the live
Reviser deterministically, plus hand-rolled scripted reviewers swapped into
the live ReviewSpec. No real LLM calls. No real project/state touched —
everything happens under ``tmp_path``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from llmxive.convergence.types import Concern, Severity, Verdict
from llmxive.speckit._stage_panel import StagePanelKickback
from llmxive.speckit.slash_command import SlashCommandContext
from llmxive.types import BackendName

_REPO_ROOT = Path(__file__).resolve().parents[2]


# --- Test doubles ---------------------------------------------------------


@dataclass
class _FakeResponse:
    text: str
    model: str = "fake-model"
    backend: str = "fake"


@dataclass
class _FakeBackend:
    responses: list[str]

    def chat(self, messages, model=None, **kw):  # type: ignore[no-untyped-def]
        sys_text = getattr(messages[0], "content", "") if messages else ""
        if "auditing a revision you just produced" in sys_text:
            return _FakeResponse(text="ok: true\nproblems: []\n")
        if not self.responses:
            raise RuntimeError("_FakeBackend ran out of canned responses")
        return _FakeResponse(text=self.responses.pop(0))


class _ScriptedReviewer:
    def __init__(self, name, *, initial_concerns, accepts_per_round):  # type: ignore[no-untyped-def]
        self.name = name
        self._initial = initial_concerns
        self._accepts = accepts_per_round
        self._rereview_round = 0
        self.identify_calls = 0
        self.rereview_calls = 0

    def identify(self, artifacts, *, constitution, advisory):  # type: ignore[no-untyped-def]
        self.identify_calls += 1
        return list(self._initial)

    def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):  # type: ignore[no-untyped-def]
        self.rereview_calls += 1
        self._rereview_round += 1
        accept_ids = self._accepts.get(self._rereview_round, [])
        return [
            Verdict(
                concern_id=c.id, reviewer=self.name,
                status="pass" if c.id in accept_ids else "fail",
            )
            for c in own_concerns
        ]


def _ctx(project_id: str, project_dir: Path, agent_name: str) -> SlashCommandContext:
    return SlashCommandContext(
        project_id=project_id,
        project_dir=project_dir,
        run_id="r", task_id="t",
        inputs=[], expected_outputs=[],
        prompt_template_path=project_dir / "ignored.md",
        default_backend=BackendName.DARTMOUTH,
        fallback_backends=[],
        default_model="fake-model",
        prompt_version="1.0.0",
        agent_name=agent_name,
    )


def _patch_panel(
    monkeypatch: pytest.MonkeyPatch,
    *,
    builder_name: str,
    backend: _FakeBackend,
    reviewers: list[_ScriptedReviewer],
) -> dict[str, object]:
    """Patch ``make_backend`` (so the cmd resolves our fake backend) and the
    named ``build_*_reviewspec`` (so we keep the LIVE reviser but swap in
    scripted reviewers). Returns a holder recording the spec the cmd used."""
    import llmxive.backends.router as router
    import llmxive.convergence.reviewspecs as rs

    monkeypatch.setattr(router, "make_backend", lambda name: backend)
    real_builder = getattr(rs, builder_name)
    holder: dict[str, object] = {}

    def _wrapped(**kwargs):  # type: ignore[no-untyped-def]
        # Resolve panel prompts against the REAL repo (the live builder loads
        # per-lens prompt files); the reviewers are swapped below so the live
        # LLM reviewers are never actually invoked.
        kwargs["repo_root"] = _REPO_ROOT
        spec = real_builder(**kwargs)
        spec.reviewers = list(reviewers)
        holder["spec"] = spec
        return spec

    monkeypatch.setattr(rs, builder_name, _wrapped)
    return holder


# --- Project skeletons ----------------------------------------------------


def _seed_research_spec(project_dir: Path) -> Path:
    spec_dir = project_dir / "specs" / "001-x"
    spec_dir.mkdir(parents=True)
    spec_md = spec_dir / "spec.md"
    spec_md.write_text(
        "# Feature Specification: X\n\n## User Scenarios\n\n"
        "### User Story 1 (Priority: P1)\n\nDo the thing.\n\n"
        "## Functional Requirements\n\n- **FR-001**: System MUST do X.\n\n"
        "## Success Criteria\n\n- **SC-001**: It works.\n",
        encoding="utf-8",
    )
    (project_dir / "idea").mkdir()
    (project_dir / "idea" / "idea.md").write_text(
        "# Idea\nResearch question: does X cause Y?\n", encoding="utf-8"
    )
    (project_dir / ".specify" / "memory").mkdir(parents=True)
    (project_dir / ".specify" / "memory" / "constitution.md").write_text(
        "# Constitution\nPrinciple I: real artifacts only.\n", encoding="utf-8"
    )
    return spec_md


def _seed_research_plan(project_dir: Path) -> Path:
    spec_dir = project_dir / "specs" / "001-x"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text(
        "# spec\n- **FR-001**: do X\n", encoding="utf-8"
    )
    plan_md = spec_dir / "plan.md"
    plan_md.write_text("# Plan\nMethodology: regression.\n", encoding="utf-8")
    (project_dir / ".specify" / "memory").mkdir(parents=True)
    (project_dir / ".specify" / "memory" / "constitution.md").write_text(
        "# Constitution\n", encoding="utf-8"
    )
    return plan_md


def _seed_paper_spec(project_dir: Path) -> Path:
    spec_dir = project_dir / "paper" / "specs" / "001-x"
    spec_dir.mkdir(parents=True)
    spec_md = spec_dir / "spec.md"
    spec_md.write_text(
        "# Paper Specification: X\n\n## Reader Scenarios\n\nReaders learn X.\n\n"
        "## Required Sections\n\n- Introduction\n- Methods\n", encoding="utf-8"
    )
    (project_dir / "paper" / ".specify" / "memory").mkdir(parents=True)
    (project_dir / "paper" / ".specify" / "memory" / "constitution.md").write_text(
        "# Paper Constitution\n", encoding="utf-8"
    )
    return spec_md


def _seed_paper_plan(project_dir: Path) -> Path:
    spec_dir = project_dir / "paper" / "specs" / "001-x"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text("# paper spec\n", encoding="utf-8")
    plan_md = spec_dir / "plan.md"
    plan_md.write_text("# Paper Plan\nStructure: IMRaD.\n", encoding="utf-8")
    (project_dir / "paper" / ".specify" / "memory").mkdir(parents=True)
    (project_dir / "paper" / ".specify" / "memory" / "constitution.md").write_text(
        "# Paper Constitution\n", encoding="utf-8"
    )
    return plan_md


# --- spec stage (clarify_cmd) --------------------------------------------


def _spec_reviser_reply(spec_key: str) -> str:
    return json.dumps({
        "new_spec_md": (
            "# Feature Specification: X\n\n## Functional Requirements\n\n"
            "- **FR-001**: System MUST do X (the metric AUC).\n\n"
            "## Success Criteria\n\n- **SC-001**: It works.\n"
        ),
        "responses": [
            {"concern_id": "C1", "response": "Resolved",
             "what_changed": "named AUC", "artifacts_changed": [spec_key]},
        ],
    })


def _run_spec_panel_directly(monkeypatch, tmp_path, *, accept):  # type: ignore[no-untyped-def]
    """Drive ClarifierAgent._run_spec_panel against a seeded project."""
    from llmxive.speckit.clarify_cmd import ClarifierAgent

    repo = tmp_path / "repo"
    project_dir = repo / "projects" / "PROJ-999-spec"
    project_dir.mkdir(parents=True)
    spec_md = _seed_research_spec(project_dir)
    spec_key = str(spec_md.relative_to(repo))

    concern = Concern(
        id="C1", reviewer="requirements_coverage", severity=Severity.REQUIREMENT,
        artifact=spec_key, location="FR-001", text="name the metric",
    )
    reviewer = _ScriptedReviewer(
        "requirements_coverage",
        initial_concerns=[concern],
        accepts_per_round={1: ["C1"]} if accept else {},
    )
    backend = _FakeBackend(responses=[_spec_reviser_reply(spec_key)] * 5)
    _patch_panel(
        monkeypatch, builder_name="build_spec_reviewspec",
        backend=backend, reviewers=[reviewer],
    )

    agent = ClarifierAgent()
    memory_dir = project_dir / ".specify" / "memory"
    agent._run_spec_panel(_ctx("PROJ-999-spec", project_dir, "clarifier"),
                          spec_md, memory_dir, repo)
    return reviewer, memory_dir


def test_spec_panel_invoked_and_advances_on_accept(monkeypatch, tmp_path):
    reviewer, memory_dir = _run_spec_panel_directly(
        monkeypatch, tmp_path, accept=True
    )
    assert reviewer.identify_calls == 1  # the panel WAS invoked
    assert not (memory_dir / "human_input_needed.yaml").exists()


def test_spec_panel_kickback_blocks_advance(monkeypatch, tmp_path):
    with pytest.raises(StagePanelKickback):
        _run_spec_panel_directly(monkeypatch, tmp_path, accept=False)
    memory = (tmp_path / "repo" / "projects" / "PROJ-999-spec"
              / ".specify" / "memory")
    # F-20 Part B: panel non-convergence writes the ADAPTIVE-kickback sentinel,
    # NOT human_input_needed.yaml (that's reserved for genuine human escalation).
    marker = memory / "convergence_kickback.yaml"
    assert marker.exists()
    assert not (memory / "human_input_needed.yaml").exists()
    payload = yaml.safe_load(marker.read_text())
    assert payload["stage"] == "spec"
    assert "to_stage" in payload
    assert payload["unresolved_concerns"]  # provenance carried


# --- plan stage (plan_cmd) -----------------------------------------------


def test_plan_panel_invoked_and_advances_on_accept(monkeypatch, tmp_path):
    from llmxive.speckit.plan_cmd import PlannerAgent

    repo = tmp_path / "repo"
    project_dir = repo / "projects" / "PROJ-999-plan"
    project_dir.mkdir(parents=True)
    plan_md = _seed_research_plan(project_dir)
    feature_dir = plan_md.parent
    plan_key = str(plan_md.relative_to(repo))

    concern = Concern(
        id="P1", reviewer="methodology", severity=Severity.METHODOLOGY,
        artifact=plan_key, location="Methodology", text="add a control",
    )
    reviewer = _ScriptedReviewer(
        "methodology", initial_concerns=[concern], accepts_per_round={1: ["P1"]},
    )
    reply = json.dumps({
        "updated_artifacts": {plan_key: "# Plan\nMethodology: regression + RCT.\n"},
        "responses": [{"concern_id": "P1", "response": "added RCT",
                       "what_changed": "RCT", "artifacts_changed": [plan_key]}],
    })
    backend = _FakeBackend(responses=[reply] * 5)
    _patch_panel(monkeypatch, builder_name="build_plan_reviewspec",
                 backend=backend, reviewers=[reviewer])

    PlannerAgent()._run_plan_panel(
        _ctx("PROJ-999-plan", project_dir, "planner"), feature_dir, repo
    )
    assert reviewer.identify_calls == 1
    assert not (project_dir / ".specify" / "memory" / "human_input_needed.yaml").exists()


def test_plan_panel_kickback_blocks_advance(monkeypatch, tmp_path):
    from llmxive.speckit.plan_cmd import PlannerAgent

    repo = tmp_path / "repo"
    project_dir = repo / "projects" / "PROJ-999-plan2"
    project_dir.mkdir(parents=True)
    plan_md = _seed_research_plan(project_dir)
    feature_dir = plan_md.parent
    plan_key = str(plan_md.relative_to(repo))

    concern = Concern(
        id="P1", reviewer="methodology", severity=Severity.METHODOLOGY,
        artifact=plan_key, location="", text="unsound",
    )
    reviewer = _ScriptedReviewer("methodology", initial_concerns=[concern],
                                 accepts_per_round={})
    reply = json.dumps({
        "updated_artifacts": {plan_key: "# Plan v_n\n"},
        "responses": [{"concern_id": "P1", "response": "tried", "what_changed": "x"}],
    })
    backend = _FakeBackend(responses=[reply] * 5)
    _patch_panel(monkeypatch, builder_name="build_plan_reviewspec",
                 backend=backend, reviewers=[reviewer])

    with pytest.raises(StagePanelKickback):
        PlannerAgent()._run_plan_panel(
            _ctx("PROJ-999-plan2", project_dir, "planner"), feature_dir, repo
        )
    memory = project_dir / ".specify" / "memory"
    marker = memory / "convergence_kickback.yaml"
    assert marker.exists()
    assert not (memory / "human_input_needed.yaml").exists()
    assert yaml.safe_load(marker.read_text())["stage"] == "plan"


# --- paper_spec stage (paper_clarify_cmd) --------------------------------


def _paper_spec_reply(spec_key: str) -> str:
    return json.dumps({
        "new_spec_md": (
            "# Paper Specification: X\n\n## Reader Scenarios\n\nReaders learn X "
            "(supported by Figure 1).\n\n## Required Sections\n\n- Introduction\n"
        ),
        "responses": [{"concern_id": "PS1", "response": "ok",
                       "what_changed": "added support",
                       "artifacts_changed": [spec_key]}],
    })


def test_paper_spec_panel_invoked_and_advances_on_accept(monkeypatch, tmp_path):
    from llmxive.speckit.paper_clarify_cmd import PaperClarifierAgent

    repo = tmp_path / "repo"
    project_dir = repo / "projects" / "PROJ-999-ps"
    project_dir.mkdir(parents=True)
    spec_md = _seed_paper_spec(project_dir)
    spec_key = str(spec_md.relative_to(repo))

    concern = Concern(
        id="PS1", reviewer="claims_supported", severity=Severity.WRITING,
        artifact=spec_key, location="", text="claim unsupported",
    )
    reviewer = _ScriptedReviewer("claims_supported", initial_concerns=[concern],
                                 accepts_per_round={1: ["PS1"]})
    backend = _FakeBackend(responses=[_paper_spec_reply(spec_key)] * 5)
    _patch_panel(monkeypatch, builder_name="build_paper_spec_reviewspec",
                 backend=backend, reviewers=[reviewer])

    memory_dir = project_dir / "paper" / ".specify" / "memory"
    PaperClarifierAgent()._run_paper_spec_panel(
        _ctx("PROJ-999-ps", project_dir, "paper_clarifier"),
        spec_md, memory_dir, repo,
    )
    assert reviewer.identify_calls == 1
    assert not (memory_dir / "human_input_needed.yaml").exists()


def test_paper_spec_panel_kickback_blocks_advance(monkeypatch, tmp_path):
    from llmxive.speckit.paper_clarify_cmd import PaperClarifierAgent

    repo = tmp_path / "repo"
    project_dir = repo / "projects" / "PROJ-999-ps2"
    project_dir.mkdir(parents=True)
    spec_md = _seed_paper_spec(project_dir)
    spec_key = str(spec_md.relative_to(repo))

    concern = Concern(
        id="PS1", reviewer="claims_supported", severity=Severity.WRITING,
        artifact=spec_key, location="", text="claim unsupported",
    )
    reviewer = _ScriptedReviewer("claims_supported", initial_concerns=[concern],
                                 accepts_per_round={})
    backend = _FakeBackend(responses=[_paper_spec_reply(spec_key)] * 5)
    _patch_panel(monkeypatch, builder_name="build_paper_spec_reviewspec",
                 backend=backend, reviewers=[reviewer])

    memory_dir = project_dir / "paper" / ".specify" / "memory"
    with pytest.raises(StagePanelKickback):
        PaperClarifierAgent()._run_paper_spec_panel(
            _ctx("PROJ-999-ps2", project_dir, "paper_clarifier"),
            spec_md, memory_dir, repo,
        )
    assert (memory_dir / "convergence_kickback.yaml").exists()
    assert not (memory_dir / "human_input_needed.yaml").exists()
    assert yaml.safe_load(
        (memory_dir / "convergence_kickback.yaml").read_text()
    )["stage"] == "paper_spec"


# --- paper_plan stage (paper_plan_cmd) -----------------------------------


def test_paper_plan_panel_invoked_and_advances_on_accept(monkeypatch, tmp_path):
    from llmxive.speckit.paper_plan_cmd import PaperPlannerAgent

    repo = tmp_path / "repo"
    project_dir = repo / "projects" / "PROJ-999-pp"
    project_dir.mkdir(parents=True)
    plan_md = _seed_paper_plan(project_dir)
    feature_dir = plan_md.parent
    plan_key = str(plan_md.relative_to(repo))

    concern = Concern(
        id="PP1", reviewer="paper_structure", severity=Severity.WRITING,
        artifact=plan_key, location="", text="structure incomplete",
    )
    reviewer = _ScriptedReviewer("paper_structure", initial_concerns=[concern],
                                 accepts_per_round={1: ["PP1"]})
    reply = json.dumps({
        "updated_artifacts": {plan_key: "# Paper Plan\nStructure: full IMRaD.\n"},
        "responses": [{"concern_id": "PP1", "response": "ok", "what_changed": "x",
                       "artifacts_changed": [plan_key]}],
    })
    backend = _FakeBackend(responses=[reply] * 5)
    _patch_panel(monkeypatch, builder_name="build_paper_plan_reviewspec",
                 backend=backend, reviewers=[reviewer])

    PaperPlannerAgent()._run_paper_plan_panel(
        _ctx("PROJ-999-pp", project_dir, "paper_planner"), feature_dir, repo
    )
    assert reviewer.identify_calls == 1
    memory_dir = project_dir / "paper" / ".specify" / "memory"
    assert not (memory_dir / "human_input_needed.yaml").exists()


def test_paper_plan_panel_kickback_blocks_advance(monkeypatch, tmp_path):
    from llmxive.speckit.paper_plan_cmd import PaperPlannerAgent

    repo = tmp_path / "repo"
    project_dir = repo / "projects" / "PROJ-999-pp2"
    project_dir.mkdir(parents=True)
    plan_md = _seed_paper_plan(project_dir)
    feature_dir = plan_md.parent
    plan_key = str(plan_md.relative_to(repo))

    concern = Concern(
        id="PP1", reviewer="paper_structure", severity=Severity.WRITING,
        artifact=plan_key, location="", text="bad",
    )
    reviewer = _ScriptedReviewer("paper_structure", initial_concerns=[concern],
                                 accepts_per_round={})
    reply = json.dumps({
        "updated_artifacts": {plan_key: "# Paper Plan v_n\n"},
        "responses": [{"concern_id": "PP1", "response": "tried", "what_changed": "x"}],
    })
    backend = _FakeBackend(responses=[reply] * 5)
    _patch_panel(monkeypatch, builder_name="build_paper_plan_reviewspec",
                 backend=backend, reviewers=[reviewer])

    with pytest.raises(StagePanelKickback):
        PaperPlannerAgent()._run_paper_plan_panel(
            _ctx("PROJ-999-pp2", project_dir, "paper_planner"), feature_dir, repo
        )
    memory_dir = project_dir / "paper" / ".specify" / "memory"
    assert (memory_dir / "convergence_kickback.yaml").exists()
    assert not (memory_dir / "human_input_needed.yaml").exists()
    assert yaml.safe_load(
        (memory_dir / "convergence_kickback.yaml").read_text()
    )["stage"] == "paper_plan"


# --- paper_tasks stage (paper_tasks_cmd) ---------------------------------


def _seed_paper_tasks(project_dir: Path) -> tuple[Path, Path, Path]:
    spec_dir = project_dir / "paper" / "specs" / "001-x"
    spec_dir.mkdir(parents=True)
    spec_md = spec_dir / "spec.md"
    spec_md.write_text("# paper spec\n- **FR-001**: write intro\n", encoding="utf-8")
    plan_md = spec_dir / "plan.md"
    plan_md.write_text("# paper plan\n", encoding="utf-8")
    tasks_md = spec_dir / "tasks.md"
    tasks_md.write_text(
        "# Tasks\n- [ ] T001 write intro [kind:prose]\n", encoding="utf-8"
    )
    (project_dir / "paper" / ".specify" / "memory").mkdir(parents=True)
    (project_dir / "paper" / ".specify" / "memory" / "constitution.md").write_text(
        "# Paper Constitution\n", encoding="utf-8"
    )
    return spec_md, plan_md, tasks_md


def test_paper_tasks_panel_invoked_and_advances_on_accept(monkeypatch, tmp_path):
    from llmxive.speckit.paper_tasks_cmd import PaperTaskerAgent

    repo = tmp_path / "repo"
    project_dir = repo / "projects" / "PROJ-999-pt"
    project_dir.mkdir(parents=True)
    spec_md, plan_md, tasks_md = _seed_paper_tasks(project_dir)
    tasks_key = str(tasks_md.relative_to(repo))

    concern = Concern(
        id="PT1", reviewer="coverage", severity=Severity.REQUIREMENT,
        artifact=tasks_key, location="", text="FR-001 task light",
    )
    reviewer = _ScriptedReviewer("coverage", initial_concerns=[concern],
                                 accepts_per_round={1: ["PT1"]})
    reply = json.dumps({
        "new_tasks_md": "# Tasks\n- [ ] T001 write full intro [kind:prose]\n",
        "responses": [{"concern_id": "PT1", "response": "ok", "what_changed": "x",
                       "artifacts_changed": [tasks_key]}],
    })
    backend = _FakeBackend(responses=[reply] * 5)
    _patch_panel(monkeypatch, builder_name="build_paper_tasks_reviewspec",
                 backend=backend, reviewers=[reviewer])

    PaperTaskerAgent()._run_paper_tasks_panel(
        _ctx("PROJ-999-pt", project_dir, "paper_tasker"),
        spec_md, plan_md, tasks_md, repo, analyze_report_text="CLEAN",
    )
    assert reviewer.identify_calls == 1
    memory_dir = project_dir / "paper" / ".specify" / "memory"
    assert not (memory_dir / "human_input_needed.yaml").exists()


def test_paper_tasks_panel_kickback_blocks_advance(monkeypatch, tmp_path):
    from llmxive.speckit.paper_tasks_cmd import PaperTaskerAgent

    repo = tmp_path / "repo"
    project_dir = repo / "projects" / "PROJ-999-pt2"
    project_dir.mkdir(parents=True)
    spec_md, plan_md, tasks_md = _seed_paper_tasks(project_dir)
    tasks_key = str(tasks_md.relative_to(repo))

    concern = Concern(
        id="PT1", reviewer="coverage", severity=Severity.REQUIREMENT,
        artifact=tasks_key, location="", text="missing task",
    )
    reviewer = _ScriptedReviewer("coverage", initial_concerns=[concern],
                                 accepts_per_round={})
    reply = json.dumps({
        "new_tasks_md": "# Tasks v_n\n- [ ] T001 x [kind:prose]\n",
        "responses": [{"concern_id": "PT1", "response": "tried", "what_changed": "x"}],
    })
    backend = _FakeBackend(responses=[reply] * 5)
    _patch_panel(monkeypatch, builder_name="build_paper_tasks_reviewspec",
                 backend=backend, reviewers=[reviewer])

    with pytest.raises(StagePanelKickback):
        PaperTaskerAgent()._run_paper_tasks_panel(
            _ctx("PROJ-999-pt2", project_dir, "paper_tasker"),
            spec_md, plan_md, tasks_md, repo, analyze_report_text="report",
        )
    memory_dir = project_dir / "paper" / ".specify" / "memory"
    assert (memory_dir / "convergence_kickback.yaml").exists()
    assert not (memory_dir / "human_input_needed.yaml").exists()
    assert yaml.safe_load(
        (memory_dir / "convergence_kickback.yaml").read_text()
    )["stage"] == "paper_tasks"


# --- tasks stage bridge: real 4-lens panel runs ALONGSIDE analyze --------


def test_tasks_bridge_keeps_live_panel_and_analyze_reviewer(monkeypatch, tmp_path):
    """The bridge must run the live 4-lens LLM panel ALONGSIDE the
    analyze-derived reviewer, not overwrite it (spec-015 / #239)."""
    from llmxive.speckit import _tasker_engine_bridge as bridge

    repo = tmp_path / "repo"
    feature = repo / "projects" / "PROJ-999-tasks" / "specs" / "001-x"
    feature.mkdir(parents=True)
    spec_path = feature / "spec.md"
    plan_path = feature / "plan.md"
    tasks_path = feature / "tasks.md"
    spec_path.write_text("# spec\n- **FR-001**: X\n- **FR-002**: Y\n", encoding="utf-8")
    plan_path.write_text("# plan\n", encoding="utf-8")
    tasks_path.write_text("# tasks\n- [ ] T001 do X\n", encoding="utf-8")

    captured: dict[str, object] = {}
    real_builder = bridge.build_tasks_reviewspec

    def _capture_builder(**kwargs):  # type: ignore[no-untyped-def]
        kwargs["repo_root"] = _REPO_ROOT
        spec = real_builder(**kwargs)
        # Replace the live LLM lenses with scripted accept-on-R1 reviewers so
        # no real call is needed, but PROVE the panel slot held >1 reviewer.
        captured["live_lens_count"] = len(spec.reviewers)
        spec.reviewers = [
            _ScriptedReviewer(r.name, initial_concerns=[], accepts_per_round={})
            for r in spec.reviewers
        ]
        return spec

    monkeypatch.setattr(bridge, "build_tasks_reviewspec", _capture_builder)

    # The _AnalyzeReportReviewer raises one concern (from analyze_findings) and
    # accepts on R3, so the reviser runs once → supply one canned reply.
    tasks_key = "projects/PROJ-999-tasks/specs/001-x/tasks.md"
    reply = json.dumps({
        "new_tasks_md": "# tasks\n- [ ] T001 do X\n- [ ] T002 do Y\n",
        "responses": [{"concern_id": "F001", "response": "addressed",
                       "what_changed": "added T002", "artifacts_changed": [tasks_key]}],
    })
    backend = _FakeBackend(responses=[reply] * 5)
    result = bridge.run_tasker_via_engine(
        project_id="PROJ-999-tasks",
        repo_root=repo,
        tasks_path=tasks_path,
        spec_path=spec_path,
        plan_path=plan_path,
        analyze_findings=[{"id": "F001", "class": "writing", "text": "minor"}],
        backend=backend,
        constitution_text=None,
        analyze_report_text="report",
        model="fake-model",
    )
    # The live panel had the 4 lenses (wired by build_tasks_reviewspec); the
    # bridge appended the analyze reviewer → its panel ran ALL of them.
    assert captured["live_lens_count"] == 4
    assert result.convergence.converged is True
