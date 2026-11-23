"""
Basic sanity test for the aggregation script.

The test runs the ``aggregate_thresholds.py`` script on the existing
``mc_results.csv`` and ``threshold_statistical.json`` files.  It checks that
the expected output CSV exists, contains exactly 36 rows (the number of
(N, k, pattern) groups), and that the validation log reports a PASS for
every row.

The test is deliberately lightweight – it does not re‑compute the heavy
Monte‑Carlo sweep, it merely verifies that the aggregation logic can be
executed without error on the real artefacts produced by earlier tasks.
"""

import pathlib
import subprocess
import sys

import pandas as pd

from utils.config import get_project_paths

def test_aggregation_script_runs_successfully(tmp_path: pathlib.Path):
    """
    Execute the aggregation script and verify its outputs.
    """
    # Ensure we are in the project root when invoking the script.
    project_root = pathlib.Path(__file__).resolve().parents[2]
    script_path = project_root / "code" / "analysis" / "aggregate_thresholds.py"

    # Run the script as a subprocess to capture its exit code.
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify that the CSV was created and has the expected number of rows.
    paths = get_project_paths()
    csv_path = paths["processed"] / "threshold_sweep_results.csv"
    assert csv_path.is_file(), f"Missing output CSV at {csv_path}"

    df = pd.read_csv(csv_path)
    assert len(df) == 36, f"Expected 36 rows, got {len(df)}"

    # Verify that the validation log exists and contains only PASS entries.
    log_path = paths["data_logs"] / "aggregation_validation.txt"
    assert log_path.is_file(), f"Missing validation log at {log_path}"
    with open(log_path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.readlines() if ln.strip()]
    # The validator writes one line per row, each starting with "PASS".
    assert all(line.startswith("PASS") for line in lines), "Validation log contains failures"