import os
import json
import pytest
from pathlib import Path
import tempfile
import shutil

from verify_dataset import (
    check_bids_structure,
    check_event_markers,
    run_verification,
    VerificationError
)

@pytest.fixture
def valid_bids_dataset(tmp_path):
    """Create a minimal valid BIDS dataset structure for testing."""
    # Create dataset_description.json
    desc = {
        "Name": "TestDataset",
        "BIDSVersion": "1.8.0"
    }
    desc_file = tmp_path / "dataset_description.json"
    with open(desc_file, 'w') as f:
        json.dump(desc, f)

    # Create a subject directory with func folder and events.tsv
    sub_dir = tmp_path / "sub-01" / "func"
    sub_dir.mkdir(parents=True)

    events_file = sub_dir / "events.tsv"
    events_file.write_text("onset\tduration\ttrial_type\n0\t1\tactive\n")

    return tmp_path

@pytest.fixture
def valid_bids_landmarks_dataset(tmp_path):
    """Create a minimal valid BIDS dataset with landmarks (fallback)."""
    desc = {
        "Name": "TestDatasetLandmarks",
        "BIDSVersion": "1.8.0"
    }
    desc_file = tmp_path / "dataset_description.json"
    with open(desc_file, 'w') as f:
        json.dump(desc, f)

    sub_dir = tmp_path / "sub-01" / "func"
    sub_dir.mkdir(parents=True)

    landmarks_file = sub_dir / "landmarks.tsv"
    landmarks_file.write_text("onset\tduration\ttrial_type\n0\t1\tlandmark\n")

    return tmp_path

@pytest.fixture
def invalid_bids_dataset(tmp_path):
    """Create an invalid BIDS dataset (missing description)."""
    sub_dir = tmp_path / "sub-01" / "func"
    sub_dir.mkdir(parents=True)
    return tmp_path

@pytest.fixture
def no_events_dataset(tmp_path):
    """Create a valid BIDS dataset without event markers."""
    desc = {
        "Name": "TestDatasetNoEvents",
        "BIDSVersion": "1.8.0"
    }
    desc_file = tmp_path / "dataset_description.json"
    with open(desc_file, 'w') as f:
        json.dump(desc, f)

    sub_dir = tmp_path / "sub-01" / "func"
    sub_dir.mkdir(parents=True)

    return tmp_path

def test_check_bids_structure_valid(valid_bids_dataset):
    """Test that valid BIDS structure passes validation."""
    result = check_bids_structure(valid_bids_dataset)
    assert result is True

def test_check_bids_structure_missing_description(invalid_bids_dataset):
    """Test that missing dataset_description.json raises error."""
    with pytest.raises(VerificationError, match="Missing required BIDS file"):
        check_bids_structure(invalid_bids_dataset)

def test_check_bids_structure_no_subjects(tmp_path):
    """Test that dataset without subject directories fails."""
    desc = {"Name": "Test", "BIDSVersion": "1.8.0"}
    with open(tmp_path / "dataset_description.json", 'w') as f:
        json.dump(desc, f)
    with pytest.raises(VerificationError, match="No subject directories"):
        check_bids_structure(tmp_path)

def test_check_event_markers_with_events(valid_bids_dataset):
    """Test event marker detection with events.tsv."""
    result = check_event_markers(valid_bids_dataset)
    assert result["has_events_tsv"] is True
    assert result["has_landmarks_tsv"] is False
    assert result["valid"] is True

def test_check_event_markers_with_landmarks(valid_bids_landmarks_dataset):
    """Test event marker detection with landmarks.tsv (fallback)."""
    result = check_event_markers(valid_bids_landmarks_dataset)
    assert result["has_events_tsv"] is False
    assert result["has_landmarks_tsv"] is True
    assert result["valid"] is True

def test_check_event_markers_missing_both(no_events_dataset):
    """Test that missing both event types raises error."""
    with pytest.raises(VerificationError, match="Missing event markers"):
        check_event_markers(no_events_dataset)

def test_run_verification_full_valid(valid_bids_dataset, tmp_path):
    """Test full verification pipeline with valid dataset."""
    output_file = tmp_path / "report.json"
    result = run_verification(str(valid_bids_dataset), str(output_file))

    assert result["status"] == "passed"
    assert result["bids_valid"] is True
    assert result["events_valid"] is True
    assert output_file.exists()

    with open(output_file) as f:
        saved_report = json.load(f)
    assert saved_report["status"] == "passed"

def test_run_verification_fails_invalid(tmp_path):
    """Test full verification pipeline with invalid dataset."""
    invalid_ds = tmp_path / "invalid"
    invalid_ds.mkdir()
    desc = {"Name": "Test", "BIDSVersion": "1.8.0"}
    with open(invalid_ds / "dataset_description.json", 'w') as f:
        json.dump(desc, f)

    with pytest.raises(VerificationError, match="No subject directories"):
        run_verification(str(invalid_ds))
