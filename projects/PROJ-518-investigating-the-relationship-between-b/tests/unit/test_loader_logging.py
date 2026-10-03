import pytest
import os
import tempfile
from pathlib import Path
import csv

# Mock the config to ensure we can run tests without full setup
import sys
from unittest.mock import patch, MagicMock

from data.loader import Participant, validate_and_filter_subjects, filter_by_motion
from utils.logging import log_exclusion

@pytest.fixture
def temp_log_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock config that points to this temp dir
        mock_config = MagicMock()
        mock_config.DATA_PATH = tmpdir
        mock_config.ATLAS_PATH = os.path.join(tmpdir, "atlas.nii")
        
        # Patch the get_config function in the loader module
        with patch('data.loader.get_config', return_value=mock_config):
            with patch('utils.logging.get_config', return_value=mock_config):
                yield tmpdir

def test_validate_and_filter_logs_missing_scan(temp_log_dir):
    """Test that MISSING_SCAN is logged for subjects with no FMRI path."""
    subjects = [
        Participant(subject_id="sub_001", fmri_path=None, behavioral_data={"caq": 10}),
        Participant(subject_id="sub_002", fmri_path="/fake/path.nii", behavioral_data={"caq": 12}),
    ]
    
    # Create a dummy file for sub_002 to make it exist
    Path(temp_log_dir).mkdir(parents=True, exist_ok=True)
    fake_fmri = Path(temp_log_dir) / "fake_path.nii"
    fake_fmri.touch()
    subjects[1].fmri_path = str(fake_fmri)

    result = validate_and_filter_subjects(subjects)
    
    # sub_001 should be excluded
    assert len(result) == 1
    assert result[0].subject_id == "sub_002"
    
    # Check log file
    log_path = os.path.join(temp_log_dir, "data_exclusion_log.txt")
    assert os.path.exists(log_path)
    
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['reason'] == 'MISSING_SCAN'
        assert rows[0]['subject_id'] == 'sub_001'

def test_validate_and_filter_logs_missing_score(temp_log_dir):
    """Test that MISSING_SCORE is logged for subjects with no behavioral data."""
    subjects = [
        Participant(subject_id="sub_003", fmri_path=str(Path(temp_log_dir) / "fake.nii"), behavioral_data=None),
        Participant(subject_id="sub_004", fmri_path=str(Path(temp_log_dir) / "fake.nii"), behavioral_data={"caq": 15}),
    ]
    
    # Ensure fake.nii exists
    Path(temp_log_dir).mkdir(parents=True, exist_ok=True)
    (Path(temp_log_dir) / "fake.nii").touch()

    result = validate_and_filter_subjects(subjects)
    
    assert len(result) == 1
    assert result[0].subject_id == "sub_004"
    
    log_path = os.path.join(temp_log_dir, "data_exclusion_log.txt")
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        # Should have entries for sub_001 (from previous test if running sequentially in same dir) 
        # and sub_003. Since we use a fresh temp dir per test, only sub_003 is here.
        assert len(rows) >= 1
        reasons = [r['reason'] for r in rows]
        assert 'MISSING_SCORE' in reasons

def test_filter_by_motion_logs_high_motion(temp_log_dir):
    """Test that HIGH_MOTION is logged for subjects exceeding thresholds."""
    subjects = [
        Participant(
            subject_id="sub_005",
            fmri_path=str(Path(temp_log_dir) / "fake.nii"),
            behavioral_data={"caq": 10},
            motion_metrics={"mean_fd": 0.6, "high_vol_ratio": 0.1} # High FD
        ),
        Participant(
            subject_id="sub_006",
            fmri_path=str(Path(temp_log_dir) / "fake.nii"),
            behavioral_data={"caq": 10},
            motion_metrics={"mean_fd": 0.2, "high_vol_ratio": 0.3} # High Vol
        ),
        Participant(
            subject_id="sub_007",
            fmri_path=str(Path(temp_log_dir) / "fake.nii"),
            behavioral_data={"caq": 10},
            motion_metrics={"mean_fd": 0.2, "high_vol_ratio": 0.1} # OK
        ),
    ]
    
    # Ensure fake.nii exists
    Path(temp_log_dir).mkdir(parents=True, exist_ok=True)
    (Path(temp_log_dir) / "fake.nii").touch()

    result = filter_by_motion(subjects)
    
    assert len(result) == 1
    assert result[0].subject_id == "sub_007"
    
    log_path = os.path.join(temp_log_dir, "data_exclusion_log.txt")
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        reasons = [r['reason'] for r in rows]
        assert reasons.count('HIGH_MOTION') == 2