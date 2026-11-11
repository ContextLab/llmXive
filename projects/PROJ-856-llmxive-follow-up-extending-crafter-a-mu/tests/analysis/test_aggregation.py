"""
test_aggregation.py
-------------------

Integration test for ``src.analysis.aggregate_validation``.  The test
executes the aggregation script (which writes the effective‑N file) and
then validates the contents of both JSON‑Lines artifacts.

Expectations:
  * Every record in ``semantic_validation_by_session.jsonl`` contains
    the keys ``session_id``, ``task_id`` and ``overall_success``.
  * The generated ``effective_N_by_participant.jsonl`` contains one line
    per distinct ``session_id`` and the ``effective_N`` value is an
    integer ≥ 1.
"""

import json
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def _run_aggregation_script() -> None:
    """Run the aggregation module as a subprocess."""
    result = subprocess.run(
        [sys.executable, "-m", "src.analysis.aggregate_validation"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Aggregation script failed: {result.stderr}"
    # The script prints a summary line; we do not assert its exact wording
    # but ensure something was printed.
    assert result.stdout.strip(), "No output from aggregation script"

def test_aggregation_outputs() -> None:
    # Ensure the script runs successfully
    _run_aggregation_script()

    # Paths to the two result files
    results_dir = paths.data("results")
    validation_path = results_dir / "semantic_validation_by_session.jsonl"
    effective_n_path = results_dir / "effective_N_by_participant.jsonl"

    # 1. Verify the validation file exists and has required fields
    assert validation_path.is_file(), f"{validation_path} does not exist"
    sessions_seen = set()
    valid_task_counter = 0

    with validation_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            for key in ("session_id", "task_id", "overall_success"):
                assert key in record, f"Missing key '{key}' in line {line_no}"
            sessions_seen.add(record["session_id"])
            if record.get("overall_success"):
                valid_task_counter += 1

    assert sessions_seen, "No participant sessions found in validation file"

    # 2. Verify the effective_N file
    assert effective_n_path.is_file(), f"{effective_n_path} does not exist"
    with effective_n_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            assert "session_id" in rec, f"Missing 'session_id' in effective_N line {line_no}"
            assert "effective_N" in rec, f"Missing 'effective_N' in line {line_no}"
            # effective_N must be an integer ≥ 1
            effective_n = rec["effective_N"]
            assert isinstance(effective_n, int), f"effective_N not int in line {line_no}"
            assert effective_n >= 1, f"effective_N < 1 for session {rec['session_id']}"

    # Cross‑check: the number of lines in effective_N should equal the number
    # of distinct sessions seen in the validation file.
    with effective_n_path.open("r", encoding="utf-8") as f:
        effective_n_sessions = {json.loads(l)["session_id"] for l in f if l.strip()}
    assert effective_n_sessions == sessions_seen, (
        "Mismatch between sessions in validation file and effective_N file"
    )