"""Unit tests for FleshOutReviser (spec 015 FR-027).

Mirrors ``tests/integration/test_spec_reviser.py`` for the idea-stage
reviser: fake backend returns canned JSON, the reviser composes its
prompt and parses the response. Tests run offline (no live LLM call) —
real-call coverage lives in ``tests/real_call/`` (gated by
``LLMXIVE_REAL_TESTS=1``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from llmxive.convergence.revisers.flesh_out_reviser import (
    FleshOutReviser,
    _is_idea_artifact,
)
from llmxive.convergence.types import Concern, Severity

# Real repo root so render_prompt can resolve agents/prompts/idea_reviser.md.
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


# --- fixtures -------------------------------------------------------------


def _fixture_idea_md() -> str:
    return (
        "---\nfield: ai\nsubmitter: agent:flesh_out\n---\n\n"
        "# An idea\n\n"
        "## Research question\nDoes X cause Y?\n\n"
        "## Motivation\nIt would be useful to know.\n\n"
        "## Related work\n- [Foo (2020)](https://example.org/foo) — related.\n\n"
        "## Expected results\nWe expect a positive correlation.\n\n"
        "## Methodology sketch\n- Download data\n- Run regression\n\n"
        "## Duplicate-check\nVerdict: NOT a duplicate.\n"
    )


def _fixture_concerns() -> list[Concern]:
    return [
        Concern(
            id="I1",
            reviewer="rq_validity",
            severity=Severity.METHODOLOGY,
            artifact="projects/PROJ-001/idea/an-idea.md",
            location="Research question",
            text="The research question reads as method-grounded ('Does X cause Y?' is fine but the methodology sketch implies the predictor and predicted are derived from the same correlation). Clarify independence.",
        ),
        Concern(
            id="I2",
            reviewer="feasibility",
            severity=Severity.WRITING,
            artifact="projects/PROJ-001/idea/an-idea.md",
            location="Methodology sketch",
            text="The 'Download data' step does not name a specific dataset URL — required for GHA-feasible execution.",
        ),
    ]


# --- unit-level helpers ----------------------------------------------------


def test_is_idea_artifact_matches_paths_under_idea_dir():
    assert _is_idea_artifact("projects/PROJ-001/idea/an-idea.md")
    assert _is_idea_artifact("idea/seed.md")
    # Non-idea paths must NOT match.
    assert not _is_idea_artifact("projects/PROJ-001/spec.md")
    assert not _is_idea_artifact("projects/PROJ-001/idea/notes.txt")  # wrong ext
    # Diagnostic siblings live in idea/ but are excluded.
    assert not _is_idea_artifact("projects/PROJ-001/idea/research_question_validation.md")


# --- end-to-end revise() --------------------------------------------------


def test_revise_returns_updated_idea_and_concern_responses(tmp_path: Path):
    """End-to-end: FleshOutReviser.revise should call the backend with the
    composed prompt, parse its JSON reply, and return the new idea text
    plus a ConcernResponse for every concern."""
    idea_path = "projects/PROJ-001/idea/an-idea.md"
    artifacts = {idea_path: _fixture_idea_md()}
    concerns = _fixture_concerns()

    new_idea_text = (
        "---\nfield: ai\nsubmitter: agent:flesh_out\n---\n\n"
        "# An idea\n\n"
        "## Research question\nDoes X (measured via channel A) predict Y "
        "(measured independently via channel B)?\n\n"
        "## Motivation\nUseful, and now framed with independent measurements.\n\n"
        "## Related work\n- [Foo (2020)](https://example.org/foo) — related.\n\n"
        "## Expected results\nWe expect a positive correlation under independence.\n\n"
        "## Methodology sketch\n- Download data from https://uci.example.org/dataset.csv\n"
        "- Run regression\n\n"
        "## Duplicate-check\nVerdict: NOT a duplicate.\n"
    )
    fake_reply = {
        "new_idea_md": new_idea_text,
        "responses": [
            {
                "concern_id": "I1",
                "response": "Reframed RQ with explicit independent measurement channels.",
                "what_changed": "Research question now names channel A / channel B.",
                "artifacts_changed": [idea_path],
            },
            {
                "concern_id": "I2",
                "response": "Added explicit dataset URL.",
                "what_changed": "Methodology sketch first bullet now names UCI URL.",
                "artifacts_changed": [idea_path],
            },
        ],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))

    reviser = FleshOutReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-001",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    updated, responses = reviser.revise(artifacts, concerns)

    assert updated[idea_path] == new_idea_text
    assert len(responses) == 2
    assert {r.concern_id for r in responses} == {"I1", "I2"}
    assert all(r.artifacts_changed == [idea_path] for r in responses)

    # Verify prompt composition: system + user with every concern + the idea body.
    assert backend.last_messages is not None
    assert len(backend.last_messages) == 2
    assert backend.last_messages[0].role == "system"
    user_msg = backend.last_messages[1].content
    assert "[concern I1]" in user_msg
    assert "[concern I2]" in user_msg
    assert "Research question" in user_msg
    assert "rq_validity" in user_msg
    assert "feasibility" in user_msg


def test_revise_pads_missing_concern_responses_honestly(tmp_path: Path):
    """If the backend returns FEWER responses than concerns, the missing
    ones MUST be padded with explicit ``<missing>`` markers — no silent
    omission (Constitution Principle II)."""
    idea_path = "projects/PROJ-001/idea/an-idea.md"
    artifacts = {idea_path: _fixture_idea_md()}
    concerns = _fixture_concerns()  # 2 concerns

    fake_reply = {
        "new_idea_md": "# revised\nResearch question: refined.\n",
        "responses": [
            # only I1 — I2 deliberately missing
            {"concern_id": "I1", "response": "resolved", "what_changed": "done"},
        ],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = FleshOutReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-001",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    _, responses = reviser.revise(artifacts, concerns)

    by_id = {r.concern_id: r for r in responses}
    assert by_id["I1"].response == "resolved"
    assert by_id["I2"].response == "<missing>"
    assert "no response" in by_id["I2"].what_changed.lower()


def test_revise_rejects_missing_new_idea_md(tmp_path: Path):
    """A reply with no ``new_idea_md`` field must raise — no silent
    acceptance of a non-edit."""
    idea_path = "projects/PROJ-001/idea/an-idea.md"
    artifacts = {idea_path: _fixture_idea_md()}
    fake_reply = {"responses": []}  # missing new_idea_md entirely
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = FleshOutReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-001",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(RuntimeError, match="no usable 'new_idea_md'"):
        reviser.revise(artifacts, [])


def test_revise_rejects_unparseable_response(tmp_path: Path):
    """Non-JSON reply must raise. The engine maps RuntimeError to
    non-convergence; this fail-loud path is what makes that possible."""
    idea_path = "projects/PROJ-001/idea/an-idea.md"
    artifacts = {idea_path: _fixture_idea_md()}
    backend = _FakeBackend(response_text="not json at all")
    reviser = FleshOutReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-001",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(RuntimeError, match="parseable JSON"):
        reviser.revise(artifacts, [])


def test_revise_raises_when_no_idea_artifact_present(tmp_path: Path):
    """Engine misuse: calling the idea reviser with no idea Markdown in
    artifacts must raise rather than fabricate one."""
    backend = _FakeBackend(
        response_text='{"new_idea_md": "x", "responses": []}'
    )
    reviser = FleshOutReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-001",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(ValueError, match="no idea Markdown artifact"):
        reviser.revise({"specs/000-x/spec.md": "hi"}, [])


def test_revise_uses_fenced_json_reply(tmp_path: Path):
    """Backend that wraps its JSON in a ```json fence MUST still parse —
    the reviser strips the fences before json.loads."""
    idea_path = "projects/PROJ-001/idea/an-idea.md"
    artifacts = {idea_path: _fixture_idea_md()}
    inner = json.dumps({
        "new_idea_md": "# revised\n",
        "responses": [{"concern_id": "I1", "response": "ok", "what_changed": "ok"}],
    })
    fenced = f"```json\n{inner}\n```"
    backend = _FakeBackend(response_text=fenced)
    reviser = FleshOutReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-001",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    updated, responses = reviser.revise(artifacts, _fixture_concerns()[:1])
    assert updated[idea_path] == "# revised\n"
    assert len(responses) == 1


# --- build_idea_reviewspec smoke ------------------------------------------


def test_build_idea_reviewspec_wires_live_reviser(tmp_path: Path):
    """``build_idea_reviewspec`` MUST return a ReviewSpec whose ``.reviser``
    is the live :class:`FleshOutReviser` (not the static TodoReviser
    placeholder) — closes FR-027 for the idea stage."""
    from llmxive.convergence.reviewspecs import (
        build_idea_reviewspec,
        reviewspec_for,
    )

    backend = _FakeBackend(response_text="{}")
    spec = build_idea_reviewspec(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-001",
    )
    assert spec.stage == "flesh_out_complete"
    assert isinstance(spec.reviser, FleshOutReviser)
    assert spec.constitution_input is False
    assert spec.advance_stage == "validated"
    # The static registry still returns a placeholder (the design pattern
    # all other build_*_reviewspec helpers follow).
    static = reviewspec_for("flesh_out_complete")
    assert static is not None
    assert static.reviser is not None
    assert not isinstance(static.reviser, FleshOutReviser)
