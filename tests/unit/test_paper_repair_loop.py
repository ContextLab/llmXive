"""Regression: bounded automatic repair loop (spec 023 / FR-023).

Compile failures and audit defects convert into repair work-specs through
the SAME revision machinery the review kickbacks use (Constitution I);
the loop is bounded by MAX_REPAIR_ROUNDS — at the cap the paper keeps its
honest failure/fallback status instead of looping.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.state import paper_status as ps
from llmxive.state import project as project_store
from llmxive.types import Project, Stage

PAPER = "PROJ-931-repair"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    project = Project(
        id=PAPER,
        title="repair test",
        field="test",
        current_stage=Stage.PAPER_REVIEW,
        created_at=now,
        updated_at=now,
        artifact_hashes={},
        speckit_research_dir=f"projects/{PAPER}/specs/001-t",
        speckit_paper_dir=f"projects/{PAPER}/paper/specs/001-p",
    )
    project_store.save(project, repo_root=tmp_path)
    return tmp_path


def test_compile_failure_generates_repair_workspec(repo: Path) -> None:
    ps.record_compile_result(
        PAPER,
        {"ok": False, "strategy": None, "pdf": None,
         "errors": ["lualatex failed:\n! Undefined control sequence."]},
        repo_root=repo,
    )

    spec_dir = ps.ensure_repair_round(PAPER, repo_root=repo)

    assert spec_dir is not None
    tasks = (spec_dir / "tasks.md").read_text(encoding="utf-8")
    assert "Undefined control sequence" in tasks
    # The project (at paper_review) carries the work-spec — the SAME
    # implementer that handles review revisions consumes it (FR-023).
    saved = project_store.load(PAPER, repo_root=repo)
    assert saved.revision_spec_path == str(spec_dir.relative_to(repo))
    rec = ps.load(PAPER, repo_root=repo)
    assert rec["repair_rounds"] == 1


def test_audit_defects_generate_repair_workspec(repo: Path) -> None:
    ps.record_compile_result(
        PAPER,
        {"ok": True, "strategy": "llmxive-compile",
         "pdf": "p/main-llmxive.pdf", "errors": []},
        repo_root=repo,
    )
    ps.record_audit_result(
        PAPER,
        {"passed": False,
         "defects": [{"kind": "non_square_bracket_cite", "page": 4,
                      "detail": "author-year citation rendered"}]},
        repo_root=repo,
    )

    spec_dir = ps.ensure_repair_round(PAPER, repo_root=repo)

    assert spec_dir is not None
    tasks = (spec_dir / "tasks.md").read_text(encoding="utf-8")
    assert "non_square_bracket_cite" in tasks


def test_repair_loop_is_bounded(repo: Path) -> None:
    ps.record_compile_result(
        PAPER,
        {"ok": False, "strategy": None, "pdf": None, "errors": ["compile failed"]},
        repo_root=repo,
    )
    rounds = []
    for _ in range(ps.MAX_REPAIR_ROUNDS + 2):
        spec_dir = ps.ensure_repair_round(PAPER, repo_root=repo)
        rounds.append(spec_dir)
        # Simulate the implementer consuming the spec between rounds.
        saved = project_store.load(PAPER, repo_root=repo)
        if saved.revision_spec_path:
            project_store.save(
                saved.model_copy(update={"revision_spec_path": None}),
                repo_root=repo,
            )
    produced = [r for r in rounds if r is not None]
    assert len(produced) == ps.MAX_REPAIR_ROUNDS, (
        "after the cap, no further rounds — the paper keeps its honest "
        "fallback status"
    )
    rec = ps.load(PAPER, repo_root=repo)
    assert rec["repair_rounds"] == ps.MAX_REPAIR_ROUNDS
    assert rec["status"] == ps.STATUS_FALLBACK


def test_nothing_to_repair_is_a_noop(repo: Path) -> None:
    ps.record_compile_result(
        PAPER,
        {"ok": True, "strategy": "llmxive-compile",
         "pdf": "p/main-llmxive.pdf", "errors": []},
        repo_root=repo,
    )
    assert ps.ensure_repair_round(PAPER, repo_root=repo) is None
