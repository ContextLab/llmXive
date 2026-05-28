"""Integration tests for PlanReviser + PaperPlanReviser (spec 015 T056).

Fake-backend test covering both revisers:
- Multi-artifact editing (the plan stage produces 5 design docs).
- Side filtering (research-side ignores paper-side keys and vice-versa).
- Source-spec discovery (research: `specs/.../spec.md`; paper: `paper/specs/.../spec.md`).
- Honest failure modes: missing `updated_artifacts`, paths outside the
  declared plan set, padded missing concern responses.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from llmxive.convergence.revisers.plan_reviser import (
    PaperPlanReviser,
    PlanReviser,
    _is_plan_artifact,
    _is_source_spec,
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


# --- helper functions (unit-level) ---------------------------------------


def test_is_plan_artifact_filters_by_side():
    assert _is_plan_artifact("specs/000-x/plan.md", paper=False)
    assert _is_plan_artifact("specs/000-x/research.md", paper=False)
    assert _is_plan_artifact("specs/000-x/contracts/api.yaml", paper=False)
    assert not _is_plan_artifact("paper/specs/000-x/plan.md", paper=False)
    assert _is_plan_artifact("paper/specs/000-x/plan.md", paper=True)
    assert not _is_plan_artifact("specs/000-x/plan.md", paper=True)
    # spec.md is the SOURCE, not a plan artifact
    assert not _is_plan_artifact("specs/000-x/spec.md", paper=False)


def test_is_source_spec_filters_by_side():
    assert _is_source_spec("specs/000-x/spec.md", paper=False)
    assert not _is_source_spec("specs/000-x/spec.md", paper=True)
    assert _is_source_spec("paper/specs/000-x/spec.md", paper=True)
    assert not _is_source_spec("paper/specs/000-x/spec.md", paper=False)


# --- end-to-end revise(): research-side PlanReviser ----------------------


def test_plan_reviser_edits_multiple_artifacts(tmp_path: Path):
    plan_key = "specs/000-x/plan.md"
    data_model_key = "specs/000-x/data-model.md"
    artifacts = {
        plan_key: "# plan v1\nMethodology: regression.\n",
        data_model_key: "# data-model v1\nentity: trial\n",
        "specs/000-x/spec.md": "# spec\n## FR\n- FR-001: X\n",
        "specs/000-x/research.md": "# research notes",
        "specs/000-x/quickstart.md": "# quickstart",
        "specs/000-x/contracts/api.yaml": "openapi: 3.0",
        "__constitution__": "Principle V: real-call testing.",
    }
    concerns = [
        Concern(
            id="C1", reviewer="methodology", severity=Severity.METHODOLOGY,
            artifact=plan_key, location="Methodology", text="regression is correlational.",
        ),
        Concern(
            id="C2", reviewer="plan_consistency", severity=Severity.REQUIREMENT,
            artifact=data_model_key, location="trial entity",
            text="trial entity lacks the seed field declared in contracts/api.yaml.",
        ),
    ]
    fake_reply = {
        "updated_artifacts": {
            plan_key: "# plan v2\nMethodology: regression + control group.\n",
            data_model_key: "# data-model v2\nentity: trial\n  seed: int\n",
        },
        "responses": [
            {"concern_id": "C1", "response": "added control group",
             "what_changed": "plan.md gained control-group methodology",
             "artifacts_changed": [plan_key]},
            {"concern_id": "C2", "response": "added seed field",
             "what_changed": "trial entity now has seed",
             "artifacts_changed": [data_model_key]},
        ],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = PlanReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    updated, responses = reviser.revise(artifacts, concerns)

    assert "v2" in updated[plan_key]
    assert "seed: int" in updated[data_model_key]
    # Unchanged artifacts MUST stay unchanged (the reviser only writes keys
    # the LLM declared in updated_artifacts).
    assert updated["specs/000-x/spec.md"] == artifacts["specs/000-x/spec.md"]
    assert updated["specs/000-x/research.md"] == artifacts["specs/000-x/research.md"]
    assert {r.concern_id for r in responses} == {"C1", "C2"}

    user_msg = backend.last_messages[1].content
    assert "FR-001" in user_msg  # source spec included
    assert "Principle V" in user_msg  # constitution included
    assert "regression" in user_msg  # current plan present
    assert plan_key in user_msg
    assert data_model_key in user_msg


def test_plan_reviser_rejects_writes_outside_plan_set(tmp_path: Path):
    """If the LLM tries to write a path that isn't in the declared plan
    artifacts, the reviser must raise — not silently drop, not silently
    accept. (Honest reporting per Constitution Principle II.)"""
    plan_key = "specs/000-x/plan.md"
    artifacts = {
        plan_key: "# plan v1",
        "specs/000-x/spec.md": "# spec",
    }
    fake_reply = {
        "updated_artifacts": {
            plan_key: "# plan v2",
            "specs/000-x/spec.md": "# malicious rewrite",  # not in plan set
        },
        "responses": [],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = PlanReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(RuntimeError, match="outside the plan set"):
        reviser.revise(artifacts, [])


def test_plan_reviser_raises_when_no_plan_artifacts_present(tmp_path: Path):
    backend = _FakeBackend(
        response_text='{"updated_artifacts": {}, "responses": []}'
    )
    reviser = PlanReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(ValueError, match="no plan-stage artifacts"):
        reviser.revise({"specs/000-x/spec.md": "# spec only"}, [])


def test_plan_reviser_rejects_missing_updated_artifacts_field(tmp_path: Path):
    plan_key = "specs/000-x/plan.md"
    backend = _FakeBackend(response_text='{"responses": []}')
    reviser = PlanReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(RuntimeError, match="no usable 'updated_artifacts'"):
        reviser.revise({plan_key: "# plan"}, [])


def test_plan_reviser_pads_missing_concern_responses(tmp_path: Path):
    plan_key = "specs/000-x/plan.md"
    fake_reply = {
        "updated_artifacts": {plan_key: "# plan v2"},
        "responses": [{"concern_id": "C1", "response": "fixed", "what_changed": "done"}],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = PlanReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    concerns = [
        Concern(id="C1", reviewer="methodology", severity=Severity.WRITING,
                artifact=plan_key, location="", text="x"),
        Concern(id="C2", reviewer="spec_coverage", severity=Severity.REQUIREMENT,
                artifact=plan_key, location="", text="y"),
    ]
    _, responses = reviser.revise({plan_key: "# plan"}, concerns)
    by_id = {r.concern_id: r for r in responses}
    assert by_id["C2"].response == "<missing>"


# --- end-to-end revise(): paper-side PaperPlanReviser --------------------


def test_paper_plan_reviser_uses_paper_side_artifacts(tmp_path: Path):
    paper_plan_key = "paper/specs/000-x/plan.md"
    artifacts = {
        paper_plan_key: "# paper plan v1\nfigure-budget: 4",
        "paper/specs/000-x/spec.md": "# paper spec\n- C1: claim",
        # research-side artifacts that should NOT be in the editable plan set
        "specs/000-x/plan.md": "# research plan (different)",
        "specs/000-x/spec.md": "# research spec",
    }
    concerns = [
        Concern(
            id="P1", reviewer="paper_structure", severity=Severity.METHODOLOGY,
            artifact=paper_plan_key, location="figure-budget",
            text="figure budget too high for the claim density.",
        ),
    ]
    fake_reply = {
        "updated_artifacts": {paper_plan_key: "# paper plan v2\nfigure-budget: 3"},
        "responses": [
            {"concern_id": "P1", "response": "tightened to 3",
             "what_changed": "figure budget reduced from 4 to 3",
             "artifacts_changed": [paper_plan_key]},
        ],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = PaperPlanReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    updated, responses = reviser.revise(artifacts, concerns)

    assert updated[paper_plan_key] == "# paper plan v2\nfigure-budget: 3"
    # research-side artifact must NOT have been touched.
    assert updated["specs/000-x/plan.md"] == artifacts["specs/000-x/plan.md"]
    assert len(responses) == 1 and responses[0].concern_id == "P1"

    user_msg = backend.last_messages[1].content
    # Source spec for the paper reviser is the paper spec.md.
    assert "# paper spec" in user_msg
    # Research-side spec.md is NOT loaded as the source spec.
    assert "# research spec" not in user_msg
    # The reviser MUST list only paper-side paths as editable. We assert
    # via the LINE form ``- <path>`` so that ``specs/000-x/plan.md`` (which
    # IS a substring of ``paper/specs/000-x/plan.md``) doesn't false-match.
    listing = user_msg.split("MUST match these inputs exactly")[1]
    assert f"- {paper_plan_key}" in listing
    assert "- specs/000-x/plan.md" not in listing


def test_paper_plan_reviser_name():
    assert PaperPlanReviser.name == "paper_planner"


def test_plan_reviser_name():
    assert PlanReviser.name == "planner"
