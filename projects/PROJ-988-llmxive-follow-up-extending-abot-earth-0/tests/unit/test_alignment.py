"""
Unit tests for alignment error calculation.
Verifies that the calculate_alignment_error function correctly computes residuals
and that validate_alignment_threshold correctly identifies if the error is within the 2m limit.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Add project root to path to allow imports from code/lib
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from lib.alignment import calculate_alignment_error, validate_alignment_threshold, AlignmentError


class TestCalculateAlignmentError:
    """Tests for the calculate_alignment_error function."""

    def test_perfect_alignment_zero_error(self):
        """Test that identical coordinates result in 0.0 error."""
        coords_gt = np.array([[0.0, 0.0], [10.0, 10.0], [20.0, 20.0]])
        coords_pred = coords_gt.copy()

        error = calculate_alignment_error(coords_gt, coords_pred)
        assert error == 0.0

    def test_single_point_error(self):
        """Test error calculation for a single point offset."""
        coords_gt = np.array([[0.0, 0.0]])
        coords_pred = np.array([[1.0, 0.0]])  # 1m offset in X

        error = calculate_alignment_error(coords_gt, coords_pred)
        # Euclidean distance = 1.0
        assert np.isclose(error, 1.0)

    def test_multiple_points_average_error(self):
        """Test error calculation averages errors across multiple points."""
        coords_gt = np.array([[0.0, 0.0], [0.0, 0.0]])
        coords_pred = np.array([[3.0, 0.0], [1.0, 0.0]])

        # Errors: 3.0 and 1.0. Mean = 2.0
        error = calculate_alignment_error(coords_gt, coords_pred)
        assert np.isclose(error, 2.0)

    def test_3d_coordinates(self):
        """Test error calculation with 3D coordinates (X, Y, Z)."""
        coords_gt = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
        coords_pred = np.array([[1.0, 0.0, 0.0], [1.0, 2.0, 1.0]])

        # Point 1: dist( (0,0,0), (1,0,0) ) = 1.0
        # Point 2: dist( (1,1,1), (1,2,1) ) = 1.0
        # Mean = 1.0
        error = calculate_alignment_error(coords_gt, coords_pred)
        assert np.isclose(error, 1.0)

    def test_mismatched_shapes_raises_error(self):
        """Test that mismatched coordinate shapes raise an AlignmentError."""
        coords_gt = np.array([[0.0, 0.0], [1.0, 1.0]])
        coords_pred = np.array([[0.0, 0.0]])

        with pytest.raises(AlignmentError):
            calculate_alignment_error(coords_gt, coords_pred)

    def test_empty_arrays_raises_error(self):
        """Test that empty arrays raise an AlignmentError."""
        coords_gt = np.array([]).reshape(0, 2)
        coords_pred = np.array([]).reshape(0, 2)

        with pytest.raises(AlignmentError):
            calculate_alignment_error(coords_gt, coords_pred)

    def test_large_error_calculation(self):
        """Test calculation with large offsets to ensure no overflow or logic errors."""
        coords_gt = np.array([[0.0, 0.0], [1000.0, 1000.0]])
        coords_pred = np.array([[500.0, 0.0], [1000.0, 1500.0]])

        # Point 1: 500.0
        # Point 2: 500.0
        # Mean: 500.0
        error = calculate_alignment_error(coords_gt, coords_pred)
        assert np.isclose(error, 500.0)


class TestValidateAlignmentThreshold:
    """Tests for the validate_alignment_threshold function."""

    def test_pass_below_threshold(self):
        """Test that error < 2m passes validation."""
        is_valid, error = validate_alignment_threshold(1.5, threshold=2.0)
        assert is_valid is True
        assert np.isclose(error, 1.5)

    def test_fail_above_threshold(self):
        """Test that error > 2m fails validation."""
        is_valid, error = validate_alignment_threshold(2.5, threshold=2.0)
        assert is_valid is False
        assert np.isclose(error, 2.5)

    def test_exact_threshold_passes(self):
        """Test that error == 2m passes validation (<=)."""
        is_valid, error = validate_alignment_threshold(2.0, threshold=2.0)
        assert is_valid is True
        assert np.isclose(error, 2.0)

    def test_default_threshold_is_two_meters(self):
        """Test that the default threshold is 2.0 meters."""
        is_valid, error = validate_alignment_threshold(1.99)
        assert is_valid is True

        is_valid, error = validate_alignment_threshold(2.01)
        assert is_valid is False

    def test_integration_with_calculate_error(self):
        """Integration test: calculate error then validate against 2m threshold."""
        coords_gt = np.array([[0.0, 0.0], [10.0, 10.0]])
        # Create a shift that results in ~1.5m average error
        # Point 1: (0,0) -> (1.5, 0) = 1.5m
        # Point 2: (10,10) -> (10, 10) = 0m
        # Mean = 0.75m (Pass)
        coords_pred = np.array([[1.5, 0.0], [10.0, 10.0]])

        error = calculate_alignment_error(coords_gt, coords_pred)
        is_valid, _ = validate_alignment_threshold(error)

        assert is_valid is True

        # Now create a shift > 2m
        # Point 1: (0,0) -> (3,0) = 3m
        # Point 2: (10,10) -> (10,10) = 0m
        # Mean = 1.5m (Pass) - Wait, let's make it fail.
        # Point 1: (0,0) -> (4,0) = 4m
        # Point 2: (10,10) -> (10,10) = 0m
        # Mean = 2m (Pass)
        # Point 1: (0,0) -> (5,0) = 5m
        # Point 2: (10,10) -> (10,10) = 0m
        # Mean = 2.5m (Fail)
        coords_pred_fail = np.array([[5.0, 0.0], [10.0, 10.0]])
        error_fail = calculate_alignment_error(coords_gt, coords_pred_fail)
        is_valid_fail, _ = validate_alignment_threshold(error_fail)

        assert is_valid_fail is False