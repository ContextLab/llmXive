import pytest
import os
import csv
from pathlib import Path
from unittest.mock import patch, mock_open
import tempfile

from data.loader import Participant, validate_and_filter_subjects, filter_by_motion
from utils.logging import log_exclusion
from errors import DataMissingCreativityError

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logging tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@patch('utils.logging.get_config')
def test_validate_and_filter_missing_score_logs(mock_get_config, temp_log_dir):
    """
    Test that validate_and_filter_subjects logs 'MISSING_SCORE' for subjects
    with missing CAQ data.
    """
    mock_get_config.return_value.DATA_PATH = temp_log_dir
    
    subjects = [
        Participant(
            subject_id="sub_001",
            fmri_path="/fake/path.nii.gz",
            behavioral_data={"CAQ": 100}
        ),
        Participant(
            subject_id="sub_002",
            fmri_path="/fake/path.nii.gz",
            behavioral_data={}  # Missing CAQ
        ),
        Participant(
            subject_id="sub_003",
            fmri_path="/fake/path.nii.gz",
            behavioral_data={"CAQ": 120}
        )
    ]
    
    # Mock os.path.exists to return True for existing paths
    with patch('os.path.exists', return_value=True):
        result = validate_and_filter_subjects(subjects)
    
    assert len(result) == 2
    assert result[0].subject_id == "sub_001"
    assert result[1].subject_id == "sub_003"
    
    # Verify log file content
    log_path = os.path.join(temp_log_dir, "data_exclusion_log.txt")
    assert os.path.exists(log_path), "Log file was not created"
    
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]['subject_id'] == 'sub_002'
    assert rows[0]['reason'] == 'MISSING_SCORE'

@patch('utils.logging.get_config')
def test_filter_by_motion_high_fd_logs(mock_get_config, temp_log_dir):
    """
    Test that filter_by_motion logs 'HIGH_MOTION' for subjects exceeding FD threshold.
    """
    mock_get_config.return_value.DATA_PATH = temp_log_dir
    
    subjects = [
        Participant(
            subject_id="sub_004",
            fmri_path="/fake/path.nii.gz",
            behavioral_data={"CAQ": 100},
            motion_metrics={'mean_fd': 0.3, 'high_vol_pct': 0.1}
        ),
        Participant(
            subject_id="sub_005",
            fmri_path="/fake/path.nii.gz",
            behavioral_data={"CAQ": 100},
            motion_metrics={'mean_fd': 0.6, 'high_vol_pct': 0.1}  # High FD
        ),
        Participant(
            subject_id="sub_006",
            fmri_path="/fake/path.nii.gz",
            behavioral_data={"CAQ": 100},
            motion_metrics={'mean_fd': 0.2, 'high_vol_pct': 0.3}  # High Vol %
        )
    ]
    
    with patch('os.path.exists', return_value=True):
        result = filter_by_motion(subjects, fd_thresh=0.5, vol_thresh=0.2)
    
    assert len(result) == 1
    assert result[0].subject_id == "sub_004"
    
    log_path = os.path.join(temp_log_dir, "data_exclusion_log.txt")
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    reasons = [row['reason'] for row in rows]
    assert 'HIGH_MOTION' in reasons
    # Verify specific subjects were logged
    logged_ids = [row['subject_id'] for row in rows]
    assert 'sub_005' in logged_ids
    assert 'sub_006' in logged_ids

@patch('utils.logging.get_config')
def test_filter_by_motion_missing_metrics_logs(mock_get_config, temp_log_dir):
    """
    Test that filter_by_motion logs 'HIGH_MOTION' when motion metrics are missing.
    """
    mock_get_config.return_value.DATA_PATH = temp_log_dir
    
    subjects = [
        Participant(
            subject_id="sub_007",
            fmri_path="/fake/path.nii.gz",
            behavioral_data={"CAQ": 100},
            motion_metrics=None  # Missing metrics
        )
    ]
    
    with patch('os.path.exists', return_value=True):
        result = filter_by_motion(subjects)
    
    assert len(result) == 0
    
    log_path = os.path.join(temp_log_dir, "data_exclusion_log.txt")
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]['reason'] == 'HIGH_MOTION'
    assert rows[0]['subject_id'] == 'sub_007'
