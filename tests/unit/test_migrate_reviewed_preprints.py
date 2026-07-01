"""Reviewed-Preprints migration (2026-07-01, increment 7).

The migration reverts a pre-ethics-change intake (llmXive turned it into a full
pipeline project) back to a clean ``paper_ingested`` Reviewed Preprint: it
discards llmXive's scaffolding, preserves the ORIGINAL paper + authors, and
resets the project state — the live pipeline then finishes the job. These tests
exercise plan-building + the reversion against a real on-disk tmp repo (no LLM).
"""

from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "migrate_reviewed_preprints.py"


def _load_module():
    import sys

    spec = importlib.util.spec_from_file_location("migrate_reviewed_preprints", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    # Register BEFORE exec so the module's @dataclass can resolve its own module
    # (dataclasses look up cls.__module__ in sys.modules during processing).
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


mig = _load_module()

_PID = "PROJ-777-modified-intake"


@pytest.fixture
def repo_with_modified_intake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, object]:
    from llmxive.state import project as project_store
    from llmxive.types import Project, Stage

    repo = tmp_path / "repo"
    pdir = repo / "projects" / _PID
    (pdir / "paper" / "source").mkdir(parents=True)
    (pdir / "paper" / "pdf").mkdir(parents=True)
    (pdir / "paper" / "reviews").mkdir(parents=True)
    (pdir / "specs" / "001-x").mkdir(parents=True)
    (pdir / "code").mkdir(parents=True)
    (pdir / "idea").mkdir(parents=True)

    # ORIGINAL work (must be preserved).
    (pdir / "paper" / "metadata.json").write_text(
        json.dumps({"title": "Orig Paper", "authors": ["Alice O.", "Bob A."],
                    "arxiv_id": "2605.1", "toplevel_tex": ["main.tex"]}), encoding="utf-8")
    (pdir / "paper" / "source" / "main.tex").write_text("\\title{Orig}", encoding="utf-8")
    (pdir / "paper" / "pdf" / "original.pdf").write_bytes(b"%PDF-1.5 orig\n%%EOF")

    # llmXive MODIFICATIONS (must be discarded).
    (pdir / "paper" / "source" / "main-llmxive.tex").write_text("modified", encoding="utf-8")
    (pdir / "paper" / "pdf" / "main-llmxive.pdf").write_bytes(b"%PDF modified")
    (pdir / "paper" / "reviews" / "paper_reviewer_x__2026-06-01__paper.md").write_text("old review", encoding="utf-8")
    (pdir / "specs" / "001-x" / "spec.md").write_text("backfilled", encoding="utf-8")
    (pdir / "paper" / "revision_history.yaml").write_text("rounds: []", encoding="utf-8")
    (pdir / "code" / "run.py").write_text("print(1)", encoding="utf-8")  # review manually
    (pdir / "idea" / "followup.md").write_text("dropped-byline follow-up", encoding="utf-8")

    now = datetime.now(UTC)
    proj = Project(id=_PID, title="Orig Paper", field="cs",
                   current_stage=Stage.IN_PROGRESS,
                   speckit_research_dir=f"projects/{_PID}/specs/001-x",
                   points_research={"research_review": 1.0}, created_at=now, updated_at=now)
    project_store.save(proj, repo_root=repo)
    monkeypatch.setattr(mig, "_repo_root", lambda: repo)
    return repo, proj


def test_build_plan_detects_modifications(repo_with_modified_intake) -> None:
    repo, proj = repo_with_modified_intake
    pdir = repo / "projects" / _PID
    plan = mig.build_plan(proj, pdir, repo)

    assert plan.current_stage == "in_progress"
    assert plan.original_authors == ["Alice O.", "Bob A."]
    assert plan.authors_dropped is False
    joined = " ".join(plan.discard)
    assert "main-llmxive.tex" in joined
    assert "main-llmxive.pdf" in joined
    assert f"projects/{_PID}/specs" in plan.discard
    assert f"projects/{_PID}/paper/reviews" in plan.discard
    assert f"projects/{_PID}/paper/revision_history.yaml" in plan.discard
    assert any("idea/followup.md" in d for d in plan.discard)
    # code/ is flagged for MANUAL review, never auto-discarded.
    assert f"projects/{_PID}/code" in plan.review_manually
    assert not any("/code" in d for d in plan.discard)


def test_execute_reverts_to_clean_preprint(repo_with_modified_intake) -> None:
    from llmxive.state import project as project_store
    from llmxive.types import Stage

    repo, proj = repo_with_modified_intake
    pdir = repo / "projects" / _PID
    orig_meta = (pdir / "paper" / "metadata.json").read_bytes()
    orig_tex = (pdir / "paper" / "source" / "main.tex").read_bytes()

    plan = mig.build_plan(proj, pdir, repo)
    mig.execute_plan(plan, proj, pdir, repo)

    # Modifications gone.
    assert not (pdir / "paper" / "source" / "main-llmxive.tex").exists()
    assert not (pdir / "paper" / "pdf" / "main-llmxive.pdf").exists()
    assert not (pdir / "specs").exists()
    assert not (pdir / "paper" / "reviews").exists()
    assert not (pdir / "paper" / "revision_history.yaml").exists()
    assert not (pdir / "idea" / "followup.md").exists()
    # ORIGINAL preserved byte-for-byte.
    assert (pdir / "paper" / "metadata.json").read_bytes() == orig_meta
    assert (pdir / "paper" / "source" / "main.tex").read_bytes() == orig_tex
    assert (pdir / "paper" / "pdf" / "original.pdf").exists()
    # code/ preserved (manual review).
    assert (pdir / "code" / "run.py").exists()
    # State reset to a clean paper_ingested.
    reverted = project_store.load(_PID, repo_root=repo)
    assert reverted.current_stage == Stage.PAPER_INGESTED
    assert reverted.speckit_research_dir is None
    assert reverted.points_research == {}
