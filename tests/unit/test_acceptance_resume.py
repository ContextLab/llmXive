"""A reliability run continues from the evidence the previous run saved."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.pipeline.acceptance import resume_from_evidence
from llmxive.state import project as store
from llmxive.types import Project, Stage

PID = "PROJ-9999-totient-canary"


def _evidence(root: Path, *, stage: Stage, status: str) -> Path:
    """What a run preserves: the project, its state record and the step trail."""
    (root / "projects" / PID / "specs").mkdir(parents=True)
    (root / "projects" / PID / "specs" / "tasks.md").write_text("- [ ] T001 Sieve.\n")
    now = datetime.now(UTC)
    store.save(
        Project(id=PID, title="Totient", field="mathematics", current_stage=stage,
                points_research={}, points_paper={}, created_at=now, updated_at=now,
                artifact_hashes={}),
        repo_root=root,
    )
    trail = root / "state" / "acceptance" / f"{PID}.json"
    trail.parent.mkdir(parents=True, exist_ok=True)
    trail.write_text(json.dumps({"status": status, "steps": [
        {"step": 1, "before": "planned", "after": "tasked", "elapsed_s": 1.0}]}))
    return root


def test_an_unfinished_run_is_continued_at_its_stage_with_its_trail(tmp_path):
    evidence = _evidence(tmp_path / "evidence", stage=Stage.VALIDATED, status="failed")
    repo = tmp_path / "canary"
    (repo / "state" / "model_selection").mkdir(parents=True)  # the platform snapshot's own state
    (repo / "state" / "model_selection" / "keep.json").write_text("{}")

    assert resume_from_evidence(evidence, repo, PID) is True

    assert store.load(PID, repo_root=repo).current_stage is Stage.VALIDATED
    assert (repo / "projects" / PID / "specs" / "tasks.md").read_text() == "- [ ] T001 Sieve.\n"
    trail = json.loads((repo / "state" / "acceptance" / f"{PID}.json").read_text())
    assert [s["after"] for s in trail["steps"]] == ["tasked"]
    assert (repo / "state" / "model_selection" / "keep.json").exists()


def test_an_accepted_run_is_not_continued(tmp_path):
    evidence = _evidence(tmp_path / "evidence", stage=Stage.PAPER_ACCEPTED, status="accepted")
    repo = tmp_path / "canary"
    repo.mkdir()
    assert resume_from_evidence(evidence, repo, PID) is False
    assert not (repo / "projects").exists() and not (repo / "state").exists()


def test_evidence_without_the_project_is_an_error_not_a_fresh_start(tmp_path):
    (tmp_path / "evidence" / "state").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match=PID):
        resume_from_evidence(tmp_path / "evidence", tmp_path / "canary", PID)
