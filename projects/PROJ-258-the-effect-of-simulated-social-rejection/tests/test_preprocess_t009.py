"""
Integration test for T009 – feature aggregation and outlier audit trail.
The test creates a minimal CSV with the required columns, runs the
preprocessing pipeline in file mode, and checks that:
  * data/processed/features_ds000208.csv exists and contains the expected columns.
  * data/interim/outlier_log.json exists and contains entries for each condition.
"""
import os
import json
import pandas as pd
import pytest
from pathlib import Path

# Ensure the project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from preprocess import run_preprocessing
from config import get_path

@pytest.fixture
def temp_dirs(tmp_path):
    """
    Create temporary raw, interim, and processed directories and monkeypatch
    config.get_path to point to them.
    """
    raw_dir = tmp_path / "raw"
    interim_dir = tmp_path / "interim"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    interim_dir.mkdir()
    processed_dir.mkdir()

    # Monkeypatch get_path
    def fake_get_path(key: str):
        mapping = {
            "raw": str(raw_dir),
            "interim": str(interim_dir),
            "processed": str(processed_dir)
        }
        return mapping.get(key, "")
    # Patch the function in the config module
    import config
    config.get_path = fake_get_path

    return {
        "raw": raw_dir,
        "interim": interim_dir,
        "processed": processed_dir
    }

def test_t009_feature_aggregation_and_outlier_log(temp_dirs):
    raw_dir = temp_dirs["raw"]
    processed_dir = temp_dirs["processed"]
    interim_dir = temp_dirs["interim"]

    # Create a minimal CSV that satisfies required columns
    csv_path = raw_dir / "test_dataset.csv"
    csv_path.write_text(
        "participant_id,condition,reaction_time,mood_rating\n"
        "sub-001,rejection,500,3\n"
        "sub-001,rejection,700,4\n"   # outlier (high RT)
        "sub-001,control,450,4\n"
        "sub-002,rejection,300,2\n"
        "sub-002,control,350,3\n"
    )

    # Define where the preprocessed CSV will be written
    preprocessed_csv = processed_dir / "preprocessed_test.csv"

    # Run the preprocessing pipeline (file mode)
    run_preprocessing(
        input_path=str(csv_path),
        output_path=str(preprocessed_csv),
        design_type="Within-Subjects"
    )

    # ------------------------------------------------------------------
    # Verify the aggregated features file
    # ------------------------------------------------------------------
    features_path = processed_dir / "features_ds000208.csv"
    assert features_path.is_file(), "Features file not created"

    features_df = pd.read_csv(features_path)
    # Expected columns
    expected_cols = {"participant_id", "condition", "mean_rt", "avg_mood"}
    assert expected_cols.issubset(set(features_df.columns)), "Missing expected columns in features file"

    # Spot‑check that aggregation was performed (means should be numeric)
    assert not features_df.empty, "Features dataframe is empty"

    # ------------------------------------------------------------------
    # Verify outlier audit trail
    # ------------------------------------------------------------------
    outlier_log_path = interim_dir / "outlier_log.json"
    assert outlier_log_path.is_file(), "Outlier log not created"

    with open(outlier_log_path, "r") as f:
        outlier_log = json.load(f)

    # There should be entries for both 'rejection' and 'control' conditions
    conditions_logged = {entry["condition"] for entry in outlier_log}
    assert {"rejection", "control"}.issubset(conditions_logged), "Outlier log missing expected conditions"

    # Each entry must contain required fields
    for entry in outlier_log:
        for key in ["condition", "flagged_count", "iqr_threshold", "q1", "q3", "lower_bound", "upper_bound"]:
            assert key in entry, f"Missing key '{key}' in outlier log entry"