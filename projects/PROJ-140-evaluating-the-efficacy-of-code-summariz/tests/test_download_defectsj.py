"""
Integration test for the Defects4J fetcher and stratified sampler.

This test runs the ``download_defectsj.py`` script and checks that:
  * The script exits with status code 0.
  * The output CSV exists at ``data/raw/defects4j/ground_truth.csv``.
  * The CSV contains exactly 60 rows (20 per project).
  * All required columns are present and non‑null.
  * The missing‑ground‑truth JSON file exists (it may be empty).
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

@pytest.mark.timeout(300)
def test_download_defectsj_produces_correct_outputs(tmp_path, monkeypatch):
    """
    Run the script from the project root and validate its outputs.
    """
    # Ensure we are running from the project root (the test runner does this)
    script_path = Path("code/download/download_defectsj.py")
    assert script_path.is_file(), f"Script not found at {script_path}"

    # Execute the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )
    # The script should succeed
    assert result.returncode == 0, f"Script failed with code {result.returncode}\\nSTDOUT:{result.stdout}\\nSTDERR:{result.stderr}"

    # Check CSV output
    csv_path = Path("data/raw/defects4j/ground_truth.csv")
    assert csv_path.is_file(), f"Ground truth CSV not found at {csv_path}"
    df = pd.read_csv(csv_path)

    # Expect exactly 60 rows (20 per project)
    assert len(df) == 60, f"Expected 60 rows, got {len(df)}"

    # Verify required columns exist
    required_cols = {
        "method_id",
        "project_name",
        "bug_id",
        "source_code",
        "ground_truth_line",
        "context_code",
    }
    missing_cols = required_cols - set(df.columns)
    assert not missing_cols, f"Missing required columns in CSV: {missing_cols}"

    # Ensure no null values in required columns
    assert not df[required_cols].isnull().any().any(), "Null values found in required columns"

    # Check JSON log for missing ground truth (it should exist even if empty)
    json_path = Path("data/interaction_logs/missing_ground_truth.json")
    assert json_path.is_file(), f"Missing ground truth JSON not found at {json_path}"
    # Load JSON to ensure it's valid
    import json
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "Missing ground truth JSON should be a list"