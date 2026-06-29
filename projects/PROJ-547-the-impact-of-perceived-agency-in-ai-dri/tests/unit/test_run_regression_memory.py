"""
Unit test for the memory‑profiling wrapper around ``run_regression``.
The test creates a tiny synthetic merged dataset, runs the regression,
and asserts that:
  * a results CSV is created,
  * a memory profile JSON is created,
  * the reported peak RAM is well below the 6 GB limit.
"""
import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from analysis.run_regression import run_regression

@pytest.fixture
def synthetic_merged_csv(tmp_path: Path) -> Path:
    """Create a minimal merged dataset with a continuous outcome."""
    df = pd.DataFrame(
        {
            "user_id": [1, 2, 3, 4, 5],
            "age": [25, 34, 45, 23, 37],
            "gender": [0, 1, 0, 1, 0],  # binary encoded
            "baseline_severity": [2.1, 3.4, 1.9, 2.8, 3.0],
            "agency_score": [0.6, 0.8, 0.4, 0.7, 0.5],
            "adherence": [0.9, 0.85, 0.95, 0.80, 0.88],  # proportion outcome
        }
    )
    out_path = tmp_path / "merged.csv"
    df.to_csv(out_path, index=False)
    return out_path

def test_run_regression_memory_profiling(synthetic_merged_csv: Path, tmp_path: Path):
    results_path = tmp_path / "regression_results.csv"
    memory_profile_path = tmp_path / "memory_profile.json"

    # Execute the regression pipeline
    run_regression(
        merged_path=synthetic_merged_csv,
        results_path=results_path,
        memory_profile_path=memory_profile_path,
    )

    # --------------------------------------------------------------
    # Assertions
    # --------------------------------------------------------------
    assert results_path.is_file(), "Regression results CSV was not created."

    assert memory_profile_path.is_file(), "Memory profile JSON was not created."

    with memory_profile_path.open() as fp:
        profile = json.load(fp)

    assert "peak_ram_mb" in profile, "JSON does not contain 'peak_ram_mb' key."
    # The synthetic run should use far less than 6 GB.
    assert profile["peak_ram_mb"] < 6000, (
        f"Peak RAM reported as {profile['peak_ram_mb']} MB, which exceeds "
        "the 6 GB threshold for this test."
    )