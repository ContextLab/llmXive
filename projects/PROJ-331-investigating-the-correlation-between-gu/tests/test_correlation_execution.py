"""Smoke test that the ``run_correlation_only`` script finishes without error.

The test simply executes the script as a module and checks that the expected
result file exists.  This provides concrete evidence that the correlation
stage (Task T004) produces its declared deliverable.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from llmxive_toolkit import paths

def test_correlation_script_runs():
    # Execute the script using the project's interpreter.
    result = subprocess.run(
        ["python", "-m", "code.src.pipeline.run_correlation_only"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify that the expected CSV was created.
    csv_path = paths.data("results", "taxa_correlations.csv")
    assert csv_path.is_file(), f"Missing results file: {csv_path}"

    # Basic sanity check on the CSV contents.
    import pandas as pd

    df = pd.read_csv(csv_path)
    expected_cols = {"taxon_name", "spearman_rho", "raw_p", "bh_adj_p"}
    assert set(df.columns) == expected_cols
    # All p‑values must be in [0, 1].
    assert df["raw_p"].between(0, 1).all()
    assert df["bh_adj_p"].between(0, 1).all()