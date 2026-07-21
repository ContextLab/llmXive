"""
Unit tests for motion threshold checking in preprocess.py
"""

import pytest
from pathlib import Path
import pandas as pd
import numpy as np

from code.data.preprocess import (
    calculate_fd,
    check_motion_threshold,
    TRANSLATION_THRESHOLD_MM,
    ROTATION_THRESHOLD_DEG
)


class TestCalculateFD:
    """Tests for FD calculation."""

    def test_calculate_fd_basic(self):
        """Test basic FD calculation with known values."""
        # Create mock confounds with known motion parameters
        confounds = pd.DataFrame({
            'trans_x': [0.0, 0.5, 1.0, 1.5],
            'trans_y': [0.0, 0.2, 0.4, 0.6],
            'trans_z': [0.0, 0.1, 0.2, 0.3],
            'rot_x': [0.0, 0.1, 0.2, 0.3],
            'rot_y': [0.0, 0.05, 0.1, 0.15],
            'rot_z': [0.0, 0.02, 0.04, 0.06]
        })

        mean_fd, mean_trans, mean_rot = calculate_fd(confounds)

        # Verify FD is calculated (should be positive)
        assert mean_fd > 0
        assert mean_trans > 0
        assert mean_rot > 0

        # Verify types
        assert isinstance(mean_fd, float)
        assert isinstance(mean_trans, float)
        assert isinstance(mean_rot, float)

    def test_calculate_fd_missing_columns(self):
        """Test that missing columns raise an error."""
        confounds = pd.DataFrame({
            'trans_x': [0.0, 0.5],
            'trans_y': [0.0, 0.2]
            # Missing other required columns
        })

        with pytest.raises(ValueError) as exc_info:
            calculate_fd(confounds)
        
        assert "Missing required motion parameters" in str(exc_info.value)

    def test_calculate_fd_zero_motion(self):
        """Test FD calculation with zero motion (all same values)."""
        confounds = pd.DataFrame({
            'trans_x': [1.0, 1.0, 1.0],
            'trans_y': [1.0, 1.0, 1.0],
            'trans_z': [1.0, 1.0, 1.0],
            'rot_x': [0.5, 0.5, 0.5],
            'rot_y': [0.5, 0.5, 0.5],
            'rot_z': [0.5, 0.5, 0.5]
        })

        mean_fd, mean_trans, mean_rot = calculate_fd(confounds)

        # With no change between volumes, FD should be 0
        assert mean_fd == 0.0
        assert mean_trans == 0.0
        assert mean_rot == 0.0


class TestCheckMotionThreshold:
    """Tests for motion threshold checking."""

    def test_pass_all_thresholds(self):
        """Test subject passes when all metrics are below threshold."""
        passed, reasons = check_motion_threshold(
            mean_fd=1.0,
            mean_translation=2.0,
            mean_rotation=2.0
        )

        assert passed is True
        assert len(reasons) == 0

    def test_fail_translation_threshold(self):
        """Test subject fails when translation exceeds threshold."""
        passed, reasons = check_motion_threshold(
            mean_fd=1.0,
            mean_translation=3.5,  # > 3.0
            mean_rotation=2.0
        )

        assert passed is False
        assert len(reasons) == 1
        assert "Translation" in reasons[0]
        assert "3.5" in reasons[0]

    def test_fail_rotation_threshold(self):
        """Test subject fails when rotation exceeds threshold."""
        passed, reasons = check_motion_threshold(
            mean_fd=1.0,
            mean_translation=2.0,
            mean_rotation=3.5  # > 3.0
        )

        assert passed is False
        assert len(reasons) == 1
        assert "Rotation" in reasons[0]
        assert "3.5" in reasons[0]

    def test_fail_both_thresholds(self):
        """Test subject fails when both translation and rotation exceed thresholds."""
        passed, reasons = check_motion_threshold(
            mean_fd=1.0,
            mean_translation=4.0,
            mean_rotation=4.0
        )

        assert passed is False
        assert len(reasons) == 2
        assert any("Translation" in r for r in reasons)
        assert any("Rotation" in r for r in reasons)

    def test_exact_threshold_values(self):
        """Test behavior at exact threshold boundaries."""
        # At exactly 3.0mm translation - should PASS (not > 3.0)
        passed, reasons = check_motion_threshold(
            mean_fd=1.0,
            mean_translation=3.0,
            mean_rotation=2.0
        )
        assert passed is True

        # At exactly 3.0° rotation - should PASS (not > 3.0)
        passed, reasons = check_motion_threshold(
            mean_fd=1.0,
            mean_translation=2.0,
            mean_rotation=3.0
        )
        assert passed is True

        # Just above 3.0 - should FAIL
        passed, reasons = check_motion_threshold(
            mean_fd=1.0,
            mean_translation=3.001,
            mean_rotation=2.0
        )
        assert passed is False

    def test_threshold_constants(self):
        """Verify threshold constants match spec."""
        assert TRANSLATION_THRESHOLD_MM == 3.0
        assert ROTATION_THRESHOLD_DEG == 3.0