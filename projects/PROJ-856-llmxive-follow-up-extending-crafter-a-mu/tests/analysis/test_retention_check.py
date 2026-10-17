"""
Unit test for the retention‑check script.

The test creates a temporary validation file with a configurable number of
distinct session identifiers that each contain a single successful record.
It then invokes the script via its ``main`` function and checks the exit code
and printed output.

Scenarios covered:
1. Sufficient successful sessions → exit code 0.
2. Insufficient successful sessions → exit code 1 and warning message.
"""

import json
import sys
from pathlib import Path

import pytest

# Import the function under test
from src.analysis.retention_check import main as retention_main

@pytest.fixture
def validation_file(tmp_path: Path):
    """Create a temporary ``semantic_validation.jsonl`` file."""
    return tmp_path / "semantic_validation.jsonl"

def _write_success_records(file_path: Path, num_sessions: int):
    """
    Write ``num_sessions`` distinct successful validation records.
    Each record includes a ``session_id`` field and both success flags set to True.
    """
    with file_path.open("w", encoding="utf-8") as f:
        for i in range(num_sessions):
            record = {
                "session_id": f"session_{i}",
                "figure_id": f"fig_{i}",
                "vector_match": True,
                "semantic_pass": True,
            }
            f.write(json.dumps(record) + "\n")

def test_retention_threshold_met(tmp_path: Path, capsys):
    """
    When the number of successful sessions meets the threshold, the script
    should exit with status 0 and print a success message.
    """
    validation_path = tmp_path / "semantic_validation.jsonl"
    _write_success_records(validation_path, num_sessions=30)

    # Mimic the quick‑start layout: logs are in ``tmp_path / "logs"``
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    # The script determines the validation file relative to the logs directory.
    # We'll create the expected sibling ``validation`` directory.
    (tmp_path / "validation").mkdir()
    (tmp_path / "validation" / "semantic_validation.jsonl").write_text(
        validation_path.read_text()
    )

    exit_code = retention_main()
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Retention threshold met" in captured.out

def test_retention_threshold_not_met(tmp_path: Path, capsys):
    """
    When fewer than the required number of sessions have a successful trial,
    the script should exit with status 1 and print the warning.
    """
    # Write only 24 successful sessions (threshold is 25 by default)
    validation_path = tmp_path / "semantic_validation.jsonl"
    _write_success_records(validation_path, num_sessions=24)

    # Set up the directory structure expected by the script
    (tmp_path / "validation").mkdir()
    (tmp_path / "validation" / "semantic_validation.jsonl").write_text(
        validation_path.read_text()
    )
    (tmp_path / "logs").mkdir()

    exit_code = retention_main()
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Retention threshold not met" in captured.err