"""
Integration test for the ``code/main.py`` entry point.

The test simply imports the ``main`` function and executes it.
After execution it asserts that the two artefacts required by
task T003 exist and contain the expected columns.

The heavy‑weight model training is performed on a 100‑sample
subset, so the test runs safely within the CI resource limits.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

# Import the entry‑point function without triggering the script's
# ``if __name__ == "__main__"`` block.
from code.main import main as run_main  # type: ignore

@pytest.mark.integration
def test_main_creates_outputs(tmp_path, monkeypatch):
    """
    Verify that ``code/main.py`` creates the required output files.
    """
    # Ensure a clean working directory inside the temporary path.
    project_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(project_root)

    # Run the pipeline.
    run_main()

    # Expected output locations.
    per_sample_path = Path(project_root) / "data" / "results" / "per_sample_errors.csv"
    log_path = Path(project_root) / "data" / "results" / "pipeline_run.json"

    # Both files must exist.
    assert per_sample_path.is_file(), f"{per_sample_path} was not created"
    assert log_path.is_file(), f"{log_path} was not created"

    # Validate the per‑sample CSV schema (a subset of columns is enough).
    df = pd.read_csv(per_sample_path)
    expected_columns = {
        "sample_id",
        "method",
        "prediction",
        "lower_bound",
        "upper_bound",
        "ground_truth",
        "dataset",
    }
    assert expected_columns.issubset(set(df.columns)), (
        f"Missing columns in per_sample_errors.csv: "
        f"{expected_columns - set(df.columns)}"
    )

    # Validate the JSON log structure.
    log_content = json.loads(log_path.read_text())
    assert "overall_status" in log_content
    assert "memory_peak_mb" in log_content
    assert "total_duration_seconds" in log_content
    assert log_content["overall_status"] == "success"  # the pipeline should finish cleanly.