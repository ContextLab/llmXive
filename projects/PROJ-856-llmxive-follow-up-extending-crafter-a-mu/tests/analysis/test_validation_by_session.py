import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

from src.analysis.validation_by_session import main

# Lightweight local schema for the aggregated per-session view.
AGGREGATED_SCHEMA = {
    "type": "object",
    "required": ["session_id", "task_id", "overall_success"],
    "properties": {
        "session_id": {"type": "string", "minLength": 1},
        "task_id": {"type": "string", "minLength": 1},
        "interface": {"type": "string"},
        "vector_match": {"type": "boolean"},
        "semantic_pass": {"type": "boolean"},
        "overall_success": {"type": "boolean"},
    },
    "additionalProperties": False,
}

SUMMARY_SCHEMA = {
    "type": "object",
    "required": ["session_id", "tasks_attempted", "successes", "success_rate"],
    "properties": {
        "session_id": {"type": "string", "minLength": 1},
        "tasks_attempted": {"type": "integer", "minimum": 0},
        "successes": {"type": "integer", "minimum": 0},
        "success_rate": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "additionalProperties": False,
}


def _write_jsonl(path: Path, records):
    with path.open("w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


def _read_jsonl(path: Path):
    with path.open("r") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_validation_by_session_mapping(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    val_dir = tmp_path / "validation"
    gt_dir = tmp_path / "gt"
    log_dir.mkdir()
    val_dir.mkdir()
    gt_dir.mkdir()
    out_path = tmp_path / "results_session.jsonl"
    sum_path = tmp_path / "summary.jsonl"

    # Interaction log uses "figure_N" naming (as produced by the logger)
    # and different participants edit different figures.
    interactions = [
        {"participant_id": "user_A", "figure_id": "figure_0", "interface": "structured", "iteration": 1},
        {"participant_id": "user_A", "figure_id": "figure_0", "interface": "structured", "iteration": 2},
        {"participant_id": "user_B", "figure_id": "figure_1", "interface": "chat", "iteration": 1},
    ]
    _write_jsonl(log_dir / "interactions_clean.jsonl", interactions)

    # Validation records use bare numeric task ids.
    validations = [
        {"task_id": "0", "vector_match": True, "semantic_pass": False},
        {"task_id": "1", "vector_match": False, "semantic_pass": False},
    ]
    _write_jsonl(val_dir / "semantic_validation.jsonl", validations)

    def mock_run(*args, **kwargs):
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""
        return Result()
    monkeypatch.setattr(subprocess, "run", mock_run)

    monkeypatch.setattr(sys, "argv", [
        "validation_by_session.py",
        "--log-dir", str(log_dir),
        "--validation-dir", str(val_dir),
        "--ground-truth-dir", str(gt_dir),
        "--output-path", str(out_path),
        "--summary-path", str(sum_path),
    ])

    assert main() == 0

    results = _read_jsonl(out_path)
    assert len(results) == 2
    res_0 = next(r for r in results if r["task_id"] == "0")
    assert res_0["session_id"] == "user_A"
    assert res_0["overall_success"] is True
    assert res_0["interface"] == "structured"

    res_1 = next(r for r in results if r["task_id"] == "1")
    assert res_1["session_id"] == "user_B"
    assert res_1["overall_success"] is False

    for rec in results:
        jsonschema.validate(rec, AGGREGATED_SCHEMA)

    summary = {r["session_id"]: r for r in _read_jsonl(sum_path)}
    assert summary["user_A"]["successes"] == 1
    assert summary["user_A"]["tasks_attempted"] == 1
    assert summary["user_B"]["successes"] == 0
    for rec in summary.values():
        jsonschema.validate(rec, SUMMARY_SCHEMA)

def test_fails_loudly_when_no_mapping(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    val_dir = tmp_path / "validation"
    gt_dir = tmp_path / "gt"
    log_dir.mkdir()
    val_dir.mkdir()
    gt_dir.mkdir()
    out_path = tmp_path / "results_session.jsonl"

    # Interaction log uses keys that cannot yield a session id.
    _write_jsonl(log_dir / "interactions_clean.jsonl", [
        {"something": "else", "figure_id": "figure_0"},
    ])
    _write_jsonl(val_dir / "semantic_validation.jsonl", [
        {"task_id": "0", "vector_match": True, "semantic_pass": True},
    ])

    def mock_run(*args, **kwargs):
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""
        return Result()
    monkeypatch.setattr(subprocess, "run", mock_run)

    monkeypatch.setattr(sys, "argv", [
        "validation_by_session.py",
        "--log-dir", str(log_dir),
        "--validation-dir", str(val_dir),
        "--ground-truth-dir", str(gt_dir),
        "--output-path", str(out_path),
        "--summary-path", str(tmp_path / "summary.jsonl"),
    ])

    assert main() == 1
    # No placeholder "unknown" output should have been written.
    assert not out_path.exists()