import pytest
import os
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.logging import log_exclusion
from data.loader import validate_and_filter_subjects, filter_by_motion
from data.loader import Participant
from errors import DataMissingCreativityError

@pytest.fixture
def temp_config(tmp_path):
    # Mock config to use temp directory for logs
    mock_config = MagicMock()
    mock_config.DATA_PATH = tmp_path
    with patch('utils.logging.get_config', return_value=mock_config):
        with patch('data.loader.get_config', return_value=mock_config):
            yield tmp_path

def test_log_exclusion_standardized_reasons(temp_config):
    """Test that log_exclusion writes the correct reason codes."""
    log_path = temp_config / "exclusion_log.csv"
    
    # Test MISSING_SCAN
    log_exclusion("MISSING_SCAN", "sub_001")
    assert log_path.exists()
    
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['reason'] == 'MISSING_SCAN'
        assert rows[0]['subject_id'] == 'sub_001'
    
    # Test MISSING_SCORE
    log_exclusion("MISSING_SCORE", "sub_002")
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[1]['reason'] == 'MISSING_SCORE'

def test_validate_and_filter_logs_missing_scan(temp_config):
    """Test that validate_and_filter_subjects logs MISSING_SCAN."""
    subjects = [
        Participant(subject_id="sub_001", fmri_path=None, behavioral_data={"caq_score": 10}),
        Participant(subject_id="sub_002", fmri_path="/fake/path.nii", behavioral_data={"caq_score": 10})
    ]
    
    # Mock os.path.exists to return False for the fake path to simulate missing file
    with patch('os.path.exists', return_value=False):
        result = validate_and_filter_subjects(subjects)
    
    log_path = temp_config / "exclusion_log.csv"
    assert log_path.exists()
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        # Both should be excluded due to missing scan (None path or non-existent file)
        reasons = [r['reason'] for r in rows]
        assert 'MISSING_SCAN' in reasons

def test_validate_and_filter_logs_missing_score(temp_config):
    """Test that validate_and_filter_subjects logs MISSING_SCORE."""
    subjects = [
        Participant(subject_id="sub_003", fmri_path="/fake/path.nii", behavioral_data={}) # No CAQ
    ]
    
    with patch('os.path.exists', return_value=True): # Pretend file exists
        result = validate_and_filter_subjects(subjects)
    
    log_path = temp_config / "exclusion_log.csv"
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        reasons = [r['reason'] for r in rows]
        assert 'MISSING_SCORE' in reasons

def test_filter_by_motion_logs_high_motion(temp_config):
    """Test that filter_by_motion logs HIGH_MOTION."""
    subjects = [
        Participant(subject_id="sub_004", fmri_path="/fake/path.nii", 
                    behavioral_data={"caq_score": 10}, 
                    motion_metrics={"fd_mean": 0.8}) # High motion
    ]
    
    result = filter_by_motion(subjects, fd_thresh=0.5)
    
    log_path = temp_config / "exclusion_log.csv"
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        reasons = [r['reason'] for r in rows]
        assert 'HIGH_MOTION' in reasons