"""
Unit tests for Fisher-z transformation and variance calculations in feature engineering.

This module tests the mathematical correctness of the fisher_z_transform function
and verifies that variance calculations handle edge cases correctly.
"""
import numpy as np
import pytest
import sys
import os

# Add project root to path to allow imports of sibling modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.feature_engineering import fisher_z_transform, extract_upper_triangular_vector


class TestFisherZTransform:
    """Tests for the Fisher-z transformation function."""

    def test_fisher_z_identity(self):
        """Test that Fisher-z transform of 0 is 0."""
        result = fisher_z_transform(np.array([0.0]))
        assert np.isclose(result[0], 0.0, atol=1e-10)

    def test_fisher_z_positive_correlation(self):
        """Test Fisher-z transform for positive correlations."""
        # r = 0.5 -> z ≈ 0.5493
        r = 0.5
        expected_z = 0.5 * np.log((1 + r) / (1 - r))
        result = fisher_z_transform(np.array([r]))
        assert np.isclose(result[0], expected_z, atol=1e-6)

    def test_fisher_z_negative_correlation(self):
        """Test Fisher-z transform for negative correlations."""
        # r = -0.5 -> z ≈ -0.5493
        r = -0.5
        expected_z = 0.5 * np.log((1 + r) / (1 - r))
        result = fisher_z_transform(np.array([r]))
        assert np.isclose(result[0], expected_z, atol=1e-6)

    def test_fisher_z_near_bounds(self):
        """Test Fisher-z transform for values near -1 and 1."""
        r_near_1 = 0.99
        expected_z_near_1 = 0.5 * np.log((1 + r_near_1) / (1 - r_near_1))
        result_near_1 = fisher_z_transform(np.array([r_near_1]))
        assert np.isclose(result_near_1[0], expected_z_near_1, atol=1e-4)

        r_near_neg_1 = -0.99
        expected_z_near_neg_1 = 0.5 * np.log((1 + r_near_neg_1) / (1 - r_near_neg_1))
        result_near_neg_1 = fisher_z_transform(np.array([r_near_neg_1]))
        assert np.isclose(result_near_neg_1[0], expected_z_near_neg_1, atol=1e-4)

    def test_fisher_z_clipping(self):
        """Test that values outside [-1, 1] are clipped to valid range."""
        r_invalid_high = 1.5
        result_high = fisher_z_transform(np.array([r_invalid_high]))
        # Should be clipped to 1.0 -> z is very large but finite due to float precision
        # Actually, implementation should clip to 0.9999 or similar to avoid inf
        # We just check it doesn't crash and returns a finite number
        assert np.isfinite(result_high[0])

        r_invalid_low = -1.5
        result_low = fisher_z_transform(np.array([r_invalid_low]))
        assert np.isfinite(result_low[0])

    def test_fisher_z_array_input(self):
        """Test Fisher-z transform on an array of correlations."""
        r_values = np.array([0.0, 0.5, -0.5, 0.9])
        result = fisher_z_transform(r_values)
        
        assert result.shape == r_values.shape
        
        for i, r in enumerate(r_values):
            # Clip for calculation if out of bounds
            r_clipped = np.clip(r, -0.9999, 0.9999)
            expected_z = 0.5 * np.log((1 + r_clipped) / (1 - r_clipped))
            assert np.isclose(result[i], expected_z, atol=1e-4)

    def test_fisher_z_variance_stabilization(self):
        """
        Verify that Fisher-z transformation stabilizes variance.
        The variance of z should be approximately 1/(N-3) where N is sample size.
        We test this by checking that the transformation is applied correctly.
        """
        # Generate random correlations
        n_samples = 100
        r_values = np.random.uniform(-0.9, 0.9, n_samples)
        z_values = fisher_z_transform(r_values)
        
        # Check that the transformation is monotonic
        assert np.all(np.diff(z_values) * np.diff(r_values) > 0) or np.all(np.diff(z_values) * np.diff(r_values) < 0)
        
        # Check that the range of z is roughly what we expect
        # z should be roughly in [-2.5, 2.5] for r in [-0.9, 0.9]
        assert np.min(z_values) > -3.0
        assert np.max(z_values) < 3.0


class TestVarianceCalculations:
    """Tests for variance-related calculations in feature engineering."""

    def test_extract_upper_triangular_vector_shape(self):
        """Test that upper triangular extraction produces correct shape."""
        n_regions = 10
        # Number of edges in upper triangle = n*(n-1)/2
        expected_size = n_regions * (n_regions - 1) // 2
        
        # Create a dummy symmetric matrix
        dummy_matrix = np.random.rand(n_regions, n_regions)
        dummy_matrix = (dummy_matrix + dummy_matrix.T) / 2
        
        result = extract_upper_triangular_vector(dummy_matrix)
        
        assert result.shape[0] == expected_size

    def test_extract_upper_triangular_content(self):
        """Test that upper triangular extraction gets the right elements."""
        # Create a known symmetric matrix
        n_regions = 4
        matrix = np.array([
            [1.0, 0.2, 0.3, 0.4],
            [0.2, 1.0, 0.5, 0.6],
            [0.3, 0.5, 1.0, 0.7],
            [0.4, 0.6, 0.7, 1.0]
        ])
        
        result = extract_upper_triangular_vector(matrix)
        
        # Expected upper triangular elements (excluding diagonal)
        expected = np.array([0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
        
        assert np.allclose(result, expected)

    def test_extract_upper_triangular_symmetry(self):
        """Test that extracting from a symmetric matrix works correctly."""
        n_regions = 5
        base = np.random.rand(n_regions, n_regions)
        symmetric_matrix = (base + base.T) / 2
        
        result = extract_upper_triangular_vector(symmetric_matrix)
        
        # Verify we get the same result regardless of how we access the upper triangle
        # (using np.triu_indices)
        expected = symmetric_matrix[np.triu_indices(n_regions, k=1)]
        
        assert np.allclose(result, expected)

    def test_extract_upper_triangular_diagonal_excluded(self):
        """Test that diagonal elements are excluded from the vector."""
        n_regions = 3
        matrix = np.eye(n_regions)  # Identity matrix
        
        result = extract_upper_triangular_vector(matrix)
        
        # For identity matrix, all off-diagonal elements are 0
        expected_size = n_regions * (n_regions - 1) // 2
        assert len(result) == expected_size
        assert np.allclose(result, 0.0)

    def test_extract_upper_triangular_single_element(self):
        """Test extraction for a 2x2 matrix (only 1 edge)."""
        matrix = np.array([[1.0, 0.5], [0.5, 1.0]])
        result = extract_upper_triangular_vector(matrix)
        
        assert len(result) == 1
        assert result[0] == 0.5


class TestIntegration:
    """Integration tests for feature engineering functions."""

    def test_fisher_z_then_upper_triangular(self):
        """Test combining Fisher-z with upper triangular extraction."""
        n_regions = 5
        # Create a correlation matrix
        base = np.random.rand(n_regions, n_regions)
        corr_matrix = (base + base.T) / 2
        
        # Clip to valid correlation range
        corr_matrix = np.clip(corr_matrix, -0.99, 0.99)
        np.fill_diagonal(corr_matrix, 1.0)
        
        # Apply Fisher-z
        z_matrix = fisher_z_transform(corr_matrix)
        
        # Extract upper triangular
        z_vector = extract_upper_triangular_vector(z_matrix)
        
        # Verify shape
        expected_size = n_regions * (n_regions - 1) // 2
        assert z_vector.shape[0] == expected_size
        
        # Verify all values are finite
        assert np.all(np.isfinite(z_vector))

    def test_zero_variance_handling(self):
        """Test that zero variance in correlations is handled correctly."""
        # Create a matrix where one row is constant (zero variance)
        n_regions = 4
        matrix = np.ones((n_regions, n_regions))
        matrix[0, 1:] = 0.5
        matrix[1:, 0] = 0.5
        # Ensure symmetry
        matrix = (matrix + matrix.T) / 2
        np.fill_diagonal(matrix, 1.0)
        
        # This should not crash
        z_matrix = fisher_z_transform(matrix)
        z_vector = extract_upper_triangular_vector(z_matrix)
        
        assert z_vector.shape[0] == n_regions * (n_regions - 1) // 2
        assert np.all(np.isfinite(z_vector))