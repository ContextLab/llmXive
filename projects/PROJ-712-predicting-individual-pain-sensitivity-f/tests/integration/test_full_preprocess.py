"""
Integration test for the full preprocessing pipeline (Task T008).

The test runs the preprocessing CLI on a small real subset located at
``data/raw/sample`` (the repository is expected to contain a few participants
with genuine EEG files). It then checks that:
  * ``data/processed/feature_matrix.csv`` exists,
  * the header contains exactly the 30 expected microstate feature columns
    (as defined in ``config.EXPECTED_FEATURE_COLUMNS``) plus the required
    metadata columns,
  * there are no NaN values in any of the feature columns.
"""
import os
from pathlib import Path

import pandas as pd
import pytest

# Import the constant list of expected feature names
from config import EXPECTED_FEATURE_COLUMNS

@pytest.mark.integration
def test_full_preprocess(tmp_path):
    # Define input (sample raw data) and output directories
    raw_dir = Path(__file__).resolve().parents[3] / "data" / "raw" / "sample"
    processed_dir = Path(__file__).resolve().parents[3] / "data" / "processed"

    # Ensure the output directory is empty before the run
    if processed_dir.exists():
        for f in processed_dir.iterdir():
            f.unlink()
    else:
        processed_dir.mkdir(parents=True)

    # Run the preprocessing CLI
    cmd = [
        "python",
        "-m",
        "preprocessing",
        "--data-dir",
        str(raw_dir),
        "--output-dir",
        str(processed_dir),
    ]
    # Execute the command; any non‑zero exit will fail the test
    exit_code = os.system(" ".join(cmd))
    assert exit_code == 0, f"Preprocessing script exited with code {exit_code}"

    # Verify the output CSV exists
    feature_csv = processed_dir / "feature_matrix.csv"
    assert feature_csv.is_file(), f"Expected feature matrix at {feature_csv}"

    # Load the CSV and perform checks
    df = pd.read_csv(feature_csv)

    # Required base columns
    base_cols = {"participant_id", "heat_pain_threshold", "age", "gender", "valid_eeg_minutes"}
    assert base_cols.issubset(set(df.columns)), f"Missing base columns: {base_cols - set(df.columns)}"

    # Feature columns
    feature_cols = set(EXPECTED_FEATURE_COLUMNS)
    missing_features = feature_cols - set(df.columns)
    extra_features = set(df.columns) - feature_cols - base_cols
    assert not missing_features, f"Missing expected feature columns: {missing_features}"
    assert not extra_features, f"Unexpected extra columns: {extra_features}"

    # No NaNs in any of the feature columns
    feature_data = df[list(feature_cols)]
    assert not feature_data.isna().any().any(), "NaN values found in feature columns"