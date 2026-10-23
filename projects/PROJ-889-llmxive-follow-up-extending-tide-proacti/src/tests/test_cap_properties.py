"""
test_cap_properties.py

Unit test for the ``src.data.cap_properties`` module.  The test creates a
temporary synthetic_meta CSV with a handful of rows, some of which exceed
the ``dependency_depth`` cap.  It then runs the ``enforce_caps`` function
via the module's CLI entry point and verifies:

* All ``dependency_depth`` values are ≤ 5 after execution.
* The log file contains one warning line per capped instance.
* The original CSV is overwritten with the corrected values.
"""

import csv
import os
import subprocess
import sys
from pathlib import Path
import tempfile

import pandas as pd

# Import the module to get the LOG_FILE constant for verification.
from src.data import cap_properties

def run_cap_properties(csv_path: Path) -> int:
    """Run the module as a script and return the exit code."""
    # Use the same interpreter that is running the tests.
    result = subprocess.run(
        [sys.executable, "-m", "src.data.cap_properties", str(csv_path)],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr

def test_enforce_caps(tmp_path: Path):
    # ------------------------------------------------------------------
    # Setup: create a temporary CSV with known values.
    # ------------------------------------------------------------------
    csv_path = tmp_path / "synthetic_meta.csv"
    rows = [
        {"instance_id": 0, "origin": "synthetic", "filename": "a.py", "dependency_depth": 3, "semantic_scope": "local", "syntactic_complexity": 1, "ground_truth_label": 0, "sha256": "dummy"},
        {"instance_id": 1, "origin": "synthetic", "filename": "b.py", "dependency_depth": 6, "semantic_scope": "cross_module", "syntactic_complexity": 2, "ground_truth_label": 1, "sha256": "dummy"},
        {"instance_id": 2, "origin": "synthetic", "filename": "c.py", "dependency_depth": 9, "semantic_scope": "local", "syntactic_complexity": 3, "ground_truth_label": 0, "sha256": "dummy"},
    ]
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)

    # Ensure the log file is empty before the test runs.
    log_path = cap_properties.LOG_FILE
    if log_path.is_file():
        log_path.unlink()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Execute the cap_properties script.
    # ------------------------------------------------------------------
    exit_code, stdout, stderr = run_cap_properties(csv_path)
    assert exit_code == 0, f"Script failed with rc={exit_code}, stderr={stderr}"

    # ------------------------------------------------------------------
    # Verify the CSV was overwritten with capped values.
    # ------------------------------------------------------------------
    df_after = pd.read_csv(csv_path)
    assert (df_after["dependency_depth"] <= cap_properties.MAX_DEPENDENCY_DEPTH).all()
    # Rows 1 and 2 should have been capped to 5.
    assert df_after.loc[df_after["instance_id"] == 1, "dependency_depth"].iloc[0] == 5
    assert df_after.loc[df_after["instance_id"] == 2, "dependency_depth"].iloc[0] == 5

    # ------------------------------------------------------------------
    # Verify the log contains the expected warnings.
    # ------------------------------------------------------------------
    with open(log_path, "r", encoding="utf-8") as f:
        log_contents = f.read().strip().splitlines()
    # Two warnings expected (for instance_id 1 and 2).
    assert len(log_contents) == 2
    assert "Instance 1:" in log_contents[0]
    assert "Instance 2:" in log_contents[1]
    # Each line should mention the original depth and the cap.
    assert "requested dependency_depth 6 exceeds cap" in log_contents[0]
    assert "requested dependency_depth 9 exceeds cap" in log_contents[1]

# The ``tmp_path`` fixture is provided by pytest; it creates a temporary
# directory that is automatically cleaned up after the test.