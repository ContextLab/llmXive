"""
Unit tests for the Data Quality Report generation logic.
"""
import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions we are testing
from code.utils.logging_init import setup_global_logger
from code.utils.logging_config import load_logging_config

# We need to import the logic from the script.
# Since the script is in code/02_data_quality_report.py, we import it.
# Note: In a real test runner, we might need to adjust sys.path.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code import code_02_data_quality_report as dq_module

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create subdirectories
        (tmp_path / "output").mkdir()
        (tmp_path / "data" / "derived").mkdir(parents=True)
        (tmp_path / "state").mkdir()
        yield tmp_path

@pytest.fixture
def mock_exclusion_log(temp_dirs):
    """Create a mock exclusion log file."""
    log_path = temp_dirs / "output" / "exclusion_log.txt"
    data = [
        {"participant_id": "P001", "reason": "Data Loss > 20%"},
        {"participant_id": "P002", "reason": "Data Loss > 20%"},
        {"participant_id": "P003", "reason": "Missing ROI"},
    ]
    with open(log_path, "w") as f:
        for record in data:
            f.write(json.dumps(record) + "\n")
    return log_path

@pytest.fixture
def mock_preprocessed_gaze(temp_dirs):
    """Create a mock preprocessed gaze CSV."""
    csv_path = temp_dirs / "data" / "derived" / "preprocessed_gaze.csv"
    data = {
        "participant_id": ["P004", "P004", "P005", "P005", "P006"],
        "headline_id": ["H1", "H2", "H1", "H2", "H1"],
        "fixation_duration": [100, 150, 200, 120, 180],
        "roi": ["headline_body", "source_attribution", "headline_body", "headline_body", "headline_body"]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def mock_hash_registry(temp_dirs):
    """Create a mock hash registry."""
    hash_path = temp_dirs / "state" / "data_hashes.json"
    data = {
        "file": "eye_tracking_raw.parquet",
        "sha256": "abc123...",
        "participant_count": 10
    }
    with open(hash_path, "w") as f:
        json.dump(data, f)
    return hash_path

def test_load_exclusion_log(mock_exclusion_log):
    """Test loading the exclusion log."""
    records = dq_module.load_exclusion_log(mock_exclusion_log)
    assert len(records) == 3
    assert records[0]["participant_id"] == "P001"
    assert records[0]["reason"] == "Data Loss > 20%"

def test_load_preprocessed_gaze(mock_preprocessed_gaze):
    """Test loading the preprocessed gaze data."""
    df = dq_module.load_preprocessed_gaze(mock_preprocessed_gaze)
    assert len(df) == 5
    assert "participant_id" in df.columns

def test_generate_quality_report(mock_exclusion_log, mock_preprocessed_gaze, mock_hash_registry):
    """Test the core report generation logic."""
    exclusion_records = dq_module.load_exclusion_log(mock_exclusion_log)
    preprocessed_df = dq_module.load_preprocessed_gaze(mock_preprocessed_gaze)
    hash_registry = dq_module.load_hash_registry(mock_hash_registry)

    report_df = dq_module.generate_quality_report(exclusion_records, preprocessed_df, hash_registry)

    # Check basic metrics
    assert "metric" in report_df.columns
    assert "value" in report_df.columns

    # Check specific values
    total_row = report_df[report_df["metric"] == "total_participants_raw"]
    assert not total_row.empty
    assert total_row.iloc[0]["value"] == 10

    excluded_row = report_df[report_df["metric"] == "excluded_participants"]
    assert not excluded_row.empty
    assert excluded_row.iloc[0]["value"] == 3

    retained_row = report_df[report_df["metric"] == "retained_participants"]
    assert not retained_row.empty
    assert retained_row.iloc[0]["value"] == 7

    # Check reason breakdown
    reason_rows = report_df[report_df["metric"].str.contains("exclusion_reason")]
    assert len(reason_rows) == 2  # Two unique reasons: "Data Loss > 20%" and "Missing ROI"

def test_write_report(mock_exclusion_log, mock_preprocessed_gaze, mock_hash_registry, temp_dirs):
    """Test writing the report to CSV."""
    exclusion_records = dq_module.load_exclusion_log(mock_exclusion_log)
    preprocessed_df = dq_module.load_preprocessed_gaze(mock_preprocessed_gaze)
    hash_registry = dq_module.load_hash_registry(mock_hash_registry)

    report_df = dq_module.generate_quality_report(exclusion_records, preprocessed_df, hash_registry)
    output_path = temp_dirs / "output" / "data_quality_report.csv"

    dq_module.write_report(report_df, output_path)

    assert output_path.exists()
    written_df = pd.read_csv(output_path)
    assert len(written_df) == len(report_df)
