"""Append-only JSON Lines run-log writer (T014).

One line per agent invocation under
state/run-log/<YYYY-MM>/<run-id>.jsonl. Schema-validation failures raise
and the failed entry is parked under .invalid/<entry_id>.json for
postmortem (FIX C7 — guarantees SC-003 100% compliance).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import ValidationError

from llmxive.contract_validate import validate
from llmxive.types import RunLogEntry


def _state_root() -> Path:
    """The repo's state/ directory.

    Resolved relative to this file (src/llmxive/state/runlog.py → repo/state).
    """
    return Path(__file__).resolve().parent.parent.parent.parent / "state"


def append_entry(entry: RunLogEntry, *, repo_root: Path | None = None) -> Path:
    """Append `entry` to its month's run-log file. Returns the file path.

    Raises ValidationError if the entry's JSON form fails contract validation.
    """
    state_dir = (repo_root / "state") if repo_root else _state_root()
    month = entry.started_at.astimezone(timezone.utc).strftime("%Y-%m")
    log_dir = state_dir / "run-log" / month
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{entry.run_id}.jsonl"

    payload = entry.model_dump(mode="json")
    try:
        validate("run-log-entry", payload)
    except ValidationError:
        invalid_dir = log_dir / ".invalid"
        invalid_dir.mkdir(exist_ok=True)
        (invalid_dir / f"{entry.entry_id}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )
        raise

    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")
    return log_file


def read_entries(run_id: str, *, repo_root: Path | None = None) -> list[RunLogEntry]:
    """Read every entry written for a given run_id, in append order."""
    state_dir = (repo_root / "state") if repo_root else _state_root()
    log_root = state_dir / "run-log"
    if not log_root.is_dir():
        return []
    entries: list[RunLogEntry] = []
    for month_dir in sorted(log_root.iterdir()):
        if not month_dir.is_dir() or month_dir.name.startswith("."):
            continue
        candidate = month_dir / f"{run_id}.jsonl"
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entries.append(RunLogEntry.model_validate_json(line))
    return entries


def latest_for_project(project_id: str, *, repo_root: Path | None = None) -> RunLogEntry | None:
    """Return the most recent entry for a project, scanning all months."""
    state_dir = (repo_root / "state") if repo_root else _state_root()
    log_root = state_dir / "run-log"
    if not log_root.is_dir():
        return None
    latest: RunLogEntry | None = None
    for month_dir in sorted(log_root.iterdir(), reverse=True):
        if not month_dir.is_dir() or month_dir.name.startswith("."):
            continue
        for jsonl in sorted(month_dir.glob("*.jsonl"), reverse=True):
            for line in reversed(jsonl.read_text(encoding="utf-8").splitlines()):
                if not line.strip():
                    continue
                entry = RunLogEntry.model_validate_json(line)
                if entry.project_id == project_id:
                    if latest is None or entry.ended_at > latest.ended_at:
                        latest = entry
                    break  # done with this file
            if latest is not None:
                return latest
    return latest


def now_utc() -> datetime:
    """UTC-aware current time helper used across run-log writers."""
    return datetime.now(timezone.utc)


__all__ = ["append_entry", "read_entries", "latest_for_project", "now_utc"]
