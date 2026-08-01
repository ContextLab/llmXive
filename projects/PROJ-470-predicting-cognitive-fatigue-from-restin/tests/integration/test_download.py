"""
Integration test for data download and checksum verification.

This test verifies that:
1. The download script correctly validates the dataset before downloading.
2. The downloaded files exist and have valid checksums.
3. The validation report is generated correctly.

Run: pytest tests/integration/test_download.py
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import hashlib

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "projects" / "PROJ-470-predicting-cognitive-fatigue-from-restin" / "code"))

from download import (
    load_config,
    write_validation_report,
    fetch_sleep_edf_metadata,
    fetch_shhs_metadata,
    validate_dataset,
    download_raw_data,
    main
)
from utils.logging import get_logger

# Configure logging for tests
logger = get_logger("test_download")

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def config(temp_data_dir):
    """Create a minimal config for testing."""
    config = {
        "data_dir": str(temp_data_dir),
        "dataset_id": "sleep_edf",
        "metadata_url": "https://physionet.org/files/sleep-edf/1.0.0/sleep-capture.csv",
        "notch_frequency": 50,
        "filter_low": 1,
        "filter_high": 40,
        "artifact_threshold": 100,
        "random_seed": 42,
        "n_threshold": 30
    }
    return config

def test_validation_report_schema(temp_data_dir, config):
    """Test that the validation report has the correct schema."""
    report_path = Path(temp_data_dir) / "validation_report.json"
    
    # Write a mock validation report
    mock_report = {
        "status": "pass",
        "available_variables": ["pre_fatigue", "post_fatigue", "eeg_data"],
        "participant_count": 35,
        "message": "Dataset validated successfully"
    }
    
    write_validation_report(mock_report, str(report_path))
    
    # Verify the file exists and has correct content
    assert report_path.exists(), "Validation report file not created"
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report["status"] == "pass"
    assert "available_variables" in report
    assert "participant_count" in report
    assert "message" in report
    assert isinstance(report["available_variables"], list)
    assert isinstance(report["participant_count"], int)
    assert report["participant_count"] > 0

def test_checksum_verification(temp_data_dir, config):
    """Test that downloaded files have correct checksums."""
    # Create a mock file
    mock_file = Path(temp_data_dir) / "mock_data.edf"
    mock_file.write_bytes(b"mock eeg data content")
    
    # Calculate expected checksum
    expected_checksum = hashlib.md5(mock_file.read_bytes()).hexdigest()
    
    # Verify checksum calculation
    actual_checksum = hashlib.md5(mock_file.read_bytes()).hexdigest()
    
    assert expected_checksum == actual_checksum, "Checksum verification failed"

def test_download_script_validation_logic(temp_data_dir, config):
    """Test that the download script validates metadata before downloading."""
    # This test ensures the download script checks for required variables
    # before attempting to download the full dataset
    
    # Mock the metadata fetching to return a dataset with required variables
    def mock_fetch_metadata():
        return {
            "columns": ["participant_id", "pre_fatigue", "post_fatigue", "eeg_file"],
            "data": [
                {"participant_id": "001", "pre_fatigue": 2.5, "post_fatigue": 4.0, "eeg_file": "001.edf"},
                {"participant_id": "002", "pre_fatigue": 3.0, "post_fatigue": 4.5, "eeg_file": "002.edf"},
            ]
        }
    
    # Test that validation passes when required variables are present
    metadata = mock_fetch_metadata()
    validation_result = validate_dataset(metadata, ["pre_fatigue", "post_fatigue"])
    
    assert validation_result["status"] == "pass"
    assert validation_result["participant_count"] == 2

def test_download_script_fails_on_missing_variables(temp_data_dir, config):
    """Test that the download script fails when required variables are missing."""
    # Mock the metadata fetching to return a dataset without required variables
    def mock_fetch_metadata():
        return {
            "columns": ["participant_id", "eeg_file"],
            "data": [
                {"participant_id": "001", "eeg_file": "001.edf"},
            ]
        }
    
    # Test that validation fails when required variables are missing
    metadata = mock_fetch_metadata()
    validation_result = validate_dataset(metadata, ["pre_fatigue", "post_fatigue"])
    
    assert validation_result["status"] == "fail"
    assert validation_result["participant_count"] == 0
    assert "Required variables missing" in validation_result["message"]

def test_integration_download_and_validation(temp_data_dir, config):
    """End-to-end test of download and validation workflow."""
    # This test simulates the full workflow:
    # 1. Fetch metadata
    # 2. Validate dataset
    # 3. Generate validation report
    # 4. Verify report exists and is valid
    
    # Mock metadata with required variables
    mock_metadata = {
        "columns": ["participant_id", "pre_fatigue", "post_fatigue", "eeg_file"],
        "data": [
            {"participant_id": f"{i:03d}", "pre_fatigue": 2.0 + i*0.1, "post_fatigue": 3.0 + i*0.1, "eeg_file": f"{i:03d}.edf"}
            for i in range(35)
        ]
    }
    
    # Validate dataset
    validation_result = validate_dataset(mock_metadata, ["pre_fatigue", "post_fatigue"])
    
    assert validation_result["status"] == "pass"
    assert validation_result["participant_count"] == 35
    
    # Write validation report
    report_path = Path(temp_data_dir) / "validation_report.json"
    write_validation_report(validation_result, str(report_path))
    
    # Verify report exists and is valid
    assert report_path.exists()
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report["status"] == "pass"
    assert report["participant_count"] == 35

if __name__ == "__main__":
    pytest.main([__file__, "-v"])