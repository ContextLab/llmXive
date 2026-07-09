"""
Unit tests for motion exclusion logic (T005).
"""

import os
import tempfile
import numpy as np
import pytest

from code.utils.motion import (
    check_motion_exclusion,
    generate_exclusion_log,
    calculate_mean_fd
)
from code.config import get_config


class TestMotionExclusion:
    """Tests for the motion exclusion logic."""

    def test_exclusion_logic_above_threshold(self):
        """Test that subjects with FD > threshold are excluded."""
        # Default threshold is 0.2
        assert check_motion_exclusion(0.21) is True
        assert check_motion_exclusion(0.2001) is True

    def test_exclusion_logic_below_threshold(self):
        """Test that subjects with FD < threshold are included."""
        assert check_motion_exclusion(0.19) is False
        assert check_motion_exclusion(0.0) is False

    def test_exclusion_logic_custom_threshold(self):
        """Test exclusion with a custom threshold."""
        # Custom threshold 0.1
        assert check_motion_exclusion(0.15, threshold=0.1) is True
        assert check_motion_exclusion(0.05, threshold=0.1) is False

    def test_exclusion_logic_boundary(self):
        """Test exact boundary condition (FD == threshold)."""
        # If FD == threshold, it should NOT be excluded (strictly greater)
        assert check_motion_exclusion(0.2, threshold=0.2) is False

    def test_generate_exclusion_log_creates_file(self):
        """Test that the exclusion log is created with correct format."""
        subjects = [
            {'Subject_ID': 'S1', 'Mean_FD': 0.1},
            {'Subject_ID': 'S2', 'Mean_FD': 0.25},
            {'Subject_ID': 'S3', 'Mean_FD': 0.15},
            {'Subject_ID': 'S4', 'Mean_FD': 0.3},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'exclusion_log.csv')
            included, excluded = generate_exclusion_log(subjects, output_path)

            # Check file exists
            assert os.path.exists(output_path)

            # Check included subjects
            assert len(included) == 2
            assert included[0]['Subject_ID'] == 'S1'
            assert included[1]['Subject_ID'] == 'S3'

            # Check excluded subjects
            assert len(excluded) == 2
            assert excluded[0]['Subject_ID'] == 'S2'
            assert excluded[1]['Subject_ID'] == 'S4'

            # Verify CSV content
            with open(output_path, 'r') as f:
                content = f.read()
                assert 'Subject_ID' in content
                assert 'Exclusion_Reason' in content
                assert 'Mean_FD' in content
                assert 'S2' in content
                assert 'S4' in content
                assert 'Motion' in content

    def test_generate_exclusion_log_missing_fd(self):
        """Test handling of subjects with missing FD."""
        subjects = [
            {'Subject_ID': 'S1', 'Mean_FD': 0.1},
            {'Subject_ID': 'S2', 'Mean_FD': None},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'exclusion_log.csv')
            included, excluded = generate_exclusion_log(subjects, output_path)

            assert len(included) == 1
            assert len(excluded) == 1
            assert excluded[0]['Exclusion_Reason'] == 'Missing_FD'