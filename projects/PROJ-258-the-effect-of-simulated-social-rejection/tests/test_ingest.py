"""
Unit tests for the ingestion module focusing on T004.
The tests verify that the condition report is generated correctly
when the required columns are present and that the script exits
with code 1 when columns are missing.
"""

import os
import json
import sys
import subprocess
import pytest
from pathlib import Path

# Ensure the project root is in PYTHONPATH for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from ingest import process_condition_report, REJECTION_DATASET_ID, REWARD_DATASET_ID, REQUIRED_COLUMNS_T004

def test_process_condition_report_creates_file(tmp_path, monkeypatch):
    """
    Verify that process_condition_report creates the expected JSON file
    and that the fields are boolean.
    """
    # Use a temporary raw directory containing minimal valid CSVs
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True)

    # Create minimal CSVs with required columns
    for ds_id, fname in [(REJECTION_DATASET_ID, "rejection.csv"),
                         (REWARD_DATASET_ID, "reward.csv")]:
        df_path = raw_dir / fname
        # Simple data that satisfies required columns
        df_path.write_text(
            "participant_id,condition,reaction_time,mood_rating\n"
            "sub-001,rejection,500,3\n"
            "sub-001,control,450,4\n"
        )

    # Patch get_path to point to our temporary directories
    def fake_get_path(key: str):
        mapping = {
            "raw": str(raw_dir),
            "interim": str(tmp_path / "interim")
        }
        return mapping.get(key, "")

    monkeypatch.setattr("config.get_path", fake_get_path)

    # Run the function
    report = process_condition_report()

    # Verify JSON file exists and content matches
    report_path = Path(fake_get_path("interim")) / "condition_report.json"
    assert report_path.is_file()
    with open(report_path) as f:
        data = json.load(f)
    assert data == report
    assert isinstance(data["rejection_present"], bool)
    assert isinstance(data["control_present"], bool)
    assert isinstance(data["reward_present"], bool)

def test_missing_required_columns_triggers_exit(monkeypatch):
    """
    Ensure that if a required column is missing the script exits with code 1.
    """
    # Create a DataFrame missing one required column
    import pandas as pd
    df = pd.DataFrame({
        "participant_id": ["sub-001"],
        "condition": ["rejection"],
        "reaction_time": [500]
        # mood_rating column omitted
    })

    # Patch the download function to return this DataFrame directly
    def fake_download(dataset_id: str, target_csv_name: str):
        return df

    monkeypatch.setattr("ingest._download_and_save_dataset", fake_download)

    # Patch get_path to use a temporary directory for raw/interim
    tmp_raw = tmp_path / "raw"
    tmp_interim = tmp_path / "interim"
    tmp_raw.mkdir()
    tmp_interim.mkdir()
    monkeypatch.setattr("config.get_path", lambda key: str(tmp_raw) if key == "raw" else str(tmp_interim))

    # Capture sys.exit
    with pytest.raises(SystemExit) as excinfo:
        process_condition_report()
    assert excinfo.value.code == 1