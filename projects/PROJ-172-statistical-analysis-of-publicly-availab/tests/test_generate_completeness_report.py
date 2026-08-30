import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# We need to mock the data_validation module if it's not fully set up in test env
# But since T016a is marked as completed, we assume validate_data_completeness exists.
# However, to be safe and test the report generation logic specifically:

from unittest.mock import patch, MagicMock
from generate_completeness_report import generate_report, PROCESSED_DATA_PATH, REPORT_OUTPUT_PATH

@pytest.fixture
def temp_state_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir) / "state"
        state_dir.mkdir()
        # Create a mock state file with completeness stats
        state_file = state_dir / "data_state.json"
        mock_stats = {
            "completeness_rate": 0.98,
            "is_real_data": True,
            "status": "PASSED",
            "details": {"missing_columns": [], "missing_rows": 0}
        }
        with open(state_file, 'w') as f:
            json.dump({"completeness_stats": mock_stats}, f)
        
        # Temporarily change the global path
        original_state_path = Path("state/data_state.json")
        # We can't easily change the global variable inside the module without import reload
        # So we will patch the function that reads it or the path check
        yield state_dir, mock_stats

@patch('generate_completeness_report.Path')
def test_generate_report_from_state(mock_path, temp_state_dir):
    """
    Test that generate_report correctly reads from state and writes the JSON report.
    """
    state_dir, expected_stats = temp_state_dir
    
    # Setup the mock Path to return our temp directory for 'state/data_state.json'
    def path_side_effect(path_str):
        p = Path(path_str)
        if str(p) == "state/data_state.json":
            return state_dir / "data_state.json"
        if str(p) == "artifacts/reports/data_completeness_report.json":
            # Return a mock path that we can write to
            return Path(tempfile.gettempdir()) / "test_report.json"
        return p

    mock_path.side_effect = path_side_effect

    # Mock ensure_directories to do nothing
    with patch('generate_completeness_report.ensure_directories'):
        report = generate_report()

    assert report["completeness_rate"] == expected_stats["completeness_rate"]
    assert report["is_real_data"] == expected_stats["is_real_data"]
    assert report["empirical_hypothesis_untested"] is False
    assert report["status"] == "PASSED"

@patch('generate_completeness_report.Path')
@patch('generate_completeness_report.validate_data_completeness')
def test_generate_report_recalculated(mock_validate, mock_path, temp_state_dir):
    """
    Test that if state is missing/invalid, the report triggers recalculation.
    """
    # Make state file look non-existent
    def path_side_effect(path_str):
        p = Path(path_str)
        if str(p) == "state/data_state.json":
            # Return a path that doesn't exist
            return Path("/nonexistent/state.json")
        if str(p) == "artifacts/reports/data_completeness_report.json":
            return Path(tempfile.gettempdir()) / "test_report2.json"
        if str(p) == "data/processed/processed_games.csv":
            return Path(tempfile.gettempdir()) / "fake.csv"
        return p

    mock_path.side_effect = path_side_effect

    # Mock the validation function to return a specific result
    mock_result = {
        "completeness_rate": 0.92,
        "is_real_data": False,
        "empirical_hypothesis_untested": True,
        "status": "SYNTHETIC_FALLBACK"
    }
    mock_validate.return_value = mock_result

    # Ensure processed data path exists check is mocked or handled
    # The function checks if PROCESSED_DATA_PATH.exists()
    # We need to make sure the mock Path returns a path that exists() returns True for
    # But we already mocked the path creation. We need to mock the 'exists' method of the returned object.
    # Actually, the function uses global PROCESSED_DATA_PATH which is a Path object.
    # We are patching the Path constructor.
    # Let's refine the mock to handle the existence check.
    
    fake_csv_path = Path(tempfile.gettempdir()) / "fake.csv"
    fake_csv_path.touch() # Create real temp file
    
    with patch('generate_completeness_report.ensure_directories'):
        report = generate_report()

    mock_validate.assert_called_once()
    assert report["completeness_rate"] == 0.92
    assert report["empirical_hypothesis_untested"] is True
    
    # Cleanup
    if fake_csv_path.exists():
        fake_csv_path.unlink()

@patch('generate_completeness_report.Path')
@patch('generate_completeness_report.validate_data_completeness')
def test_generate_report_threshold_failure(mock_validate, mock_path):
    """
    Test that a ValueError from validate_data_completeness is caught and reported.
    """
    def path_side_effect(path_str):
        p = Path(path_str)
        if str(p) == "state/data_state.json":
            return Path("/nonexistent/state.json")
        if str(p) == "artifacts/reports/data_completeness_report.json":
            return Path(tempfile.gettempdir()) / "test_report3.json"
        if str(p) == "data/processed/processed_games.csv":
            return Path(tempfile.gettempdir()) / "fake3.csv"
        return p

    mock_path.side_effect = path_side_effect
    
    # Create the fake csv
    fake_csv = Path(tempfile.gettempdir()) / "fake3.csv"
    fake_csv.touch()

    # Mock validate to raise ValueError
    mock_validate.side_effect = ValueError("Completeness rate 0.90 is below 0.95 threshold for real data.")

    with patch('generate_completeness_report.ensure_directories'):
        report = generate_report()

    assert report["status"] == "FAILED_THRESHOLD"
    assert "error_message" in report
    assert "0.90" in report["error_message"]
    
    if fake_csv.exists():
        fake_csv.unlink()
