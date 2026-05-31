"""Regression tests for run-log readers (spec 015 / discrepancy #7).

Covers:
  - ``producer_of_artifact`` resolves the agent that recorded an artifact in
    its run-log ``outputs`` (the real fix for the former
    ``produced_by_agent=None`` self-review-prevention stub).
  - All readers TOLERATE foreign records in the run-log files. ``personality.py``
    writes personality-activity rows (``action``/``personality_slug`` … no
    ``run_id``) into the same ``state/run-log/<month>/*.jsonl`` files; the strict
    RunLogEntry model rejects them. The readers must SKIP such lines, not crash
    (they previously raised ValidationError — and, subtly, on the WRONG
    ValidationError: runlog imports jsonschema's, while model_validate_json
    raises pydantic's).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from llmxive.state import runlog
from llmxive.types import BackendName, Outcome, RunLogEntry

_FOREIGN_LINE = (
    '{"action": "contribute", "agent_name": "personality", '
    '"display_name": "Dan Rockmore (simulated)", "model_kind": '
    '"personality_simulator", "outcome": "no-op", "project_id": "PROJ-001-x", '
    '"personality_slug": "dan-rockmore", "ended_at": '
    '"2026-05-01T00:00:00+00:00"}'
)


def _entry(**kw: object) -> RunLogEntry:
    base: dict[str, object] = {
        "run_id": "run-1",
        "entry_id": "entry-1",
        "agent_name": "tasker",
        "project_id": "PROJ-001-x",
        "task_id": "task-1",
        "inputs": [],
        "outputs": ["projects/PROJ-001-x/specs/001-f/tasks.md"],
        "backend": BackendName.DARTMOUTH,
        "model_name": "qwen.qwen3.5-122b",
        "prompt_version": "1.0.0",
        "started_at": datetime(2026, 5, 1, tzinfo=UTC),
        "ended_at": datetime(2026, 5, 1, tzinfo=UTC),
        "outcome": Outcome.SUCCESS,
        "cost_estimate_usd": 0.0,
    }
    base.update(kw)
    return RunLogEntry(**base)  # type: ignore[arg-type]


def _logfile(tmp_path: Path) -> Path:
    return next((tmp_path / "state" / "run-log").rglob("*.jsonl"))


def test_producer_of_artifact_resolves_real_producer(tmp_path: Path) -> None:
    runlog.append_entry(_entry(), repo_root=tmp_path)
    got = runlog.producer_of_artifact(
        "PROJ-001-x", "projects/PROJ-001-x/specs/001-f/tasks.md", repo_root=tmp_path
    )
    assert got == "tasker"


def test_producer_of_artifact_none_when_unmatched(tmp_path: Path) -> None:
    runlog.append_entry(_entry(), repo_root=tmp_path)
    assert (
        runlog.producer_of_artifact("PROJ-001-x", "no/such/file.md", repo_root=tmp_path)
        is None
    )
    # Empty artifact_path is a no-op.
    assert runlog.producer_of_artifact("PROJ-001-x", "", repo_root=tmp_path) is None


def test_readers_tolerate_foreign_personality_lines(tmp_path: Path) -> None:
    """A personality-activity row mixed into the run-log must be skipped, not
    crash producer_of_artifact / latest_for_project / read_entries."""
    runlog.append_entry(_entry(), repo_root=tmp_path)
    logf = _logfile(tmp_path)
    with logf.open("a", encoding="utf-8") as fh:
        fh.write(_FOREIGN_LINE + "\n")

    # producer_of_artifact: resolves the real entry, skips the foreign line.
    assert (
        runlog.producer_of_artifact(
            "PROJ-001-x", "projects/PROJ-001-x/specs/001-f/tasks.md", repo_root=tmp_path
        )
        == "tasker"
    )
    # latest_for_project: returns the real entry (does not raise on the foreign line).
    latest = runlog.latest_for_project("PROJ-001-x", repo_root=tmp_path)
    assert latest is not None and latest.agent_name == "tasker"
    # read_entries: returns only the true RunLogEntry (foreign line skipped).
    entries = runlog.read_entries("run-1", repo_root=tmp_path)
    assert len(entries) == 1 and entries[0].agent_name == "tasker"
