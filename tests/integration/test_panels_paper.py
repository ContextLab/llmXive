"""Paper-side panel integration tests (spec 015 T047).

Mirrors ``test_panels_research.py`` for the paper-track stages:
paper_spec / paper_plan / paper_tasks / paper_implement. Each test
exercises the engine + a live Reviser (via ``build_paper_*_reviewspec``)
+ a hand-rolled fake reviewer panel + a fake backend.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from llmxive.convergence.engine import run_convergence
from llmxive.convergence.reviewspecs import (
    build_paper_implement_reviewspec,
    build_paper_plan_reviewspec,
    build_paper_spec_reviewspec,
    build_paper_tasks_reviewspec,
)
from llmxive.convergence.types import Concern, Severity, Verdict

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class _FakeResponse:
    text: str
    model: str = "fake-model"
    backend: str = "fake"


@dataclass
class _FakeBackend:
    responses: list[str]

    def chat(self, messages, model=None):  # type: ignore[no-untyped-def]
        if not self.responses:
            raise RuntimeError("_FakeBackend ran out of canned responses")
        return _FakeResponse(text=self.responses.pop(0))


class _ScriptedReviewer:
    def __init__(self, name, *, initial_concerns, accepts_per_round):
        self.name = name
        self._initial = initial_concerns
        self._accepts = accepts_per_round
        self._rereview_round = 0
        self.identify_calls = 0
        self.rereview_calls = 0

    def identify(self, artifacts, *, constitution, advisory):
        self.identify_calls += 1
        return list(self._initial)

    def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):
        self.rereview_calls += 1
        self._rereview_round += 1
        accept_ids = self._accepts.get(self._rereview_round, [])
        return [
            Verdict(concern_id=c.id, reviewer=self.name,
                    status="pass" if c.id in accept_ids else "fail")
            for c in own_concerns
        ]


def _replace_panel(spec, reviewers):
    spec.reviewers = list(reviewers)
    return spec


# --- Paper-spec end-to-end ------------------------------------------------


def test_paper_spec_convergence_accepts_after_one_revision(tmp_path: Path):
    paper_spec_key = "paper/specs/000-x/spec.md"
    artifacts = {
        paper_spec_key: (
            "# paper spec v1\n## Claims\n- C1: X causes Y "
            "[NEEDS CLARIFICATION: under what condition?].\n"
        ),
        "specs/000-x/spec.md": "# research spec\n- FR-001\n",
        "specs/000-x/plan.md": "# research plan",
        "specs/000-x/tasks.md": "# research tasks",
    }
    concern = Concern(
        id="P1", reviewer="claims_supported", severity=Severity.SCIENCE,
        artifact=paper_spec_key, location="C1",
        text="C1 over-claims; the research is correlational",
    )
    reviewer = _ScriptedReviewer(
        "claims_supported",
        initial_concerns=[concern],
        accepts_per_round={1: ["P1"]},
    )
    fake_reply = json.dumps({
        "new_spec_md": (
            "# paper spec v2\n## Claims\n- C1: X is associated with Y "
            "under condition A.\n"
        ),
        "responses": [
            {"concern_id": "P1", "response": "Reworded to 'associated with'",
             "what_changed": "C1 no longer claims causation",
             "artifacts_changed": [paper_spec_key]},
        ],
    })
    backend = _FakeBackend(responses=[fake_reply])
    spec = build_paper_spec_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    assert result.converged is True
    assert result.next_stage == "paper_planned"


def test_paper_spec_science_class_kicks_back_to_research_side(tmp_path: Path):
    """Science-class concerns on the paper spec MUST route back to the
    research side (``clarified``), not the paper side — the engine's
    adaptive kickback enforces this via the registry's kickback_routing."""
    paper_spec_key = "paper/specs/000-x/spec.md"
    artifacts = {paper_spec_key: "# paper spec\n"}
    concern = Concern(
        id="P1", reviewer="scope_vs_research", severity=Severity.SCIENCE,
        artifact=paper_spec_key, location="",
        text="paper would redefine the research question (HARKing by spec)",
    )
    reviewer = _ScriptedReviewer(
        "scope_vs_research",
        initial_concerns=[concern],
        accepts_per_round={},  # never accepts
    )
    fake_reply = json.dumps({
        "new_spec_md": "# paper spec v_n",
        "responses": [{"concern_id": "P1", "response": "tried",
                       "what_changed": "edited"}],
    })
    backend = _FakeBackend(responses=[fake_reply] * 5)
    spec = build_paper_spec_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    assert result.converged is False
    assert result.kickback is not None
    # SCIENCE on paper_clarified routes to research-side `clarified`.
    assert result.kickback.to_stage == "clarified"
    assert result.kickback.worst_severity == Severity.SCIENCE


# --- Paper-plan end-to-end -----------------------------------------------


def test_paper_plan_convergence_accepts_after_one_revision(tmp_path: Path):
    paper_plan_key = "paper/specs/000-x/plan.md"
    artifacts = {
        paper_plan_key: "# paper plan v1\nfigure-budget: 5",
        "paper/specs/000-x/spec.md": "# paper spec\n- C1: claim",
    }
    concern = Concern(
        id="PP1", reviewer="paper_structure", severity=Severity.METHODOLOGY,
        artifact=paper_plan_key, location="figure-budget",
        text="5 figures is too many for the claim density",
    )
    reviewer = _ScriptedReviewer(
        "paper_structure",
        initial_concerns=[concern],
        accepts_per_round={1: ["PP1"]},
    )
    fake_reply = json.dumps({
        "updated_artifacts": {paper_plan_key: "# paper plan v2\nfigure-budget: 3"},
        "responses": [
            {"concern_id": "PP1", "response": "tightened to 3",
             "what_changed": "figure budget reduced from 5 to 3",
             "artifacts_changed": [paper_plan_key]},
        ],
    })
    backend = _FakeBackend(responses=[fake_reply])
    spec = build_paper_plan_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    assert result.converged is True
    assert result.next_stage == "paper_tasked"


# --- Paper-tasks end-to-end ----------------------------------------------


def test_paper_tasks_convergence_two_round_resolution(tmp_path: Path):
    """Multi-round convergence: round-1 revision insufficient, round-2 OK."""
    paper_tasks_key = "paper/specs/000-x/tasks.md"
    artifacts = {
        paper_tasks_key: "# paper tasks v1\n- PT001 write methods\n",
        "paper/specs/000-x/spec.md": "# paper spec\n## Sections\n- methods\n- results\n",
        "paper/specs/000-x/plan.md": "# paper plan",
    }
    concern = Concern(
        id="PT1", reviewer="coverage", severity=Severity.REQUIREMENT,
        artifact=paper_tasks_key, location="results",
        text="results section has no task",
    )
    reviewer = _ScriptedReviewer(
        "coverage",
        initial_concerns=[concern],
        accepts_per_round={2: ["PT1"]},
    )
    round1 = json.dumps({
        "new_tasks_md": "# paper tasks v2\n- PT001 write methods\n",  # still missing results
        "responses": [{"concern_id": "PT1", "response": "tried", "what_changed": "tried"}],
    })
    round2 = json.dumps({
        "new_tasks_md": "# paper tasks v3\n- PT001 write methods\n- PT002 write results\n",
        "responses": [{"concern_id": "PT1", "response": "added results task",
                       "what_changed": "PT002 written"}],
    })
    backend = _FakeBackend(responses=[round1, round2])
    spec = build_paper_tasks_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    assert result.converged is True
    assert result.rounds_used == 2
    assert reviewer.rereview_calls == 2


# --- Paper-implement end-to-end ------------------------------------------


def test_paper_implement_convergence_dispatched_to_sub_agent(tmp_path: Path):
    """The PaperImplementReviser's `dispatched_to` field MUST be captured
    in the ConcernResponse text so the engine's log records which
    sub-agent handled which concern."""
    methods_tex = "paper/source/methods.tex"
    artifacts = {
        methods_tex: r"\section{Methods}brief",
        "paper/source/main.tex": r"\documentclass{article}",
        "__paper_spec_md__": "# paper spec\n- claim X",
    }
    concern = Concern(
        id="PI1", reviewer="writing_quality", severity=Severity.WRITING,
        artifact=methods_tex, location="Methods",
        text="Methods is one word; expand it.",
    )
    reviewer = _ScriptedReviewer(
        "writing_quality",
        initial_concerns=[concern],
        accepts_per_round={1: ["PI1"]},
    )
    fake_reply = json.dumps({
        "updated_artifacts": {methods_tex: r"\section{Methods}We did OLS regression with N=120."},
        "responses": [
            {"concern_id": "PI1", "response": "expanded methods",
             "what_changed": "methods.tex now describes regression",
             "artifacts_changed": [methods_tex],
             "dispatched_to": "paper_writing"},
        ],
    })
    backend = _FakeBackend(responses=[fake_reply])
    spec = build_paper_implement_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    assert result.converged is True
    # The dispatched_to label MUST show up in the response history so
    # the engine's log records the sub-agent attribution.
    assert any("paper_writing" in r.response for r in result.response_history)


def test_paper_implement_science_class_kicks_back_to_research_side(tmp_path: Path):
    """Per the registry, METHODOLOGY/SCIENCE concerns on paper-review
    route back to research-side `clarified` (not paper-side)."""
    main_tex = "paper/source/main.tex"
    artifacts = {main_tex: r"\documentclass{a}"}
    concern = Concern(
        id="PI1", reviewer="statistical_analysis", severity=Severity.SCIENCE,
        artifact=main_tex, location="Results",
        text="statistical test wrong for the data type",
    )
    reviewer = _ScriptedReviewer(
        "statistical_analysis",
        initial_concerns=[concern],
        accepts_per_round={},
    )
    fake_reply = json.dumps({
        "updated_artifacts": {main_tex: r"\documentclass{b}"},
        "responses": [{"concern_id": "PI1", "response": "tried", "what_changed": "tried"}],
    })
    backend = _FakeBackend(responses=[fake_reply] * 5)
    spec = build_paper_implement_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    assert result.converged is False
    assert result.kickback is not None
    assert result.kickback.to_stage == "clarified"  # research side
    assert result.kickback.worst_severity == Severity.SCIENCE
