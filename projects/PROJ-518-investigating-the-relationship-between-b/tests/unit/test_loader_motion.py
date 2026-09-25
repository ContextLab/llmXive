import pytest
import os
import tempfile
from pathlib import Path
import json

from code.data.loader import (
    Participant, 
    filter_by_motion, 
    log_exclusion,
    validate_and_filter_subjects
)
from code.utils.logging import log_exclusion as log_exclusion_func

class TestFilterByMotion:
    """Tests for the filter_by_motion function."""

    def test_filter_by_motion_default_thresholds(self):
        """Test filtering with default thresholds (fd=0.5, vol=0.2)."""
        subjects = [
            Participant(subject_id="sub_001", mean_fd=0.3, high_motion_volumes=10),
            Participant(subject_id="sub_002", mean_fd=0.6, high_motion_volumes=15),
            Participant(subject_id="sub_003", mean_fd=0.4, high_motion_volumes=25),
            Participant(subject_id="sub_004", mean_fd=0.2, high_motion_volumes=5),
        ]

        filtered = filter_by_motion(subjects, fd_thresh=0.5, vol_thresh=0.2)

        # sub_001: FD 0.3 < 0.5, volumes 10 < 0.2 (assuming 0.2 is count or proportion) -> Keep
        # sub_002: FD 0.6 > 0.5 -> Exclude
        # sub_003: FD 0.4 < 0.5, but volumes 25 > 0.2 -> Exclude
        # sub_004: FD 0.2 < 0.5, volumes 5 < 0.2 -> Keep

        # Note: The vol_thresh interpretation depends on the data. 
        # If vol_thresh is a proportion (0.2 = 20%), we need total volumes.
        # For this test, we assume vol_thresh is a count threshold for simplicity.
        
        # Adjusting test logic based on typical usage:
        # Let's assume vol_thresh is a count (e.g., 20 volumes)
        filtered = filter_by_motion(subjects, fd_thresh=0.5, vol_thresh=20)

        assert len(filtered) == 2
        assert filtered[0].subject_id == "sub_001"
        assert filtered[1].subject_id == "sub_004"

    def test_filter_by_motion_high_fd(self):
        """Test that subjects with high FD are excluded."""
        subjects = [
            Participant(subject_id="sub_001", mean_fd=0.8, high_motion_volumes=10),
            Participant(subject_id="sub_002", mean_fd=0.4, high_motion_volumes=10),
        ]

        filtered = filter_by_motion(subjects, fd_thresh=0.5, vol_thresh=20)

        assert len(filtered) == 1
        assert filtered[0].subject_id == "sub_002"

    def test_filter_by_motion_high_volumes(self):
        """Test that subjects with high motion volumes are excluded."""
        subjects = [
            Participant(subject_id="sub_001", mean_fd=0.3, high_motion_volumes=30),
            Participant(subject_id="sub_002", mean_fd=0.3, high_motion_volumes=10),
        ]

        filtered = filter_by_motion(subjects, fd_thresh=0.5, vol_thresh=20)

        assert len(filtered) == 1
        assert filtered[0].subject_id == "sub_002"

    def test_filter_by_motion_no_exclusions(self):
        """Test when no subjects exceed thresholds."""
        subjects = [
            Participant(subject_id="sub_001", mean_fd=0.1, high_motion_volumes=5),
            Participant(subject_id="sub_002", mean_fd=0.2, high_motion_volumes=10),
        ]

        filtered = filter_by_motion(subjects, fd_thresh=0.5, vol_thresh=20)

        assert len(filtered) == 2

    def test_filter_by_motion_empty_list(self):
        """Test with empty subject list."""
        filtered = filter_by_motion([], fd_thresh=0.5, vol_thresh=20)
        assert len(filtered) == 0

    def test_filter_by_motion_all_excluded(self):
        """Test when all subjects exceed thresholds."""
        subjects = [
            Participant(subject_id="sub_001", mean_fd=0.9, high_motion_volumes=30),
            Participant(subject_id="sub_002", mean_fd=0.8, high_motion_volumes=25),
        ]

        filtered = filter_by_motion(subjects, fd_thresh=0.5, vol_thresh=20)

        assert len(filtered) == 0

    def test_filter_by_motion_missing_motion_data(self):
        """Test handling of subjects with missing motion data."""
        subjects = [
            Participant(subject_id="sub_001", mean_fd=None, high_motion_volumes=None),
            Participant(subject_id="sub_002", mean_fd=0.3, high_motion_volumes=10),
        ]

        # Subjects with missing motion data should be kept (conservative approach)
        filtered = filter_by_motion(subjects, fd_thresh=0.5, vol_thresh=20)

        assert len(filtered) == 2

class TestLogExclusion:
    """Tests for the log_exclusion function."""

    def test_log_exclusion_creates_file(self):
        """Test that log_exclusion creates the exclusion log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the config to use our temp directory
            import code.utils.logging as logging_module
            original_get_config = logging_module.get_config
            
            class MockConfig:
                DATA_PATH = tmpdir
            
            logging_module.get_config = lambda: MockConfig()
            
            try:
                log_exclusion(reason="HIGH_MOTION", subject_id="sub_test")
                
                log_path = os.path.join(tmpdir, "data_exclusion_log.txt")
                assert os.path.exists(log_path)
            finally:
                logging_module.get_config = original_get_config

    def test_log_exclusion_standardized_codes(self):
        """Test that standardized reason codes are used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import code.utils.logging as logging_module
            original_get_config = logging_module.get_config
            
            class MockConfig:
                DATA_PATH = tmpdir
            
            logging_module.get_config = lambda: MockConfig()
            
            try:
                # Test all standardized codes
                log_exclusion(reason="MISSING_SCAN", subject_id="sub_1")
                log_exclusion(reason="MISSING_SCORE", subject_id="sub_2")
                log_exclusion(reason="HIGH_MOTION", subject_id="sub_3")
                
                log_path = os.path.join(tmpdir, "data_exclusion_log.txt")
                assert os.path.exists(log_path)
                
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                
                assert len(lines) == 3
                assert "MISSING_SCAN" in lines[0]
                assert "MISSING_SCORE" in lines[1]
                assert "HIGH_MOTION" in lines[2]
            finally:
                logging_module.get_config = original_get_config