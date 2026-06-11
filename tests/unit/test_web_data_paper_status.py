"""Regression: the public shelf reflects each paper's TRUE status
(spec 023 / FR-024). Zero unmarked fallbacks: a served PDF without a
status record surfaces as "unverified" (fail-closed), never as healthy.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from llmxive.state import paper_status as ps
from llmxive.state import project as project_store
from llmxive.types import Project, Stage
from llmxive.web_data import _paper_status_entry

PAPER = "PROJ-932-shelf"


def _project(repo: Path, *, with_pdf: bool) -> Project:
    pdf_dir = repo / "projects" / PAPER / "paper" / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    if with_pdf:
        (pdf_dir / "main-llmxive.pdf").write_bytes(b"%PDF fake")
    (repo / "state" / "projects").mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    project = Project(
        id=PAPER,
        title="shelf test",
        field="test",
        current_stage=Stage.PAPER_REVIEW,
        created_at=now,
        updated_at=now,
        artifact_hashes={},
        speckit_research_dir=f"projects/{PAPER}/specs/001-t",
        speckit_paper_dir=f"projects/{PAPER}/paper/specs/001-p",
    )
    project_store.save(project, repo_root=repo)
    return project


def test_audited_paper_shows_audited(tmp_path: Path) -> None:
    project = _project(tmp_path, with_pdf=True)
    ps.record_compile_result(
        PAPER,
        {"ok": True, "strategy": "llmxive-compile",
         "pdf": "p/main-llmxive.pdf", "errors": []},
        repo_root=tmp_path,
    )
    ps.record_audit_result(PAPER, {"passed": True, "defects": []}, repo_root=tmp_path)

    entry = _paper_status_entry(tmp_path, project)

    assert entry["status"] == "audited"
    assert entry["audit_passed"] is True
    assert entry["failure"] is None


def test_fallback_paper_shows_marked_fallback_with_reason(tmp_path: Path) -> None:
    project = _project(tmp_path, with_pdf=True)
    ps.record_compile_result(
        PAPER,
        {"ok": True, "strategy": "arxiv-fallback",
         "pdf": "p/2605.1.pdf", "errors": ["restyle step failed"]},
        repo_root=tmp_path,
    )

    entry = _paper_status_entry(tmp_path, project)

    assert entry["status"] == "fallback_original"
    assert "restyle step failed" in entry["failure"]


def test_served_pdf_without_record_is_unverified_not_healthy(tmp_path: Path) -> None:
    """The fail-closed display: pre-023's silent fallbacks can never read
    as healthy again."""
    project = _project(tmp_path, with_pdf=True)
    entry = _paper_status_entry(tmp_path, project)
    assert entry == {"status": "unverified", "failure": None, "audit_passed": None}


def test_no_pdf_no_entry(tmp_path: Path) -> None:
    project = _project(tmp_path, with_pdf=False)
    assert _paper_status_entry(tmp_path, project) is None
