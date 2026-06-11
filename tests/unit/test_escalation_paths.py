"""Regression: de-escalation path discipline (spec 023 / FR-015..017).

* Engine failures file a tracked, DEDUPED GitHub issue (recording fake at
  the ``gh`` subprocess boundary) and the project STAYS schedulable — no
  ``human_input_needed.yaml``, no stage change.
* Infrastructure failures (BackendUnavailable / TransientBackendError)
  produce NO record, NO issue, NO marker — clean abort, retry later
  (extends the PR-#302 router classification).
* The convergence-kickback cap escalation carries an exhaustion-evidence
  record (FR-017).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llmxive.backends.base import BackendUnavailable, TransientBackendError
from llmxive.speckit import _stage_panel
from llmxive.speckit._stage_panel import StagePanelEscalation, run_stage_panel
from llmxive.state import escalations


class _RecordingGh:
    """Fake `gh` at the subprocess boundary (same tuple protocol)."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self._next_number = 100

    def __call__(self, *args: str) -> tuple[int, str, str]:
        self.calls.append(args)
        if args[0] == "api" and "-X" in args and "POST" in args:
            self._next_number += 1
            return 0, json.dumps({"number": self._next_number}), ""
        if args[0] == "api" and args[1].startswith("search/issues"):
            return 0, json.dumps({"items": []}), ""
        return 0, "{}", ""


def test_engine_failure_files_issue_once(tmp_path: Path) -> None:
    gh = _RecordingGh()
    n1 = escalations.file_engine_failure_issue(
        project_id="PROJ-912-x", stage="plan",
        error="KeyError: 'verdict'", evidence="trace...",
        repo_root=tmp_path, gh=gh,
    )
    n2 = escalations.file_engine_failure_issue(
        project_id="PROJ-912-x", stage="plan",
        error="KeyError: 'verdict' (again)", repo_root=tmp_path, gh=gh,
    )
    assert n1 == 101
    assert n2 == 101, "same project+failure class reuses the ledgered issue"
    posts = [c for c in gh.calls if "POST" in c]
    assert len(posts) == 1, "deduped — exactly one issue created"
    # NO escalation record for engine failures (they file issues instead).
    assert escalations.list_records(repo_root=tmp_path) == []


def test_engine_failure_filing_is_best_effort(tmp_path: Path) -> None:
    def gh_down(*args: str) -> tuple[int, str, str]:
        return 1, "", "api: connection refused"

    n = escalations.file_engine_failure_issue(
        project_id="PROJ-913-x", stage="plan",
        error="ValueError: boom", repo_root=tmp_path, gh=gh_down,
    )
    assert n is None  # no crash, no park — the project just retries later


def test_stage_panel_engine_failure_files_issue_not_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The panel's generic-Exception path now files the issue and does NOT
    write human_input_needed.yaml (FR-016)."""
    filed: list[dict] = []

    def fake_file(**kwargs):
        filed.append(kwargs)
        return 7

    monkeypatch.setattr(escalations, "file_engine_failure_issue", fake_file)
    monkeypatch.setattr(
        _stage_panel, "run_engine_for_project",
        lambda **kw: (_ for _ in ()).throw(KeyError("engine exploded")),
    )
    memory_dir = tmp_path / "projects" / "PROJ-914-x" / ".specify" / "memory"
    memory_dir.mkdir(parents=True)

    with pytest.raises(StagePanelEscalation):
        run_stage_panel(
            stage_label="plan",
            spec=None,  # never reached — the engine raises first
            artifact_paths={},
            extra_inputs={},
            repo_root=tmp_path,
            memory_dir=memory_dir,
        )

    assert filed and filed[0]["project_id"] == "PROJ-914-x"
    assert not (memory_dir / "human_input_needed.yaml").exists(), (
        "engine failures must NOT park the project (FR-016)"
    )


@pytest.mark.parametrize("exc", [
    BackendUnavailable("endpoint down"),
    TransientBackendError("connection reset"),
])
def test_infra_failures_produce_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exc: Exception
) -> None:
    """FR-015: outages re-raise AS-IS — no marker, no issue, no record."""
    filed: list[dict] = []
    monkeypatch.setattr(
        escalations, "file_engine_failure_issue",
        lambda **kw: filed.append(kw),
    )
    monkeypatch.setattr(
        _stage_panel, "run_engine_for_project",
        lambda **kw: (_ for _ in ()).throw(exc),
    )
    memory_dir = tmp_path / "projects" / "PROJ-915-x" / ".specify" / "memory"
    memory_dir.mkdir(parents=True)

    with pytest.raises(type(exc)):
        run_stage_panel(
            stage_label="plan",
            spec=None,
            artifact_paths={},
            extra_inputs={},
            repo_root=tmp_path,
            memory_dir=memory_dir,
        )

    assert filed == []
    assert not (memory_dir / "human_input_needed.yaml").exists()
    assert escalations.list_records(repo_root=tmp_path) == []


def test_digest_aggregates_and_marks(tmp_path: Path) -> None:
    gh = _RecordingGh()
    escalations.write_record(
        escalations.EscalationRecord(
            project_id="PROJ-916-x", stage="plan",
            loop="convergence-kickback", bound=3, rounds_used=3,
        ),
        repo_root=tmp_path,
    )
    number = escalations.update_digest(repo_root=tmp_path, gh=gh)
    assert number == 101
    assert escalations.list_records(repo_root=tmp_path, open_only=True) == [], (
        "digested records carry digest_id and stop re-aggregating"
    )
    # A second run with nothing open does nothing.
    assert escalations.update_digest(repo_root=tmp_path, gh=gh) is None
