import pytest
from pathlib import Path
import tempfile
import os
import csv
import pandas as pd

# Mock the config to avoid dependency on real config.py during tests
import sys
from unittest.mock import patch, MagicMock

# We will test the logic without actually downloading data
# by mocking the fetch_dataset and other functions

@pytest.fixture
def mock_dataset_dir(tmp_path):
    """Create a mock dataset directory structure."""
    # Create sub-01, sub-02, sub-03
    for subj in ["01", "02", "03"]:
        subj_dir = tmp_path / f"sub-{subj}" / "func"
        subj_dir.mkdir(parents=True)
        # Create a dummy NIfTI file (we won't actually read it, just check path existence)
        nifti_file = subj_dir / f"sub-{subj}_task-rest_bold.nii.gz"
        nifti_file.touch()
    return tmp_path

@pytest.fixture
def mock_config():
    """Mock the config module."""
    with patch("data_loader.MIN_TIME_POINTS", 100), \
         patch("data_loader.FD_THRESHOLD", 0.2), \
         patch("data_loader.DATASET_ID", "ds000305"):
        yield

def test_filter_subjects_logic(mock_dataset_dir, mock_config):
    """Test that filter_subjects correctly filters based on time points and FD."""
    from data_loader import filter_subjects

    # Mock get_subject_time_points and get_mean_fd to simulate specific cases
    with patch("data_loader.get_subject_time_points") as mock_tp, \
         patch("data_loader.get_mean_fd") as mock_fd:

        # Sub-01: 150 time points, FD=0.1 -> Valid
        # Sub-02: 80 time points, FD=0.1 -> Excluded (time points)
        # Sub-03: 150 time points, FD=0.3 -> Excluded (FD)

        mock_tp.side_effect = lambda _, subj: 150 if subj in ["01", "03"] else 80
        mock_fd.side_effect = lambda _, subj: 0.1 if subj == "01" else (0.3 if subj == "03" else 0.1)

        valid, exclusions = filter_subjects(mock_dataset_dir)

        assert "01" in valid
        assert "02" not in valid
        assert "03" not in valid

        assert len(exclusions) == 2
        excl_ids = [e["subject_id"] for e in exclusions]
        assert "02" in excl_ids
        assert "03" in excl_ids

        # Check reasons
        excl_dict = {e["subject_id"]: e for e in exclusions}
        assert "Time points" in excl_dict["02"]["reason"]
        assert "Mean FD" in excl_dict["03"]["reason"]

def test_write_exclusions_log(tmp_path, mock_config):
    """Test that write_exclusions_log writes correct CSV."""
    from data_loader import write_exclusions_log

    exclusions = [
        {"subject_id": "02", "reason": "Time points < 100", "fd_mean": 0.1},
        {"subject_id": "03", "reason": "FD > 0.2", "fd_mean": 0.3},
    ]
    log_file = tmp_path / "exclusions.log"

    write_exclusions_log(exclusions, log_file)

    assert log_file.exists()
    with open(log_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["subject_id"] == "02"
    assert rows[1]["subject_id"] == "03"

def test_write_valid_subjects_csv(tmp_path, mock_config):
    """Test that write_valid_subjects_csv writes correct CSV."""
    from data_loader import write_valid_subjects_csv

    valid_subjects = ["01", "04", "05"]
    output_file = tmp_path / "valid_subjects.csv"

    write_valid_subjects_csv(valid_subjects, output_file)

    assert output_file.exists()
    df = pd.read_csv(output_file)
    assert list(df["subject_id"]) == valid_subjects

def test_calculate_sha256(tmp_path):
    """Test SHA256 calculation."""
    from data_loader import calculate_sha256

    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    checksum = calculate_sha256(test_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert checksum.isalnum()