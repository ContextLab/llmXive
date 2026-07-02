"""Integration test to ensure ``run_experiment.py`` creates the expected CSV."""
import csv
import os
from pathlib import Path

import subprocess
import sys

def test_results_full_csv_created(tmp_path: Path):
    # Build the command line – use a tiny number of games for speed
    cmd = [
        sys.executable,
        "code/run_experiment.py",
        "--agents",
        "3",
        "--games",
        "10",
        "--context",
        "full",
        "--output-dir",
        str(tmp_path / "results"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Run failed: {result.stderr}"

    csv_path = tmp_path / "results" / "results_full.csv"
    assert csv_path.is_file(), "CSV file was not created"

    # Verify header and row count
    with csv_path.open() as f:
        reader = csv.reader(f)
        rows = list(reader)
    assert rows[0] == [
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    ], "CSV header mismatch"
    # 10 games + header = 11 rows
    assert len(rows) == 11, f"Expected 11 rows, got {len(rows)}"