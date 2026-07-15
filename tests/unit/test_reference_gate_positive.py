"""The reference gate is a POSITIVE gate: advance only when ALL citations verify.

Issue #1139 D15: ``has_blocking_citations`` previously blocked ONLY ``UNREACHABLE``
/ ``MISMATCH`` citations, so a ``PENDING`` (present-but-unverified) reference
silently advanced research_review -> research_accepted / paper_review ->
paper_accepted. The gate is inverted: a project may advance ONLY when EVERY
citation is currently ``VERIFIED``; ``PENDING`` / ``UNREACHABLE`` / ``MISMATCH``
/ any non-verified status blocks (bounded retry / substitution upstream).

REAL tests: real ``Citation`` records are persisted through the production
citations store and read back through the production gate.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from llmxive.agents.reference_validator import (
    has_blocking_citations,
    project_has_unverified_for_review,
)
from llmxive.state import citations as citations_store
from llmxive.types import (
    Citation,
    CitationKind,
    Project,
    Stage,
    VerificationStatus,
)

_PROJECT_ID = "PROJ-777-gate"


def _cite(status: VerificationStatus, *, cite_id: str = "c-001") -> Citation:
    return Citation(
        cite_id=cite_id,
        artifact_path=f"projects/{_PROJECT_ID}/specs/plan.md",
        artifact_hash="0" * 64,
        kind=CitationKind.URL,
        value="https://example.com/some/paper",
        cited_title="A Real Paper Title About Something",
        verification_status=status,
        verified_at=datetime.now(UTC),
    )


def _save(repo: Path, cits: list[Citation]) -> None:
    citations_store.save(_PROJECT_ID, cits, repo_root=repo)


def _project() -> Project:
    now = datetime.now(UTC)
    return Project(
        id=_PROJECT_ID,
        title="Gate fixture",
        field="testing",
        current_stage=Stage.RESEARCH_REVIEW,
        created_at=now,
        updated_at=now,
        speckit_research_dir=f"projects/{_PROJECT_ID}/specs/001-x",
    )


def test_pending_blocks_the_gate(tmp_path):
    """A PENDING citation is present-but-unverified -> BLOCKS (positive gate)."""
    _save(tmp_path, [_cite(VerificationStatus.PENDING)])
    assert has_blocking_citations(_PROJECT_ID, repo_root=tmp_path) is True


def test_all_verified_advances(tmp_path):
    """Every citation VERIFIED -> the gate does not block."""
    _save(
        tmp_path,
        [
            _cite(VerificationStatus.VERIFIED, cite_id="c-001"),
            _cite(VerificationStatus.VERIFIED, cite_id="c-002"),
        ],
    )
    assert has_blocking_citations(_PROJECT_ID, repo_root=tmp_path) is False


def test_one_pending_among_verified_blocks(tmp_path):
    """A single non-verified citation blocks even when the rest verify."""
    _save(
        tmp_path,
        [
            _cite(VerificationStatus.VERIFIED, cite_id="c-001"),
            _cite(VerificationStatus.PENDING, cite_id="c-002"),
        ],
    )
    assert has_blocking_citations(_PROJECT_ID, repo_root=tmp_path) is True


def test_unreachable_and_mismatch_still_block(tmp_path):
    """The anti-fabrication states remain blocking under the positive gate."""
    _save(tmp_path, [_cite(VerificationStatus.UNREACHABLE)])
    assert has_blocking_citations(_PROJECT_ID, repo_root=tmp_path) is True
    _save(tmp_path, [_cite(VerificationStatus.MISMATCH)])
    assert has_blocking_citations(_PROJECT_ID, repo_root=tmp_path) is True


def test_no_citations_does_not_block(tmp_path):
    """A project with no external references has nothing to verify -> advances."""
    _save(tmp_path, [])
    assert has_blocking_citations(_PROJECT_ID, repo_root=tmp_path) is False


def test_project_wrapper_matches_positive_gate(tmp_path):
    """project_has_unverified_for_review shares the positive-gate semantics."""
    _save(tmp_path, [_cite(VerificationStatus.PENDING)])
    assert project_has_unverified_for_review(_project(), repo_root=tmp_path) is True
    _save(tmp_path, [_cite(VerificationStatus.VERIFIED)])
    assert project_has_unverified_for_review(_project(), repo_root=tmp_path) is False
