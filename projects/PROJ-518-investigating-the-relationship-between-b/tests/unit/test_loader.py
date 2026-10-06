import pytest
from code.data.loader import Participant, filter_by_motion, validate_and_filter_subjects
from code.utils.logging import REASON_HIGH_MOTION, REASON_MISSING_SCAN, REASON_MISSING_SCORE
import os
import csv
from pathlib import Path

@pytest.fixture
def sample_subjects():
    """Create a list of test participants with varying motion levels."""
    return [
        Participant(
            subject_id="sub_001",
            fmri_path="data/raw/sub_001_fMRI.nii.gz",
            behavioral_data={"caq": 150.0},
            caq_score=150.0,
            motion_metrics={"mean_fd": 0.1}
        ),
        Participant(
            subject_id="sub_002",
            fmri_path="data/raw/sub_002_fMRI.nii.gz",
            behavioral_data={"caq": 160.0},
            caq_score=160.0,
            motion_metrics={"mean_fd": 0.6}  # High motion
        ),
        Participant(
            subject_id="sub_003",
            fmri_path="data/raw/sub_003_fMRI.nii.gz",
            behavioral_data={"caq": 140.0},
            caq_score=140.0,
            motion_metrics={"mean_fd": 0.2}
        ),
        Participant(
            subject_id="sub_004",
            fmri_path=None,  # Missing scan
            behavioral_data={"caq": 130.0},
            caq_score=130.0,
            motion_metrics={"mean_fd": 0.1}
        ),
        Participant(
            subject_id="sub_005",
            fmri_path="data/raw/sub_005_fMRI.nii.gz",
            behavioral_data={},
            caq_score=None,  # Missing CAQ
            motion_metrics={"mean_fd": 0.1}
        ),
        Participant(
            subject_id="sub_006",
            fmri_path="data/raw/sub_006_fMRI.nii.gz",
            behavioral_data={"caq": 120.0},
            caq_score=120.0,
            motion_metrics=None  # Missing motion metrics
        ),
    ]

def test_filter_by_motion_excludes_high_motion(sample_subjects, tmp_path, monkeypatch):
    """Test that filter_by_motion excludes subjects with mean_fd > threshold."""
    # Setup logging to a temp file to verify logs
    log_file = tmp_path / "data_exclusion_log.txt"
    monkeypatch.setattr("code.utils.logging.EXCLUSION_LOG_PATH", str(log_file))
    
    # Run filter
    # Note: validate_and_filter_subjects must run first to handle scan/CAQ issues
    # But filter_by_motion is independent in logic, so we test it directly on clean data
    # We'll create a subset of valid subjects for this specific test
    valid_subjects = [
        Participant(
            subject_id="sub_good",
            fmri_path="data/raw/sub_good.nii.gz",
            behavioral_data={"caq": 100.0},
            caq_score=100.0,
            motion_metrics={"mean_fd": 0.1}
        ),
        Participant(
            subject_id="sub_bad",
            fmri_path="data/raw/sub_bad.nii.gz",
            behavioral_data={"caq": 100.0},
            caq_score=100.0,
            motion_metrics={"mean_fd": 0.8}
        )
    ]
    
    filtered = filter_by_motion(valid_subjects, fd_thresh=0.5)
    
    assert len(filtered) == 1
    assert filtered[0].subject_id == "sub_good"

def test_filter_by_motion_logs_exclusion(sample_subjects, tmp_path, monkeypatch):
    """Test that filter_by_motion logs exclusions with HIGH_MOTION reason."""
    log_file = tmp_path / "data_exclusion_log.txt"
    monkeypatch.setattr("code.utils.logging.EXCLUSION_LOG_PATH", str(log_file))
    
    # Create a subject with high motion
    high_motion_sub = Participant(
        subject_id="sub_high",
        fmri_path="data/raw/sub_high.nii.gz",
        behavioral_data={"caq": 100.0},
        caq_score=100.0,
        motion_metrics={"mean_fd": 0.9}
    )
    
    filter_by_motion([high_motion_sub], fd_thresh=0.5)
    
    # Verify log file exists and contains the exclusion
    assert log_file.exists()
    with open(log_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['reason'] == REASON_HIGH_MOTION
        assert rows[0]['subject_id'] == "sub_high"

def test_filter_by_motion_handles_missing_metrics(sample_subjects, tmp_path, monkeypatch):
    """Test that filter_by_motion excludes subjects with missing motion metrics."""
    log_file = tmp_path / "data_exclusion_log.txt"
    monkeypatch.setattr("code.utils.logging.EXCLUSION_LOG_PATH", str(log_file))
    
    missing_metrics_sub = Participant(
        subject_id="sub_missing",
        fmri_path="data/raw/sub_missing.nii.gz",
        behavioral_data={"caq": 100.0},
        caq_score=100.0,
        motion_metrics=None
    )
    
    filtered = filter_by_motion([missing_metrics_sub], fd_thresh=0.5)
    
    assert len(filtered) == 0
    
    # Verify log
    with open(log_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['reason'] == REASON_HIGH_MOTION
        assert rows[0]['subject_id'] == "sub_missing"

def test_validate_and_filter_subjects_integration(sample_subjects, tmp_path, monkeypatch):
    """Integration test for validate_and_filter_subjects and filter_by_motion."""
    log_file = tmp_path / "data_exclusion_log.txt"
    monkeypatch.setattr("code.utils.logging.EXCLUSION_LOG_PATH", str(log_file))
    
    # Run validation first
    validated = validate_and_filter_subjects(sample_subjects)
    
    # Should exclude sub_004 (missing scan) and sub_005 (missing CAQ)
    assert len(validated) == 4
    subject_ids = [s.subject_id for s in validated]
    assert "sub_004" not in subject_ids
    assert "sub_005" not in subject_ids
    
    # Now run motion filter
    motion_filtered = filter_by_motion(validated, fd_thresh=0.5)
    
    # Should exclude sub_002 (high motion) and sub_006 (missing metrics)
    assert len(motion_filtered) == 2
    subject_ids = [s.subject_id for s in motion_filtered]
    assert "sub_002" not in subject_ids
    assert "sub_006" not in subject_ids
    assert "sub_001" in subject_ids
    assert "sub_003" in subject_ids

    # Verify total exclusions logged
    with open(log_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        # Expected exclusions: sub_004 (scan), sub_005 (score), sub_002 (motion), sub_006 (motion)
        assert len(rows) == 4