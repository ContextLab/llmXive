"""
Test for the sample pipeline execution.

This test runs the `run_pipeline.py` script with the `--sample` argument,
verifies that it exits with a zero return code, and checks that the
expected CSV file `data/results/sample_run.csv` is created with the
required columns: id, subreddit, created_utc, body.
"""

import subprocess
import sys
from pathlib import Path
import csv

import pytest

# Path to the pipeline script relative to the project root
PIPELINE_SCRIPT = Path(__file__).resolve().parents[2] / "code" / "analysis" / "run_pipeline.py"

@pytest.mark.timeout(300)
def test_sample_pipeline_creates_csv(tmp_path, monkeypatch):
    """
    Run the pipeline with a small sample size and verify output.
    """
    # Ensure we run from the project root so relative paths resolve correctly
    project_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(project_root)

    # Define the sample size
    sample_size = 5

    # Execute the pipeline script
    result = subprocess.run(
        [sys.executable, str(PIPELINE_SCRIPT), f"--sample={sample_size}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Check that the script exited successfully
    assert result.returncode == 0, f"Pipeline exited with non-zero code {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"

    # Path to the expected CSV file
    csv_path = project_root / "data" / "results" / "sample_run.csv"

    # Verify the CSV file exists
    assert csv_path.is_file(), f"Expected CSV file not found at {csv_path}"

    # Verify the CSV has the required columns
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        expected_fields = {"id", "subreddit", "created_utc", "body"}
        actual_fields = set(reader.fieldnames or [])
        missing = expected_fields - actual_fields
        assert not missing, f"CSV is missing required columns: {missing}"
        
    # Optionally, verify that we have at least the requested number of rows (excluding header)
    row_count = sum(1 for _ in reader)
    assert row_count >= sample_size, f"CSV contains {row_count} rows, expected at least {sample_size}"