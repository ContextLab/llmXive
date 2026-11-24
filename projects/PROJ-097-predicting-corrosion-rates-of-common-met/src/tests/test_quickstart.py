"""Test that the quickstart commands actually run successfully.

The project’s quickstart documentation specifies two commands:
1. `python -m src.pipeline.run_all` – runs the full pipeline end‑to‑end.
2. `pytest src/tests/` – runs the test suite.

This test executes the first command via a subprocess and asserts a
zero exit status, providing concrete evidence that the quickstart
workflow works on real data.
"""

import subprocess
import sys
from pathlib import Path

def test_quickstart_run_all():
    """Execute the pipeline using the quickstart command and verify success."""
    # Use the same Python interpreter that runs the tests.
    result = subprocess.run(
        [sys.executable, "-m", "src.pipeline.run_all"],
        capture_output=True,
        text=True,
        timeout=300,  # generous but well within the 5‑minute limit for the test.
    )
    assert result.returncode == 0, (
        f"Quickstart pipeline failed (exit code {result.returncode}). "
        f"Stderr:\n{result.stderr}"
    )
    # Basic sanity check: ensure key output files were created.
    expected_files = [
        Path("data/processed/cleaned_dataset.csv"),
        Path("data/processed/features.parquet"),
        Path("data/results/vif_diagnostics.json"),
        Path("data/results/first_run_metrics.json"),
    ]
    missing = [str(p) for p in expected_files if not p.is_file()]
    assert not missing, f"Quickstart missing expected output files: {missing}"