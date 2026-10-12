import subprocess
import sys
import os
from pathlib import Path

import pandas as pd

def test_sample_run_creates_csv(tmp_path, monkeypatch):
    """
    Verify that the ``--sample`` command runs without error and creates the expected CSV.
    """
    # Ensure we are in the project root
    project_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(project_root)

    # Run the sample pipeline
    result = subprocess.run(
        [sys.executable, "-m", "code.analysis.run_pipeline", "--sample", "5"],
        capture_output=True,
        text=True,
    )

    # The command should exit with code 0
    assert result.returncode == 0, f"Process failed: {result.stderr}"

    # Expected output path
    csv_path = project_root / "data" / "results" / "sample_run.csv"
    assert csv_path.is_file(), f"Sample CSV not found at {csv_path}"

    # Load the CSV and check required columns
    df = pd.read_csv(csv_path)
    expected_columns = {"id", "subreddit", "created_utc", "body"}
    assert expected_columns.issubset(set(df.columns)), "Missing required columns in sample CSV"

    # Ensure we have at most the requested number of rows (could be fewer if dataset is tiny)
    assert len(df) <= 5, "Sample CSV contains more rows than requested"