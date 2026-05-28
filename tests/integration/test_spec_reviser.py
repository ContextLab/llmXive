"""Integration tests for the SpecReviser (spec 015 T054, FR-006/027).

Exercises the spec-convergence-unit reviser end-to-end with a fake backend
that returns predetermined JSON: verifies that ``revise(artifacts, concerns)``
correctly folds concerns + ``[NEEDS CLARIFICATION]`` markers into ONE pass,
returns the new spec text, and produces a ConcernResponse for every concern.

NOTE: a real-call variant lives in ``tests/real_call/`` (gated by the
``LLMXIVE_REAL_TESTS=1`` env var per the project's testing convention).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from llmxive.convergence.revisers.spec_reviser import (
    SpecReviser,
    _scan_markers,
    _strip_json_fences,
)
from llmxive.convergence.types import Concern, Severity

# The reviser needs the real repo root so `render_prompt` can resolve
# ``agents/prompts/clarifier.md``. Tests still use ``tmp_path`` for the
# summarize cache so they leave no on-disk side effects.
_REPO_ROOT = Path(__file__).resolve().parents[2]


# --- fake backend ---------------------------------------------------------


@dataclass
class _FakeResponse:
    text: str
    model: str = "fake-model"
    backend: str = "fake"


@dataclass
class _FakeBackend:
    """Backend stand-in: returns ``response_text`` for every ``chat`` call
    and records the messages passed in."""

    response_text: str
    last_messages: list = None  # type: ignore[assignment]

    def chat(self, messages, model=None):  # type: ignore[no-untyped-def]
        self.last_messages = list(messages)
        return _FakeResponse(text=self.response_text)


def _fixture_spec_with_markers() -> str:
    return (
        "# Spec — PROJ-test-x\n\n"
        "## Stories\n"
        "- US1: A user can compute the [NEEDS CLARIFICATION: which metric?].\n\n"
        "## Functional Requirements\n"
        "- FR-001: System MUST accept input.\n"
        "- FR-002: System SHOULD **NEEDS CLARIFICATION**: pick a threshold value.\n\n"
        "## Success Criteria\n"
        "- SC-001: First user can complete the workflow in < 5 minutes.\n"
    )


def _fixture_idea() -> str:
    return "# Idea\n\nResearch question: does X cause Y?\nKey constraint: real data only.\n"


def _fixture_concerns() -> list[Concern]:
    return [
        Concern(
            id="C1",
            reviewer="requirements_coverage",
            severity=Severity.REQUIREMENT,
            artifact="specs/000-x/spec.md",
            location="FR-002",
            text="FR-002 contains a NEEDS CLARIFICATION marker that must be resolved.",
        ),
        Concern(
            id="C2",
            reviewer="testability",
            severity=Severity.WRITING,
            artifact="specs/000-x/spec.md",
            location="SC-001",
            text="'< 5 minutes' should be tied to a measurement procedure.",
        ),
    ]


# --- unit-level helpers ----------------------------------------------------


def test_scan_markers_handles_both_forms():
    spec = _fixture_spec_with_markers()
    markers = _scan_markers(spec)
    assert len(markers) == 2
    assert "which metric" in markers[0]
    assert "threshold" in markers[1]


def test_scan_markers_returns_empty_when_no_markers():
    assert _scan_markers("# Clean spec\nFR-001: do X.\n") == []


def test_strip_json_fences_handles_fenced_and_unfenced():
    fenced = '```json\n{"a": 1}\n```'
    assert _strip_json_fences(fenced) == '{"a": 1}'
    assert _strip_json_fences('{"a": 1}') == '{"a": 1}'


# --- end-to-end revise() --------------------------------------------------


def test_revise_returns_updated_spec_and_concern_responses(tmp_path: Path):
    """End-to-end: SpecReviser.revise should call the backend with the
    composed prompt, parse its JSON reply, and return the new spec text
    plus a ConcernResponse for every concern."""
    spec_path = "specs/000-x/spec.md"
    artifacts = {
        spec_path: _fixture_spec_with_markers(),
        "idea/test.md": _fixture_idea(),
    }
    concerns = _fixture_concerns()

    new_spec_text = (
        "# Spec — PROJ-test-x\n\n"
        "## Stories\n- US1: A user can compute the AUC.\n\n"
        "## Functional Requirements\n"
        "- FR-001: System MUST accept input.\n"
        "- FR-002: System SHOULD use threshold 0.5.\n\n"
        "## Success Criteria\n"
        "- SC-001: First user can complete the workflow in < 5 minutes "
        "(measured by `tests/e2e/test_first_user_flow.py::test_under_five_minutes`).\n"
    )
    fake_reply = {
        "new_spec_md": new_spec_text,
        "responses": [
            {
                "concern_id": "C1",
                "response": "Resolved by picking threshold 0.5.",
                "what_changed": "FR-002 now names threshold 0.5 explicitly.",
                "artifacts_changed": [spec_path],
            },
            {
                "concern_id": "C2",
                "response": "Pinned SC-001 to a real test.",
                "what_changed": "Added pytest path to SC-001 acceptance.",
                "artifacts_changed": [spec_path],
            },
        ],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))

    reviser = SpecReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    updated, responses = reviser.revise(artifacts, concerns)

    assert updated[spec_path] == new_spec_text
    assert _scan_markers(updated[spec_path]) == []  # markers were resolved
    assert len(responses) == 2
    assert {r.concern_id for r in responses} == {"C1", "C2"}
    assert all(r.artifacts_changed == [spec_path] for r in responses)

    # The backend was called with a system+user pair; the user message must
    # mention every concern id AND every marker AND the current spec.
    assert backend.last_messages is not None
    assert len(backend.last_messages) == 2
    assert backend.last_messages[0].role == "system"
    user_msg = backend.last_messages[1].content
    assert "[concern C1]" in user_msg
    assert "[concern C2]" in user_msg
    assert "FR-002" in user_msg  # current spec body present
    assert "[marker 0]" in user_msg  # markers enumerated


def test_revise_pads_missing_concern_responses_honestly(tmp_path: Path):
    """If the backend returns FEWER responses than concerns, the missing
    ones must be padded with explicit ``<missing>`` markers — no silent
    omission, no fake-resolved entries (Constitution Principle II)."""
    spec_path = "specs/000-x/spec.md"
    artifacts = {spec_path: _fixture_spec_with_markers()}
    concerns = _fixture_concerns()  # 2 concerns

    fake_reply = {
        "new_spec_md": "# revised spec\nFR-002: threshold 0.5\n",
        "responses": [
            # only C1 — C2 deliberately missing
            {"concern_id": "C1", "response": "resolved", "what_changed": "done"},
        ],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = SpecReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    _, responses = reviser.revise(artifacts, concerns)

    by_id = {r.concern_id: r for r in responses}
    assert by_id["C1"].response == "resolved"
    assert by_id["C2"].response == "<missing>"
    assert "no response" in by_id["C2"].what_changed.lower()


def test_revise_rejects_missing_new_spec_md(tmp_path: Path):
    """A reply with no ``new_spec_md`` field must raise — no silent acceptance
    of a non-edit."""
    spec_path = "specs/000-x/spec.md"
    artifacts = {spec_path: _fixture_spec_with_markers()}
    fake_reply = {"responses": []}  # missing new_spec_md entirely
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = SpecReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(RuntimeError, match="no usable 'new_spec_md'"):
        reviser.revise(artifacts, [])


def test_revise_rejects_unparseable_response(tmp_path: Path):
    """Non-JSON reply must raise. The engine maps RuntimeError to
    non-convergence; this fail-loud path is what makes that possible."""
    spec_path = "specs/000-x/spec.md"
    artifacts = {spec_path: _fixture_spec_with_markers()}
    backend = _FakeBackend(response_text="not json at all")
    reviser = SpecReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(RuntimeError, match="parseable JSON"):
        reviser.revise(artifacts, [])


def test_revise_raises_when_no_spec_artifact_present(tmp_path: Path):
    """Engine misuse: calling the spec reviser with no spec.md in artifacts
    must raise rather than fabricate one."""
    backend = _FakeBackend(response_text='{"new_spec_md": "x", "responses": []}')
    reviser = SpecReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(ValueError, match=r"no 'spec\.md' artifact"):
        reviser.revise({"idea/x.md": "hi"}, [])
