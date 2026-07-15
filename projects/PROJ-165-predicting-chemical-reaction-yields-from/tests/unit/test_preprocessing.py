"""
Unit tests for spectral resampling logic in src.data.preprocessing.

Tests verify that:
1. Linear interpolation correctly resamples spectra to target grids.
2. Edge cases (single point, empty array) are handled gracefully.
3. Output shape matches the requested target grid size.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Ensure the project root is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.preprocessing import resample_spectrum, normalize_spectrum


class TestSpectralResampling:
    """Tests for the resample_spectrum function."""

    def test_resample_linear_interpolation(self):
        """Test standard linear interpolation to a finer grid."""
        # Original data: 3 points
        x_orig = np.array([100.0, 200.0, 300.0])
        y_orig = np.array([10.0, 20.0, 30.0])  # Linear relationship

        # Target: 5 points between 100 and 300
        x_target = np.linspace(100.0, 300.0, 5)  # 100, 150, 200, 250, 300

        y_resampled = resample_spectrum(x_orig, y_orig, x_target)

        expected_y = np.array([10.0, 15.0, 20.0, 25.0, 30.0])
        np.testing.assert_array_almost_equal(y_resampled, expected_y, decimal=5)

    def test_resample_coarser_grid(self):
        """Test resampling to a coarser grid (downsampling)."""
        x_orig = np.linspace(0.0, 100.0, 101)
        y_orig = np.sin(x_orig / 10.0)  # Some non-linear signal

        # Target: 11 points
        x_target = np.linspace(0.0, 100.0, 11)

        y_resampled = resample_spectrum(x_orig, y_orig, x_target)

        assert len(y_resampled) == len(x_target)
        # Check that values are within the range of original y (interpolation property)
        assert np.min(y_resampled) >= np.min(y_orig) - 1e-5
        assert np.max(y_resampled) <= np.max(y_orig) + 1e-5

    def test_resample_outside_bounds_clipping(self):
        """Test behavior when target grid extends beyond original bounds."""
        x_orig = np.array([100.0, 200.0, 300.0])
        y_orig = np.array([10.0, 20.0, 30.0])

        # Target extends slightly beyond [100, 300]
        x_target = np.linspace(90.0, 310.0, 5)

        # The function should handle this (typically by clipping or extrapolation)
        # Based on standard numpy.interp behavior, values outside bounds are clipped
        y_resampled = resample_spectrum(x_orig, y_orig, x_target)

        assert len(y_resampled) == len(x_target)
        # Check that the first and last values correspond to the boundary values
        # (assuming clip behavior which is standard for interp)
        assert y_resampled[0] == y_orig[0]
        assert y_resampled[-1] == y_orig[-1]

    def test_resample_single_point(self):
        """Test resampling when original data has only one point."""
        x_orig = np.array([150.0])
        y_orig = np.array([25.0])

        # Target grid
        x_target = np.linspace(100.0, 200.0, 5)

        # Should return the single value repeated (or handle gracefully)
        # If implementation uses interp, it might fail or return constant.
        # Assuming a robust implementation that handles single point by returning constant
        y_resampled = resample_spectrum(x_orig, y_orig, x_target)

        assert len(y_resampled) == len(x_target)
        # If the implementation handles single points by constant fill:
        np.testing.assert_array_almost_equal(y_resampled, np.full_like(y_resampled, 25.0), decimal=5)

    def test_resample_empty_input_raises(self):
        """Test that empty input arrays raise an error."""
        x_orig = np.array([])
        y_orig = np.array([])
        x_target = np.linspace(100.0, 200.0, 5)

        with pytest.raises((ValueError, IndexError)):
            resample_spectrum(x_orig, y_orig, x_target)

    def test_resample_mismatched_lengths_raises(self):
        """Test that mismatched x and y lengths raise an error."""
        x_orig = np.array([100.0, 200.0, 300.0])
        y_orig = np.array([10.0, 20.0]) # Mismatched
        x_target = np.linspace(100.0, 300.0, 5)

        with pytest.raises(ValueError):
            resample_spectrum(x_orig, y_orig, x_target)

    def test_resample_preserves_dtype(self):
        """Test that output dtype matches input dtype (float64)."""
        x_orig = np.array([100.0, 200.0, 300.0], dtype=np.float64)
        y_orig = np.array([10.0, 20.0, 30.0], dtype=np.float64)
        x_target = np.linspace(100.0, 300.0, 5, dtype=np.float64)

        y_resampled = resample_spectrum(x_orig, y_orig, x_target)

        assert y_resampled.dtype == np.float64


class TestSpectralNormalization:
    """Tests for the normalize_spectrum function."""

    def test_normalize_unit_variance(self):
        """Test that normalized spectrum has unit variance (or close to 1)."""
        # Create a spectrum with known variance
        y_orig = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        # Normalize
        y_norm = normalize_spectrum(y_orig)

        # Calculate variance (ddof=1 for sample variance, or 0 for population)
        # Standard normalization usually implies std dev = 1
        std_dev = np.std(y_norm, ddof=0)
        assert np.isclose(std_dev, 1.0, atol=1e-5)

    def test_normalize_mean_zero(self):
        """Test that normalized spectrum has mean close to 0."""
        y_orig = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        
        y_norm = normalize_spectrum(y_orig)

        mean_val = np.mean(y_norm)
        assert np.isclose(mean_val, 0.0, atol=1e-5)

    def test_normalize_constant_input(self):
        """Test behavior when input has zero variance (constant values)."""
        y_orig = np.array([5.0, 5.0, 5.0, 5.0])
        
        # Should handle division by zero gracefully (e.g., return zeros or NaN)
        # Standard practice: if std is 0, return array of zeros or same array
        y_norm = normalize_spectrum(y_orig)

        # If implementation returns zeros:
        assert np.all(y_norm == 0.0) or np.all(np.isnan(y_norm))

    def test_normalize_2d_array(self):
        """Test normalization of 2D array (batch of spectra)."""
        # Shape: (batch_size, num_points)
        y_orig = np.array([
            [1.0, 2.0, 3.0],
            [10.0, 20.0, 30.0]
        ])
        
        y_norm = normalize_spectrum(y_orig, axis=1) # Normalize along the spectral axis

        # Check shape
        assert y_norm.shape == y_orig.shape

        # Check each row
        for i in range(y_orig.shape[0]):
            std_row = np.std(y_norm[i])
            mean_row = np.mean(y_norm[i])
            assert np.isclose(std_row, 1.0, atol=1e-5)
            assert np.isclose(mean_row, 0.0, atol=1e-5)

    def test_normalize_inplace_false(self):
        """Test that normalize_spectrum does not modify input if copy is made."""
        y_orig = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_orig_copy = y_orig.copy()
        
        y_norm = normalize_spectrum(y_orig)

        # Input should remain unchanged
        np.testing.assert_array_equal(y_orig, y_orig_copy)
        # Output should be different
        assert not np.array_equal(y_orig, y_norm)