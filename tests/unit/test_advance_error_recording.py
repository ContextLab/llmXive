"""A per-project advancement failure must NOT crash the run/worker (returning
non-zero would skip the workflow commit, discard progress, and red-X the matrix
job). It is recorded to state/advance_errors/<id>.json and the run exits 0."""
from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime

import pytest

from llmxive import cli
from llmxive.pipeline import graph
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


@pytest.fixture(autouse=True)
def _isolate_env():
    """``cli._cmd_run`` sets process-global env vars (e.g. LLMXIVE_CLAIM_FILL via
    ``os.environ.setdefault``); snapshot + restore os.environ so this test can
    NEVER leak into later tests (the order-dependent test_flesh_out_reviser
    pollution this otherwise caused)."""
    saved = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(saved)


def _make_project(repo, pid: str) -> Project:
    (repo / "projects" / pid).mkdir(parents=True)
    (repo / "state" / "projects").mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    p = Project(id=pid, title="x", field="t", current_stage=Stage.BRAINSTORMED,
                created_at=now, updated_at=now)
    project_store.save(p, repo_root=repo)
    return p


def test_record_advance_error_writes_and_increments(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    p = _make_project(tmp_path, "PROJ-901-x")
    cli._record_advance_error(p, RuntimeError("dead reference: HTTP 404"))
    cli._record_advance_error(p, RuntimeError("dead reference: HTTP 404"))
    rec = json.loads((tmp_path / "state" / "advance_errors" / "PROJ-901-x.json")
                     .read_text(encoding="utf-8"))
    # INVARIANT (issue #1139): a recurring failure is COUNTED, not dismissed. The
    # schema is now typed (consecutive_count instead of a bare count) and carries a
    # control disposition the scheduler honours.
    assert rec["consecutive_count"] == 2
    assert "404" in rec["last_error"]
    assert rec["stage"] == "brainstormed"
    for key in ("class", "fingerprint", "status", "retry_after", "remediation"):
        assert key in rec


def test_run_exits_zero_and_records_on_project_failure(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    pid = "PROJ-902-x"
    _make_project(tmp_path, pid)

    def _boom(project):
        raise RuntimeError("research.md reference is unreachable: 'https://x/' (HTTP 404)")
    monkeypatch.setattr(graph, "run_one_step", _boom)

    args = argparse.Namespace(agent=None, stage=None, max_tasks=1, project=pid,
                              worker=None, workers=None, personality=None)
    rc = cli._cmd_run(args)
    assert rc == 0  # INVARIANT: did NOT crash the worker
    rec_path = tmp_path / "state" / "advance_errors" / f"{pid}.json"
    assert rec_path.exists()  # INVARIANT: the failure is recorded
    # The typed record classifies the dead reference as permanent -> rerouted.
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    assert rec["fingerprint"] == "unreachable_reference"
    assert rec["class"] == "permanent"
    assert rec["status"] == "rerouted"


def test_run_clears_record_on_successful_step(tmp_path, monkeypatch) -> None:
    """The SUCCESS path (run_one_step returns without raising) clears the ledger
    so consecutive_count reflects CONSECUTIVE failures, not lifetime failures."""
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    pid = "PROJ-903-x"
    p = _make_project(tmp_path, pid)
    # Pre-seed a recorded failure.
    cli._record_advance_error(
        p, RuntimeError("every backend in chain ['dartmouth', 'local'] failed")
    )
    rec_path = tmp_path / "state" / "advance_errors" / f"{pid}.json"
    assert rec_path.exists()

    # Now a step SUCCEEDS (advances the stage).
    def _advance(project):
        return project.model_copy(update={"current_stage": Stage.PROJECT_INITIALIZED})
    monkeypatch.setattr(graph, "run_one_step", _advance)

    args = argparse.Namespace(agent=None, stage=None, max_tasks=1, project=pid,
                              worker=None, workers=None, personality=None)
    rc = cli._cmd_run(args)
    assert rc == 0
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    assert rec["status"] == "cleared"
    assert rec["consecutive_count"] == 0
