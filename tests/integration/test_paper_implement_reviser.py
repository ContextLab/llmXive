"""Integration tests for PaperImplementReviser (spec 015 T059, FR-028)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from llmxive.convergence.revisers.paper_implement_reviser import (
    PaperImplementReviser,
    _is_paper_artifact,
)
from llmxive.convergence.types import Concern, Severity

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class _FakeResponse:
    text: str
    model: str = "fake-model"
    backend: str = "fake"


@dataclass
class _FakeBackend:
    response_text: str
    last_messages: list = None  # type: ignore[assignment]

    def chat(self, messages, model=None):  # type: ignore[no-untyped-def]
        self.last_messages = list(messages)
        return _FakeResponse(text=self.response_text)


def test_is_paper_artifact_includes_paper_content_excludes_spec_kit():
    assert _is_paper_artifact("paper/source/main.tex")
    assert _is_paper_artifact("paper/figures/fig1.pdf")
    assert _is_paper_artifact("paper/data/effect_sizes.csv")
    assert _is_paper_artifact("paper/bibliography.bib")
    # spec-kit artifacts under paper/specs/ are NOT this reviser's domain
    assert not _is_paper_artifact("paper/specs/000-x/spec.md")
    assert not _is_paper_artifact("paper/specs/000-x/plan.md")
    # research-side artifacts are NOT this reviser's domain
    assert not _is_paper_artifact("src/proj/util.py")
    assert not _is_paper_artifact("specs/000-x/spec.md")


def test_paper_implement_reviser_edits_paper_artifacts(tmp_path: Path):
    main_tex = "paper/source/main.tex"
    methods_tex = "paper/source/methods.tex"
    artifacts = {
        main_tex: r"\documentclass{article}\begin{document}\input{methods}\end{document}",
        methods_tex: r"\section{Methods}We did regression analysis.",
        "__paper_spec_md__": "# paper spec\n- C1: claim",
        "__paper_plan_md__": "# paper plan\nfigure-budget: 3",
        "__results_md__": "# results\neffect_size = 0.35",
        "__constitution__": "Principle V: real-call testing.",
    }
    concerns = [
        Concern(
            id="P1", reviewer="writing_quality", severity=Severity.WRITING,
            artifact=methods_tex, location="Section{Methods}",
            text="Methods section is one sentence; needs detail.",
        ),
    ]
    revised_methods = (
        r"\section{Methods}We performed multiple linear regression with "
        r"X as the predictor and Y as the outcome (N=120; OLS estimation; "
        r"$\alpha = 0.05$). Robustness checks included 5-fold cross-validation."
    )
    fake_reply = {
        "updated_artifacts": {methods_tex: revised_methods},
        "responses": [
            {
                "concern_id": "P1",
                "response": "Expanded Methods section to describe regression details.",
                "what_changed": "methods.tex now describes sample size + estimation procedure.",
                "artifacts_changed": [methods_tex],
                "dispatched_to": "paper_writing",
            },
        ],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = PaperImplementReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    updated, responses = reviser.revise(artifacts, concerns)

    assert "OLS estimation" in updated[methods_tex]
    # main.tex unchanged (LLM didn't emit it).
    assert updated[main_tex] == artifacts[main_tex]
    # Dispatched-to is recorded in the response text so the engine's
    # ConcernResponse log captures which sub-agent handled which concern.
    assert any("paper_writing" in r.response for r in responses)


def test_paper_implement_reviser_isolates_paper_from_research(tmp_path: Path):
    """Reviser must NOT touch research-side code even if it's in the
    artifacts dict."""
    paper_tex = "paper/source/main.tex"
    artifacts = {
        paper_tex: r"\documentclass{article}",
        "src/proj/util.py": "def add(a, b): return a + b",
        "specs/000-x/spec.md": "# research spec",
    }
    fake_reply = {
        "updated_artifacts": {
            paper_tex: r"\documentclass{revtex4}",
            "src/proj/util.py": "# malicious rewrite",  # NOT a paper artifact
        },
        "responses": [],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = PaperImplementReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(RuntimeError, match="outside the declared paper set"):
        reviser.revise(artifacts, [])


def test_paper_implement_reviser_raises_when_no_paper_artifacts(tmp_path: Path):
    backend = _FakeBackend(
        response_text=json.dumps({"updated_artifacts": {}, "responses": []})
    )
    reviser = PaperImplementReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(ValueError, match="no paper-side artifacts"):
        reviser.revise({"src/proj/util.py": "x"}, [])


def test_paper_implement_reviser_pads_missing_responses(tmp_path: Path):
    paper_tex = "paper/source/main.tex"
    backend = _FakeBackend(
        response_text=json.dumps(
            {
                "updated_artifacts": {paper_tex: "x"},
                "responses": [{"concern_id": "P1", "response": "ok", "what_changed": "x"}],
            }
        )
    )
    reviser = PaperImplementReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    concerns = [
        Concern(id="P1", reviewer="figure_critic", severity=Severity.WRITING,
                artifact=paper_tex, location="", text="x"),
        Concern(id="P2", reviewer="statistical_analysis", severity=Severity.SCIENCE,
                artifact=paper_tex, location="", text="y"),
    ]
    _, responses = reviser.revise({paper_tex: r"\documentclass{a}"}, concerns)
    by_id = {r.concern_id: r for r in responses}
    assert by_id["P2"].response == "<missing>"


def test_paper_implement_reviser_rejects_non_json(tmp_path: Path):
    paper_tex = "paper/source/main.tex"
    backend = _FakeBackend(response_text="not json")
    reviser = PaperImplementReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(RuntimeError, match="parseable JSON"):
        reviser.revise({paper_tex: r"\documentclass{a}"}, [])


def test_paper_implement_reviser_name():
    assert PaperImplementReviser.name == "paper_implementer"
