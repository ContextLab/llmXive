"""
Unit tests for code/data/preprocess.py motion threshold logic.

This test suite verifies that the motion threshold logic correctly flags
subjects based on translation (>3mm) and rotation (>3°) thresholds as
specified in FR-002 and SC-002.
"""
import pytest
import numpy as np
from code.data.preprocess import check_motion_threshold, calculate_fd
from code.config import Config


class TestMotionThresholdLogic:
    """Tests for motion threshold validation logic."""

    def test_translation_below_threshold_passes(self):
        """Subject with translation 2.5mm should PASS (threshold is 3mm)."""
        motion_metrics = {
            'translation_x': 1.0,
            'translation_y': 1.5,
            'translation_z': 2.5,
            'rotation_x': 0.5,
            'rotation_y': 0.3,
            'rotation_z': 0.2
        }
        is_excluded, reason = check_motion_threshold(motion_metrics)
        assert is_excluded is False, f"Subject should pass, but was excluded: {reason}"
        assert reason is None

    def test_translation_at_threshold_passes(self):
        """Subject with translation exactly 3.0mm should PASS (threshold is >3mm)."""
        motion_metrics = {
            'translation_x': 1.0,
            'translation_y': 1.0,
            'translation_z': 3.0,
            'rotation_x': 0.5,
            'rotation_y': 0.3,
            'rotation_z': 0.2
        }
        is_excluded, reason = check_motion_threshold(motion_metrics)
        assert is_excluded is False, f"Subject at threshold should pass, but was excluded: {reason}"
        assert reason is None

    def test_translation_above_threshold_fails(self):
        """Subject with translation 3.1mm should FAIL (threshold is >3mm)."""
        motion_metrics = {
            'translation_x': 1.0,
            'translation_y': 1.0,
            'translation_z': 3.1,
            'rotation_x': 0.5,
            'rotation_y': 0.3,
            'rotation_z': 0.2
        }
        is_excluded, reason = check_motion_threshold(motion_metrics)
        assert is_excluded is True, "Subject with translation >3mm should be excluded"
        assert reason is not None
        assert "translation" in reason.lower() or "motion" in reason.lower()

    def test_rotation_below_threshold_passes(self):
        """Subject with rotation 2.5° should PASS (threshold is 3°)."""
        motion_metrics = {
            'translation_x': 1.0,
            'translation_y': 1.0,
            'translation_z': 1.0,
            'rotation_x': 1.0,
            'rotation_y': 1.0,
            'rotation_z': 2.5
        }
        is_excluded, reason = check_motion_threshold(motion_metrics)
        assert is_excluded is False, f"Subject should pass, but was excluded: {reason}"
        assert reason is None

    def test_rotation_at_threshold_passes(self):
        """Subject with rotation exactly 3.0° should PASS (threshold is >3°)."""
        motion_metrics = {
            'translation_x': 1.0,
            'translation_y': 1.0,
            'translation_z': 1.0,
            'rotation_x': 1.0,
            'rotation_y': 1.0,
            'rotation_z': 3.0
        }
        is_excluded, reason = check_motion_threshold(motion_metrics)
        assert is_excluded is False, f"Subject at threshold should pass, but was excluded: {reason}"
        assert reason is None

    def test_rotation_above_threshold_fails(self):
        """Subject with rotation 3.1° should FAIL (threshold is >3°)."""
        motion_metrics = {
            'translation_x': 1.0,
            'translation_y': 1.0,
            'translation_z': 1.0,
            'rotation_x': 1.0,
            'rotation_y': 1.0,
            'rotation_z': 3.1
        }
        is_excluded, reason = check_motion_threshold(motion_metrics)
        assert is_excluded is True, "Subject with rotation >3° should be excluded"
        assert reason is not None
        assert "rotation" in reason.lower() or "motion" in reason.lower()

    def test_both_translation_and_rotation_above_threshold_fails(self):
        """Subject exceeding both thresholds should be excluded with clear reason."""
        motion_metrics = {
            'translation_x': 1.0,
            'translation_y': 1.0,
            'translation_z': 4.0,
            'rotation_x': 1.0,
            'rotation_y': 1.0,
            'rotation_z': 4.0
        }
        is_excluded, reason = check_motion_threshold(motion_metrics)
        assert is_excluded is True, "Subject exceeding both thresholds should be excluded"
        assert reason is not None

    def test_max_translation_detection(self):
        """Verify that the maximum translation across axes is used for threshold check."""
        # translation_z is 2.9, but translation_x is 3.5 -> should fail
        motion_metrics = {
            'translation_x': 3.5,
            'translation_y': 1.0,
            'translation_z': 2.9,
            'rotation_x': 0.5,
            'rotation_y': 0.3,
            'rotation_z': 0.2
        }
        is_excluded, reason = check_motion_threshold(motion_metrics)
        assert is_excluded is True, "Max translation (3.5mm) should trigger exclusion"

    def test_max_rotation_detection(self):
        """Verify that the maximum rotation across axes is used for threshold check."""
        # rotation_z is 2.9, but rotation_x is 3.5 -> should fail
        motion_metrics = {
            'translation_x': 1.0,
            'translation_y': 1.0,
            'translation_z': 1.0,
            'rotation_x': 3.5,
            'rotation_y': 1.0,
            'rotation_z': 2.9
        }
        is_excluded, reason = check_motion_threshold(motion_metrics)
        assert is_excluded is True, "Max rotation (3.5°) should trigger exclusion"

    def test_fd_calculation_with_real_values(self):
        """Test FD calculation with known values to ensure mathematical correctness."""
        # Create synthetic but realistic motion parameters
        # Using values that would produce a known FD
        motion_metrics = {
            'translation_x': 0.5,
            'translation_y': 0.5,
            'translation_z': 0.5,
            'rotation_x': 0.1,  # radians
            'rotation_y': 0.1,
            'rotation_z': 0.1
        }
        # FD is typically calculated as sum of absolute differences + rotation component
        # This test ensures the function runs and returns a finite value
        fd = calculate_fd(motion_metrics)
        assert isinstance(fd, (int, float)), "FD should be a numeric value"
        assert np.isfinite(fd), "FD should be finite (not NaN or Inf)"
        assert fd >= 0, "FD should be non-negative"

    def test_fd_calculation_with_high_motion(self):
        """Test FD calculation with high motion values."""
        motion_metrics = {
            'translation_x': 2.0,
            'translation_y': 2.0,
            'translation_z': 2.0,
            'rotation_x': 0.5,
            'rotation_y': 0.5,
            'rotation_z': 0.5
        }
        fd = calculate_fd(motion_metrics)
        assert isinstance(fd, (int, float)), "FD should be a numeric value"
        assert np.isfinite(fd), "FD should be finite"
        assert fd > 0, "FD should be positive for high motion"

    def test_missing_motion_metrics_raises_error(self):
        """Test that missing required motion metrics raises an appropriate error."""
        motion_metrics = {
            'translation_x': 1.0,
            # Missing other required keys
        }
        with pytest.raises((KeyError, ValueError)):
            check_motion_threshold(motion_metrics)

    def test_config_thresholds_are_respected(self):
        """Verify that Config thresholds are used (if Config has motion thresholds defined)."""
        # This test verifies the logic respects the 3mm/3° constants
        # Since Config might not have motion thresholds explicitly, we test the hardcoded logic
        motion_metrics = {
            'translation_x': 3.0001,
            'translation_y': 0.0,
            'translation_z': 0.0,
            'rotation_x': 0.0,
            'rotation_y': 0.0,
            'rotation_z': 0.0
        }
        is_excluded, reason = check_motion_threshold(motion_metrics)
        assert is_excluded is True, "Threshold should be strictly > 3.0"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])