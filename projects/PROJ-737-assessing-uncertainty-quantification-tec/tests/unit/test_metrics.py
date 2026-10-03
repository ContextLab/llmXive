"""
Unit tests for metrics calculation functions.

These tests verify the correctness of Calibration Error and Sharpness
calculations using known inputs and expected outputs.
"""
import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.metrics.evaluation import (
    calculate_calibration_error,
    calculate_sharpness,
    calculate_interval_coverage,
    calculate_mean_interval_width
)


class TestCalibrationError:
    """Tests for calculate_calibration_error function."""

    def test_perfect_calibration(self):
        """Test case where observed coverage exactly matches nominal level."""
        # Create data where exactly 90% of points are covered
        n_samples = 100
        predictions = np.zeros(n_samples)
        ground_truth = np.zeros(n_samples)

        # Set intervals such that first 90 are covered, last 10 are not
        intervals = np.zeros((n_samples, 2))
        intervals[:90, 0] = -1.0  # Lower bound
        intervals[:90, 1] = 1.0   # Upper bound
        # Last 10: intervals are [0, 0], ground_truth is 1 (not covered)
        intervals[90:, 0] = 0.0
        intervals[90:, 1] = 0.0
        ground_truth[90:] = 1.0

        error = calculate_calibration_error(predictions, intervals, ground_truth, 0.9)

        # Observed coverage = 0.9, Nominal = 0.9, Error = 0.0
        assert abs(error) < 1e-6, f"Expected 0.0 error, got {error}"

    def test_mis_calibration(self):
        """Test case where observed coverage differs from nominal level."""
        # Create data where 100% are covered but nominal is 90%
        n_samples = 100
        predictions = np.zeros(n_samples)
        ground_truth = np.zeros(n_samples)
        intervals = np.ones((n_samples, 2)) * [-10, 10]  # All covered

        error = calculate_calibration_error(predictions, intervals, ground_truth, 0.9)

        # Observed coverage = 1.0, Nominal = 0.9, Error = 0.1
        assert abs(error - 0.1) < 1e-6, f"Expected 0.1 error, got {error}"

    def test_no_coverage(self):
        """Test case where 0% are covered."""
        n_samples = 100
        predictions = np.zeros(n_samples)
        ground_truth = np.zeros(n_samples)
        intervals = np.zeros((n_samples, 2))  # Zero width at 0, ground_truth at 0
        # Actually, if intervals are [0,0] and ground_truth is 0, it IS covered.
        # Let's make ground_truth = 1 to ensure no coverage.
        ground_truth[:] = 1.0
        intervals[:] = [[0.0, 0.0]]

        error = calculate_calibration_error(predictions, intervals, ground_truth, 0.9)

        # Observed coverage = 0.0, Nominal = 0.9, Error = 0.9
        assert abs(error - 0.9) < 1e-6, f"Expected 0.9 error, got {error}"

    def test_invalid_nominal_level(self):
        """Test that invalid nominal level raises ValueError."""
        predictions = np.array([0.0])
        intervals = np.array([[0.0, 1.0]])
        ground_truth = np.array([0.5])

        with pytest.raises(ValueError):
            calculate_calibration_error(predictions, intervals, ground_truth, 1.5)

        with pytest.raises(ValueError):
            calculate_calibration_error(predictions, intervals, ground_truth, -0.1)

    def test_shape_mismatch(self):
        """Test that shape mismatch raises ValueError."""
        predictions = np.array([0.0, 1.0])
        intervals = np.array([[0.0, 1.0]])  # Only 1 sample
        ground_truth = np.array([0.5])

        with pytest.raises(ValueError):
            calculate_calibration_error(predictions, intervals, ground_truth, 0.9)

    def test_invalid_interval_shape(self):
        """Test that invalid interval shape raises ValueError."""
        predictions = np.array([0.0])
        intervals = np.array([0.0, 1.0])  # 1D array
        ground_truth = np.array([0.5])

        with pytest.raises(ValueError):
            calculate_calibration_error(predictions, intervals, ground_truth, 0.9)


class TestSharpness:
    """Tests for calculate_sharpness function."""

    def test_mean_width(self):
        """Test that sharpness equals mean interval width."""
        intervals = np.array([
            [0.0, 2.0],  # Width 2
            [0.0, 4.0],  # Width 4
            [0.0, 6.0]   # Width 6
        ])

        sharpness = calculate_sharpness(intervals)

        # Mean width = (2 + 4 + 6) / 3 = 4.0
        assert abs(sharpness - 4.0) < 1e-6, f"Expected 4.0, got {sharpness}"

    def test_zero_width_intervals(self):
        """Test sharpness with zero-width intervals."""
        intervals = np.array([
            [1.0, 1.0],
            [2.0, 2.0],
            [3.0, 3.0]
        ])

        sharpness = calculate_sharpness(intervals)

        assert sharpness == 0.0, f"Expected 0.0, got {sharpness}"

    def test_invalid_interval_shape(self):
        """Test that invalid interval shape raises ValueError."""
        intervals = np.array([1.0, 2.0, 3.0])  # 1D array

        with pytest.raises(ValueError):
            calculate_sharpness(intervals)

    def test_negative_width_handling(self):
        """Test that negative widths (lower > upper) are handled via absolute value."""
        intervals = np.array([
            [5.0, 1.0],  # Width -4 -> abs(4)
            [0.0, 2.0]   # Width 2
        ])

        sharpness = calculate_sharpness(intervals)

        # Mean width = (4 + 2) / 2 = 3.0
        assert abs(sharpness - 3.0) < 1e-6, f"Expected 3.0, got {sharpness}"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_interval_coverage(self):
        """Test calculate_interval_coverage."""
        predictions = np.array([0.0])
        intervals = np.array([[-1.0, 1.0]])
        ground_truth = np.array([0.5])

        coverage = calculate_interval_coverage(predictions, intervals, ground_truth)
        assert coverage == 1.0, f"Expected 1.0, got {coverage}"

        # Not covered
        ground_truth[0] = 2.0
        coverage = calculate_interval_coverage(predictions, intervals, ground_truth)
        assert coverage == 0.0, f"Expected 0.0, got {coverage}"

    def test_mean_interval_width(self):
        """Test calculate_mean_interval_width (alias for sharpness)."""
        intervals = np.array([[0.0, 10.0]])

        width = calculate_mean_interval_width(intervals)
        assert width == 10.0, f"Expected 10.0, got {width}"