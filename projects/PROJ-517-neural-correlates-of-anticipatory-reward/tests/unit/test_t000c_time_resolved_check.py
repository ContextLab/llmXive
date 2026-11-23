"""
Unit tests for T000c: Time-Resolved Analysis Check.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to mock the file system interactions for the test
# Since the script reads from state/dataset_candidates.json and writes to state/claim_status.json
# We will create a temporary directory structure for these tests.

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir) / "state"
        state_dir.mkdir()
        yield state_dir

def test_check_supported_when_verified_and_no_missing_temporal(temp_state_dir):
    """Test that check returns SUCCESS when dataset is verified and no temporal columns are missing."""
    # Arrange
    candidates = {
        "dataset_id": "ds000001",
        "url": "https://openneuro.org/datasets/ds000001",
        "verified": True,
        "missing_columns": ["some_other_column"]
    }
    candidates_file = temp_state_dir / "dataset_candidates.json"
    with open(candidates_file, 'w') as f:
        json.dump(candidates, f)

    # Mock the paths in the module
    with patch('t000c_time_resolved_check.CANDIDATES_FILE', candidates_file):
        with patch('t000c_time_resolved_check.STATE_DIR', temp_state_dir):
            with patch('t000c_time_resolved_check.CLAIM_STATUS_FILE', temp_state_dir / "claim_status.json"):
                # Act
                from t000c_time_resolved_check import run_check
                run_check()
                
                # Assert
                claim_file = temp_state_dir / "claim_status.json"
                assert claim_file.exists()
                with open(claim_file, 'r') as f:
                    status_data = json.load(f)
                assert status_data["status"] == "SUCCESS"
                assert "Temporal columns" in status_data["reason"]

def test_check_limited_when_missing_temporal_columns(temp_state_dir):
    """Test that check returns LIMITED when temporal columns are missing."""
    # Arrange
    candidates = {
        "dataset_id": "ds000002",
        "url": "https://openneuro.org/datasets/ds000002",
        "verified": True,
        "missing_columns": ["spike_timestamps", "cue_timestamps"]
    }
    candidates_file = temp_state_dir / "dataset_candidates.json"
    with open(candidates_file, 'w') as f:
        json.dump(candidates, f)

    with patch('t000c_time_resolved_check.CANDIDATES_FILE', candidates_file):
        with patch('t000c_time_resolved_check.STATE_DIR', temp_state_dir):
            with patch('t000c_time_resolved_check.CLAIM_STATUS_FILE', temp_state_dir / "claim_status.json"):
                # Act
                from t000c_time_resolved_check import run_check
                run_check()
                
                # Assert
                claim_file = temp_state_dir / "claim_status.json"
                assert claim_file.exists()
                with open(claim_file, 'r') as f:
                    status_data = json.load(f)
                assert status_data["status"] == "LIMITED"
                assert "Missing temporal columns" in status_data["reason"]

def test_check_limited_when_not_verified(temp_state_dir):
    """Test that check returns LIMITED when dataset is not verified."""
    # Arrange
    candidates = {
        "dataset_id": "ds000003",
        "url": "https://openneuro.org/datasets/ds000003",
        "verified": False,
        "missing_columns": []
    }
    candidates_file = temp_state_dir / "dataset_candidates.json"
    with open(candidates_file, 'w') as f:
        json.dump(candidates, f)

    with patch('t000c_time_resolved_check.CANDIDATES_FILE', candidates_file):
        with patch('t000c_time_resolved_check.STATE_DIR', temp_state_dir):
            with patch('t000c_time_resolved_check.CLAIM_STATUS_FILE', temp_state_dir / "claim_status.json"):
                # Act
                from t000c_time_resolved_check import run_check
                run_check()
                
                # Assert
                claim_file = temp_state_dir / "claim_status.json"
                assert claim_file.exists()
                with open(claim_file, 'r') as f:
                    status_data = json.load(f)
                assert status_data["status"] == "LIMITED"
                assert "Dataset not verified" in status_data["reason"]

def test_check_limited_when_candidates_missing(temp_state_dir):
    """Test that check returns LIMITED when candidates file is missing."""
    # Arrange: No candidates file created
    
    with patch('t000c_time_resolved_check.CANDIDATES_FILE', temp_state_dir / "dataset_candidates.json"):
        with patch('t000c_time_resolved_check.STATE_DIR', temp_state_dir):
            with patch('t000c_time_resolved_check.CLAIM_STATUS_FILE', temp_state_dir / "claim_status.json"):
                # Act
                from t000c_time_resolved_check import run_check
                run_check()
                
                # Assert
                claim_file = temp_state_dir / "claim_status.json"
                assert claim_file.exists()
                with open(claim_file, 'r') as f:
                    status_data = json.load(f)
                assert status_data["status"] == "LIMITED"
                assert "Dataset candidates file missing" in status_data["reason"]
