"""Integration tests for personality-cron → living-document wiring
(spec 015 T078 / FR-047-048).

Verifies that when the target project is in ``Stage.POSTED`` the
personality dispatcher routes the comment through
``llmxive.agents.living_document.ingest_comment`` INSTEAD of writing a
formal review file. POSTED-stage projects no longer accept research /
paper reviews — comments are post-publication discussion contributions
that feed the recompile queue + Discussion-section render.

Counterpart to ``test_personality_triage.py`` (which covers the
research/paper-review routing for projects that are NOT in POSTED).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.agents.living_document import (
    pending_recompile_count,
    project_log_path,
)
from llmxive.agents.personality import (
    ACTION_COMMENT,
    OUTCOME_COMMITTED,
    OUTCOME_TRIAGE_REJECTED,
    Action,
    Personality,
    _dispatch_comment,
    _project_id_from_artifact_path,
)
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


@pytest.fixture
def persona() -> Personality:
    return Personality(
        slug="test-persona",
        display_name="Test Persona",
        summary="for tests",
        sources=["https://example.com/persona"],
        prompt_body="You are a test persona.",
        version="1.0.0",
    )


def _make_artifact(repo: Path, rel: str, body: str = "# stub\n") -> Path:
    abs_path = repo / rel
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_text(body)
    return abs_path


def _bootstrap_project(
    repo: Path,
    project_id: str,
    *,
    stage: Stage,
    speckit_research_dir: str | None = None,
    speckit_paper_dir: str | None = None,
) -> Project:
    """Materialize a real on-disk Project state file at the given
    ``current_stage``. No mocks — the dispatcher calls
    ``project_store.load`` against this file."""
    for sub in ("projects", "run-log", "locks", "citations"):
        (repo / "state" / sub).mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    proj = Project(
        id=project_id,
        title="living-document test",
        field="test",
        current_stage=stage,
        points_research={},
        points_paper={},
        created_at=now,
        updated_at=now,
        artifact_hashes={},
        speckit_research_dir=speckit_research_dir,
        speckit_paper_dir=speckit_paper_dir,
    )
    project_store.save(proj, repo_root=repo)
    return proj


# ---------------------------------------------------------------------------
# _project_id_from_artifact_path — small helper used by _dispatch_comment.
# ---------------------------------------------------------------------------


def test_project_id_extracted_from_canonical_artifact_path():
    assert _project_id_from_artifact_path(
        "projects/PROJ-001-test/paper/source/main.tex"
    ) == "PROJ-001-test"
    assert _project_id_from_artifact_path(
        "projects/PROJ-042-foo/specs/000-x/spec.md"
    ) == "PROJ-042-foo"


def test_project_id_returns_none_for_non_project_paths():
    assert _project_id_from_artifact_path("") is None
    assert _project_id_from_artifact_path("README.md") is None
    assert _project_id_from_artifact_path("reviews/foo.md") is None
    assert _project_id_from_artifact_path("projects/not-a-proj/x") is None


# ---------------------------------------------------------------------------
# POSTED-stage routing — the critical wiring this fix lands.
# ---------------------------------------------------------------------------


def test_posted_project_comment_routes_to_living_document(
    persona: Personality, tmp_path: Path,
):
    """A well-formed comment on a POSTED-stage project lands in the
    living-document log + recompile queue — NOT in the reviews store."""
    project_id = "PROJ-001-living"
    _bootstrap_project(
        tmp_path,
        project_id,
        stage=Stage.POSTED,
        speckit_research_dir=f"projects/{project_id}/specs/001-research",
        speckit_paper_dir=f"projects/{project_id}/paper/specs/001-paper",
    )
    artifact_rel = f"projects/{project_id}/paper/source/main.tex"
    _make_artifact(tmp_path, artifact_rel, "\\documentclass{article}\n")
    long_body = (
        "Reading the posted paper, I notice the figure_critic lens "
        "applies: Figure 2's caption omits the sample size N=120. The "
        "statistical_analysis section in `paper/source/results.tex` "
        "could clarify whether the regression was OLS or ridge. "
        "Otherwise a solid contribution to the claim_accuracy story."
    )
    action = Action(
        action=ACTION_COMMENT,
        reason="post-publication comment",
        target_artifact_path=artifact_rel,
        target_artifact_kind="paper",
        content=long_body,
    )
    result = _dispatch_comment(action, persona, tmp_path)
    assert result.outcome == OUTCOME_COMMITTED, (
        f"unexpected outcome: {result!r}"
    )
    # Living-document log was written (its path is the committed_path).
    assert len(result.committed_paths) == 1
    log_path = project_log_path(tmp_path / "projects" / project_id)
    assert log_path.exists()
    assert (tmp_path / result.committed_paths[0]).resolve() == log_path.resolve()
    log_text = log_path.read_text()
    # The persona slug + lens markers should appear in the log entry.
    assert persona.slug in log_text
    assert "figure_critic" in log_text
    # Recompile queue ticked up by exactly 1.
    assert pending_recompile_count(
        tmp_path / "projects" / project_id,
    ) == 1
    # CRITICAL: no review file was written under reviews/.
    reviews_dir = tmp_path / "reviews"
    review_files = list(reviews_dir.rglob("*.md")) if reviews_dir.exists() else []
    assert review_files == [], (
        f"POSTED-stage comment must NOT be written to the review store; "
        f"found {review_files!r}"
    )


def test_posted_project_off_topic_comment_rejected_via_living_document_triage(
    persona: Personality, tmp_path: Path,
):
    """An off-topic / low-quality comment on a POSTED project is rejected
    by ``ingest_comment``'s triage gate — NO log entry written, NO review
    file written, NO recompile-queue tick."""
    project_id = "PROJ-002-living"
    _bootstrap_project(
        tmp_path,
        project_id,
        stage=Stage.POSTED,
        speckit_research_dir=f"projects/{project_id}/specs/001-research",
        speckit_paper_dir=f"projects/{project_id}/paper/specs/001-paper",
    )
    artifact_rel = f"projects/{project_id}/paper/source/main.tex"
    _make_artifact(tmp_path, artifact_rel, "\\documentclass{article}\n")
    action = Action(
        action=ACTION_COMMENT,
        reason="off-topic noise",
        target_artifact_path=artifact_rel,
        target_artifact_kind="paper",
        content="lol nice",  # too short → triage rejects
    )
    result = _dispatch_comment(action, persona, tmp_path)
    assert result.outcome == OUTCOME_TRIAGE_REJECTED
    assert result.committed_paths == []
    assert "living-document triage rejected" in (result.error or "")
    # No log file, no queue tick, no review file.
    living_dir = tmp_path / "projects" / project_id / "paper" / "living_document"
    assert not (living_dir / "log.jsonl").exists()
    assert pending_recompile_count(
        tmp_path / "projects" / project_id,
    ) == 0
    reviews_dir = tmp_path / "reviews"
    review_files = list(reviews_dir.rglob("*.md")) if reviews_dir.exists() else []
    assert review_files == []


# ---------------------------------------------------------------------------
# Regression: non-POSTED projects continue to flow through the review-store
# path (T040 wiring preserved).
# ---------------------------------------------------------------------------


def test_non_posted_project_comment_routes_to_review_store_unchanged(
    persona: Personality, tmp_path: Path,
):
    """A comment on a project NOT in POSTED (here: PAPER_REVIEW) goes
    through the legacy review-store path — this is the regression
    guarantee that the POSTED routing didn't accidentally swallow the
    formal-review case."""
    project_id = "PROJ-003-paperreview"
    _bootstrap_project(
        tmp_path,
        project_id,
        stage=Stage.PAPER_REVIEW,
        speckit_research_dir=f"projects/{project_id}/specs/001-research",
        speckit_paper_dir=f"projects/{project_id}/paper/specs/001-paper",
    )
    artifact_rel = f"projects/{project_id}/paper/source/main.tex"
    _make_artifact(tmp_path, artifact_rel, "\\documentclass{article}\n")
    long_body = (
        "Reading `projects/" + project_id + "/paper/source/main.tex`, I "
        "notice the figure_critic lens applies: figure 1 lacks a caption. "
        "The statistical_analysis section needs more detail on the test "
        "used. The writing_quality is generally good. The claim_accuracy "
        "of section 3 is questionable."
    )
    action = Action(
        action=ACTION_COMMENT,
        reason="formal paper review comment",
        target_artifact_path=artifact_rel,
        target_artifact_kind="paper",
        content=long_body,
    )
    result = _dispatch_comment(action, persona, tmp_path)
    # Either committed via the review-store path (the expected sunny-day)
    # or triage-rejected — but NEVER a living-document log entry.
    assert result.outcome in {OUTCOME_COMMITTED, OUTCOME_TRIAGE_REJECTED}
    # Living-document log MUST NOT exist (this project is not POSTED).
    assert not project_log_path(tmp_path / "projects" / project_id).exists()
    assert pending_recompile_count(
        tmp_path / "projects" / project_id,
    ) == 0
    if result.outcome == OUTCOME_COMMITTED:
        # The committed path is under reviews/ (not the living-doc log).
        assert any("/Paper/" in p or "/paper" in p.lower()
                   for p in result.committed_paths)


def test_comment_without_project_state_falls_back_to_review_store(
    persona: Personality, tmp_path: Path,
):
    """Brand-new project where the state file doesn't exist yet — the
    dispatcher MUST NOT crash; it falls through to the legacy
    review-store path (existing T040 behaviour preserved)."""
    # NB: no _bootstrap_project — only the artifact exists on disk.
    project_id = "PROJ-004-nostate"
    artifact_rel = f"projects/{project_id}/specs/000-x/spec.md"
    _make_artifact(tmp_path, artifact_rel, "# spec\n## FR\n- FR-001: do X.\n")
    long_body = (
        "Reading the spec at `" + artifact_rel + "`, I notice the "
        "code_quality of the proposed implementation could be improved. "
        "Specifically the implementation_completeness lens would flag "
        "that FR-001 needs more concrete acceptance criteria. The "
        "data_quality discussion in section 2 is fine but could be "
        "expanded. Overall a solid first draft."
    )
    action = Action(
        action=ACTION_COMMENT,
        reason="legitimate review comment",
        target_artifact_path=artifact_rel,
        target_artifact_kind="spec",
        content=long_body,
    )
    result = _dispatch_comment(action, persona, tmp_path)
    # No crash; outcome is whatever the legacy review-store path produces.
    assert result.outcome in {OUTCOME_COMMITTED, OUTCOME_TRIAGE_REJECTED}
    # No living-document log was created.
    assert not project_log_path(tmp_path / "projects" / project_id).exists()
