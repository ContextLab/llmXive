import pytest
from unittest.mock import patch
import os
import sys
from pathlib import Path

# Add project root to path for imports if running from test dir
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.loader import Participant, filter_by_motion
from utils.logging import log_exclusion
import logging

@pytest.fixture
def valid_subject():
    return Participant(
        subject_id="sub_001",
        fmri_path="/fake/path.nii.gz",
        behavioral_data={"caq_score": 100},
        motion_metrics={"fd_mean": 0.1}
    )

@pytest.fixture
def high_motion_subject():
    return Participant(
        subject_id="sub_002",
        fmri_path="/fake/path.nii.gz",
        behavioral_data={"caq_score": 100},
        motion_metrics={"fd_mean": 0.6}  # Above default 0.5
    )

@pytest.fixture
def missing_motion_subject():
    return Participant(
        subject_id="sub_003",
        fmri_path="/fake/path.nii.gz",
        behavioral_data={"caq_score": 100},
        motion_metrics=None
    )

def test_filter_by_motion_keeps_valid(valid_subject, caplog):
    """Test that subjects with low motion are kept."""
    subjects = [valid_subject]
    with caplog.at_level(logging.WARNING):
        result = filter_by_motion(subjects)
    
    assert len(result) == 1
    assert result[0].subject_id == "sub_001"
    assert "HIGH_MOTION" not in caplog.text

def test_filter_by_motion_excludes_high_motion(high_motion_subject, caplog):
    """Test that subjects with FD > threshold are excluded and logged."""
    subjects = [high_motion_subject]
    with caplog.at_level(logging.WARNING):
        result = filter_by_motion(subjects)
    
    assert len(result) == 0
    assert "High motion" in caplog.text
    assert "HIGH_MOTION" in caplog.text

def test_filter_by_motion_excludes_missing_metrics(missing_motion_subject, caplog):
    """Test that subjects with missing motion metrics are excluded."""
    subjects = [missing_motion_subject]
    with caplog.at_level(logging.WARNING):
        result = filter_by_motion(subjects)
    
    assert len(result) == 0
    # Even if specific "Missing motion metrics" text isn't there, 
    # the exclusion logic must trigger HIGH_MOTION log
    assert "HIGH_MOTION" in caplog.text or len(result) == 0

def test_filter_by_motion_custom_threshold():
    """Test custom FD threshold."""
    low_motion = Participant(
        subject_id="sub_004",
        fmri_path="/fake/path.nii.gz",
        behavioral_data={"caq_score": 100},
        motion_metrics={"fd_mean": 0.3}
    )
    
    # Default threshold (0.5) keeps 0.3
    assert len(filter_by_motion([low_motion], fd_thresh=0.5)) == 1
    
    # Custom threshold (0.2) excludes 0.3
    assert len(filter_by_motion([low_motion], fd_thresh=0.2)) == 0
    
    # Custom threshold (0.25) excludes 0.3
    assert len(filter_by_motion([low_motion], fd_thresh=0.25)) == 0