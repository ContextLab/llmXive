"""Integration tests for the PaperSpecReviser (spec 015 T055, FR-006/028).

Mirrors the research-side ``test_spec_reviser.py``: fake backend, no real
API. Covers paper-side artifact discovery, research-context gathering,
code/data summary injection, missing-response padding, and JSON-failure
handling.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from llmxive.convergence.revisers.paper_spec_reviser import PaperSpecReviser
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
        # FR-011 self-consistency audit turns are content-distinct (their
        # system prompt opens with the audit banner). Return a clean 'ok'
        # audit reply for those WITHOUT recording them as last_messages, so
        # the revision call's messages stay observable for assertions.
        sys_text = getattr(messages[0], "content", "") if messages else ""
        if "auditing a revision you just produced" in sys_text:
            return _FakeResponse(text="ok: true\nproblems: []\n")
        self.last_messages = list(messages)
        return _FakeResponse(text=self.response_text)


def _fixture_paper_spec() -> str:
    return (
        "# Paper Spec — PROJ-test-x\n\n"
        "## Reader Scenarios\n"
        "- Skim path: abstract + figure 1 + conclusion.\n\n"
        "## Claims\n"
        "- C1: X causes Y under [NEEDS CLARIFICATION: which condition?].\n"
    )


def _fixture_research_artifacts() -> dict[str, str]:
    return {
        "specs/000-x/spec.md": (
            "# Research spec\n## FR\n- FR-001: measure Y from X.\n"
        ),
        "specs/000-x/plan.md": (
            "# Research plan\nMethodology: regression analysis.\n"
        ),
        "specs/000-x/tasks.md": (
            "# Research tasks\n- T001: implement measurement.\n"
        ),
    }


def _fixture_concerns() -> list[Concern]:
    return [
        Concern(
            id="PC1",
            reviewer="claims_supported",
            severity=Severity.SCIENCE,
            artifact="paper/specs/000-x/spec.md",
            location="C1",
            text="C1 over-claims causation; research is correlational only.",
        ),
        Concern(
            id="PC2",
            reviewer="required_sections_figures",
            severity=Severity.REQUIREMENT,
            artifact="paper/specs/000-x/spec.md",
            location="(missing)",
            text="Required Methods section is not declared.",
        ),
    ]


def test_revise_returns_updated_paper_spec_and_responses(tmp_path: Path):
    paper_spec_key = "paper/specs/000-x/spec.md"
    artifacts: dict[str, str] = {
        paper_spec_key: _fixture_paper_spec(),
        **_fixture_research_artifacts(),
        "__code_summary__": "code: 12 python modules, 3 helpers",
        "__data_summary__": "data: ds002800 (open neuro)",
        "__comments_block__": "personality(simulated): consider effect size.",
    }
    new_paper_spec = (
        "# Paper Spec — PROJ-test-x\n\n## Reader Scenarios\n- Skim: abstract+fig.\n\n"
        "## Claims\n- C1: X is associated with Y under condition A.\n\n"
        "## Methods\n- regression analysis.\n"
    )
    fake_reply = {
        "new_spec_md": new_paper_spec,
        "responses": [
            {
                "concern_id": "PC1",
                "response": "Replaced 'causes' with 'is associated with'.",
                "what_changed": "C1 reworded to match correlational evidence.",
                "artifacts_changed": [paper_spec_key],
            },
            {
                "concern_id": "PC2",
                "response": "Added Methods section declaring regression analysis.",
                "what_changed": "Methods section now present in paper spec.",
                "artifacts_changed": [paper_spec_key],
            },
        ],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = PaperSpecReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    updated, responses = reviser.revise(artifacts, _fixture_concerns())

    assert updated[paper_spec_key] == new_paper_spec
    assert {r.concern_id for r in responses} == {"PC1", "PC2"}

    assert backend.last_messages is not None
    user_msg = backend.last_messages[1].content
    # User prompt must include research bundle + code+data summaries +
    # paper spec body + concerns + markers.
    assert "FR-001" in user_msg  # research spec.md included
    assert "regression analysis" in user_msg  # plan.md included
    assert "code: 12 python modules" in user_msg
    assert "data: ds002800" in user_msg
    assert "[concern PC1]" in user_msg
    assert "[concern PC2]" in user_msg
    assert "[marker 0]" in user_msg


def test_revise_handles_missing_research_context(tmp_path: Path):
    """Reviser must still function with only the paper spec — research
    artifacts are not strictly required (the panel will flag if absent)."""
    paper_spec_key = "paper/specs/000-x/spec.md"
    artifacts = {paper_spec_key: _fixture_paper_spec()}
    backend = _FakeBackend(
        response_text=json.dumps(
            {"new_spec_md": "# revised paper spec", "responses": []}
        )
    )
    reviser = PaperSpecReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    updated, responses = reviser.revise(artifacts, [])
    assert updated[paper_spec_key] == "# revised paper spec"
    assert responses == []
    # User message documents the missing research context honestly.
    user_msg = backend.last_messages[1].content
    assert "(no research-side artifacts supplied)" in user_msg


def test_revise_pads_missing_paper_concern_responses(tmp_path: Path):
    paper_spec_key = "paper/specs/000-x/spec.md"
    artifacts = {paper_spec_key: _fixture_paper_spec()}
    backend = _FakeBackend(
        response_text=json.dumps(
            {
                "new_spec_md": "# revised paper spec",
                # only PC1 — PC2 missing
                "responses": [
                    {"concern_id": "PC1", "response": "fixed", "what_changed": "done"},
                ],
            }
        )
    )
    reviser = PaperSpecReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    _, responses = reviser.revise(artifacts, _fixture_concerns())
    by_id = {r.concern_id: r for r in responses}
    assert by_id["PC1"].response == "fixed"
    assert by_id["PC2"].response == "<missing>"


def test_revise_raises_on_no_paper_spec(tmp_path: Path):
    backend = _FakeBackend(response_text='{"new_spec_md":"x","responses":[]}')
    reviser = PaperSpecReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    # research-side artifacts present but no paper spec
    with pytest.raises(ValueError, match="no paper-side 'spec\\.md' artifact"):
        reviser.revise(_fixture_research_artifacts(), [])


def test_revise_rejects_non_json(tmp_path: Path):
    paper_spec_key = "paper/specs/000-x/spec.md"
    backend = _FakeBackend(response_text="this is prose not json")
    reviser = PaperSpecReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(RuntimeError, match="parseable JSON"):
        reviser.revise({paper_spec_key: _fixture_paper_spec()}, [])


def test_paper_spec_reviser_name():
    """Reviser name is the collapsed-pair label the engine logs in
    `ConcernResponse.what_changed` / `ProgressRecord` provenance."""
    assert PaperSpecReviser.name == "paper_specifier+paper_clarifier"
