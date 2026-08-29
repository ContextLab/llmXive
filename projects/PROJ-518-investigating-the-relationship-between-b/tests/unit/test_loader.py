import pytest
from pathlib import Path
from code.data.loader import Participant, filter_by_motion
from code.utils.logging import log_exclusion
import os

def test_filter_by_motion_excludes_high_fd(tmp_path):
    """Test that filter_by_motion excludes participants with high mean FD."""
    # Create a mock log file path
    log_path = tmp_path / "exclusion_log.csv"
    os.environ['LOG_PATH'] = str(log_path)
    
    # Create participants with different motion levels
    sub_pass = Participant(
        subject_id="sub_001",
        fmri_path=str(tmp_path / "bold.nii.gz"),
        behavioral_data={"caq_score": 10.0},
        fd_mean=0.3,
        fd_max=0.4,
        high_motion_volumes_ratio=0.1
    )
    
    sub_fail_fd = Participant(
        subject_id="sub_002",
        fmri_path=str(tmp_path / "bold.nii.gz"),
        behavioral_data={"caq_score": 12.0},
        fd_mean=0.6,  # Exceeds default 0.5
        fd_max=0.7,
        high_motion_volumes_ratio=0.1
    )
    
    sub_fail_vol = Participant(
        subject_id="sub_003",
        fmri_path=str(tmp_path / "bold.nii.gz"),
        behavioral_data={"caq_score": 11.0},
        fd_mean=0.4,
        fd_max=0.5,
        high_motion_volumes_ratio=0.3  # Exceeds default 0.2
    )
    
    subjects = [sub_pass, sub_fail_fd, sub_fail_vol]
    filtered = filter_by_motion(subjects)
    
    assert len(filtered) == 1
    assert filtered[0].subject_id == "sub_001"
    
    # Verify log file was updated
    assert log_path.exists()
    log_content = log_path.read_text()
    assert "HIGH_MOTION" in log_content
    assert "sub_002" in log_content
    assert "sub_003" in log_content

def test_filter_by_motion_custom_thresholds(tmp_path):
    """Test filter_by_motion with custom thresholds."""
    log_path = tmp_path / "exclusion_log.csv"
    os.environ['LOG_PATH'] = str(log_path)
    
    sub = Participant(
        subject_id="sub_004",
        fmri_path=str(tmp_path / "bold.nii.gz"),
        behavioral_data={"caq_score": 9.0},
        fd_mean=0.45,
        fd_max=0.5,
        high_motion_volumes_ratio=0.15
    )
    
    # Pass with default thresholds
    assert len(filter_by_motion([sub])) == 1
    
    # Fail with stricter thresholds
    filtered = filter_by_motion([sub], fd_thresh=0.4, vol_thresh=0.1)
    assert len(filtered) == 0

def test_filter_by_motion_empty_list(tmp_path):
    """Test filter_by_motion with empty input."""
    result = filter_by_motion([])
    assert result == []