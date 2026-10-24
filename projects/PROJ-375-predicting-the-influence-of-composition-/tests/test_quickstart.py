"""
Unit test for the quick‑start pipeline (T001).

The test simply imports the ``pipeline.run`` module and executes its ``main``
function with ``--sample 5`` to keep the run fast. It asserts that:

* The script exits with status 0.
* The file ``results/sample_output.parquet`` is created.
* The resulting DataFrame contains the required descriptor columns.
"""

import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.timeout(180)
def test_quickstart_sample_run(tmp_path, monkeypatch):
    # Ensure the repository root is on PYTHONPATH (pytest does this by default)
    # Run the module with a small sample size
    result = subprocess.run(
        [sys.executable, "-m", "pipeline.run", "--sample", "5"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"

    # Verify the parquet file exists
    output_file = Path("results") / "sample_output.parquet"
    assert output_file.is_file(), "sample_output.parquet was not created"

    # Verify required columns
    import pandas as pd

    df = pd.read_parquet(output_file)
    required_cols = {
        "composition",
        "cte",
        "weighted_mean_atomic_radius",
        "electronegativity_variance",
        "vec",
        "atomic_size_coefficient_of_variation",
        "checksum",
    }
    missing = required_cols - set(df.columns)
    assert not missing, f"Missing required columns: {missing}"