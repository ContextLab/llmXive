"""Tests for the run-log writer in `submission_intake.process_submission_issue`.

The Activity tab on the website reads only from
`state/run-log/<YYYY-MM>/*.jsonl`. Before this writer existed, the
intake processed issues into new projects but emitted nothing to the
run-log, so the Activity feed showed no record of the 15 issues
intake handled in run #25976994027.

These tests verify each terminal status path writes a properly-shaped
JSONL entry.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch


def _read_run_log_lines(repo: Path) -> list[dict]:
    log_root = repo / "state" / "run-log"
    if not log_root.is_dir():
        return []
    lines: list[dict] = []
    for month_dir in log_root.iterdir():
        if not month_dir.is_dir():
            continue
        for jsonl in month_dir.glob("*.jsonl"):
            for raw in jsonl.read_text(encoding="utf-8").splitlines():
                if raw.strip():
                    lines.append(json.loads(raw))
    return lines


def test_skipped_already_closed_issue_writes_log(tmp_path: Path) -> None:
    from llmxive.agents.submission_intake import process_submission_issue
    closed_issue = {"number": 9999, "state": "closed", "body": "", "user": {"login": "alice"}}
    result = process_submission_issue(closed_issue, repo_root=tmp_path, gh=lambda *a, **k: (0, "", ""))
    assert result.status == "skipped"
    entries = _read_run_log_lines(tmp_path)
    assert len(entries) == 1
    e = entries[0]
    assert e["agent_name"] == "submission_intake"
    assert e["outcome"] == "no-op"
    assert e["issue_number"] == 9999
    assert e["issue_author"] == "alice"
    assert e["project_id"] is None  # nothing was created
    assert "started_at" in e and "ended_at" in e


def test_malformed_labels_writes_failed_log(tmp_path: Path) -> None:
    from llmxive.agents.submission_intake import process_submission_issue
    # No labels → subtype is None → outcome=failed
    bad_issue = {
        "number": 42, "state": "open", "body": "",
        "user": {"login": "bob"}, "labels": [],
    }
    # Mock gh to swallow the comment call.
    gh_calls = []
    def fake_gh(*args, **kwargs):
        gh_calls.append(args)
        return (0, "", "")
    result = process_submission_issue(bad_issue, repo_root=tmp_path, gh=fake_gh)
    assert result.status == "failed"
    assert "malformed labels" in (result.error or "")
    entries = _read_run_log_lines(tmp_path)
    assert len(entries) == 1
    assert entries[0]["outcome"] == "failed"
    assert entries[0]["issue_number"] == 42
    assert entries[0]["error"] == "malformed labels"


def test_log_writer_failure_does_not_break_intake(tmp_path: Path) -> None:
    """If the log-write fails (read-only FS, etc.), intake still returns
    its IntakeResult. The Activity tab can survive a missing entry; an
    intake CRASH would lose the project."""
    from llmxive.agents import submission_intake as si
    closed_issue = {"number": 1, "state": "closed", "body": "", "user": {"login": "u"}}
    with patch.object(si, "_write_run_log_entry",
                       side_effect=OSError("read-only fs")):
        result = si.process_submission_issue(closed_issue, repo_root=tmp_path)
    assert result.status == "skipped"
    # No log written (the write raised), but the intake didn't crash.
    assert _read_run_log_lines(tmp_path) == []


def test_log_path_uses_github_run_id_when_set(tmp_path: Path, monkeypatch) -> None:
    """In CI, all per-issue entries from one workflow run land in the
    same `<RUN_ID>.jsonl` so a tailing audit can group them."""
    from llmxive.agents.submission_intake import process_submission_issue
    monkeypatch.setenv("GITHUB_RUN_ID", "12345678")
    closed_issue = {"number": 1, "state": "closed", "body": "", "user": {"login": "u"}}
    process_submission_issue(closed_issue, repo_root=tmp_path, gh=lambda *a, **k: (0, "", ""))
    # Find the single file under state/run-log/<month>/
    log_files = list((tmp_path / "state" / "run-log").rglob("*.jsonl"))
    assert len(log_files) == 1
    assert log_files[0].name == "12345678.jsonl"
