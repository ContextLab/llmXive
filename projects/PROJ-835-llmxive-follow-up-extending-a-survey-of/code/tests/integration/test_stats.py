"""
Integration tests for the statistical utilities in src/utils/stats.py.
"""
import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.stats import compute_benign_statistics, calculate_mahalanobis_distance


class TestStatsUtils:
    """Tests for Mahalanobis distance and covariance estimation."""

    def test_compute_benign_statistics_shapes(self):
        """Test that compute_benign_statistics returns correct shapes."""
        np.random.seed(42)
        n_samples = 100
        dim = 512
        data = np.random.randn(n_samples, dim)

        mean, cov = compute_benign_statistics(data)

        assert mean.shape == (dim,), f"Mean shape mismatch: {mean.shape} vs ({dim},)"
        assert cov.shape == (dim, dim), f"Cov shape mismatch: {cov.shape} vs ({dim}, {dim})"

    def test_compute_benign_statistics_small_sample(self):
        """Test covariance estimation with minimal sample size (2)."""
        np.random.seed(42)
        dim = 64
        # Only 2 samples
        data = np.random.randn(2, dim)

        mean, cov = compute_benign_statistics(data)

        assert mean.shape == (dim,)
        assert cov.shape == (dim, dim)
        # Check that covariance is not all zeros
        assert not np.allclose(cov, 0), "Covariance matrix should not be zero for distinct samples."

    def test_compute_benign_statistics_raises_on_empty(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError):
            compute_benign_statistics(np.array([]).reshape(0, 10))

    def test_compute_benign_statistics_raises_on_single_sample(self):
        """Test that single sample raises ValueError."""
        with pytest.raises(ValueError):
            compute_benign_statistics(np.random.randn(1, 10))

    def test_mahalanobis_distance_zero_for_centroid(self):
        """Test that distance from centroid to itself is zero."""
        np.random.seed(42)
        n_samples = 50
        dim = 32
        data = np.random.randn(n_samples, dim)

        mean, cov = compute_benign_statistics(data)

        # Create a sample exactly at the mean
        sample_at_mean = mean.reshape(1, -1)

        distances = calculate_mahalanobis_distance(sample_at_mean, mean, cov)

        assert np.isclose(distances[0], 0.0, atol=1e-5), "Distance from centroid to itself should be 0."

    def test_mahalanobis_distance_symmetry(self):
        """Test that distance calculation is consistent for multiple points."""
        np.random.seed(42)
        dim = 128
        # Generate benign data
        benign_data = np.random.randn(100, dim)
        mean, cov = compute_benign_statistics(benign_data)

        # Generate test points
        test_points = np.random.randn(10, dim)

        distances = calculate_mahalanobis_distance(test_points, mean, cov)

        assert distances.shape == (10,), "Distance array shape mismatch."
        assert np.all(distances >= 0), "Mahalanobis distances must be non-negative."

    def test_mahalanobis_distance_dimension_mismatch(self):
        """Test that dimension mismatch raises ValueError."""
        np.random.seed(42)
        dim = 64
        data = np.random.randn(10, dim)
        mean, cov = compute_benign_statistics(data)

        # Try to calculate distance with wrong dimension
        wrong_dim_points = np.random.randn(5, dim + 10)

        with pytest.raises(ValueError):
            calculate_mahalanobis_distance(wrong_dim_points, mean, cov)

    def test_mahalanobis_distance_vs_scipy(self):
        """
        Compare our implementation against scipy.spatial.distance.mahalanobis
        for a small dataset to ensure correctness.
        """
        from scipy.spatial.distance import mahalanobis as scipy_mahalanobis

        np.random.seed(123)
        dim = 10
        n_samples = 20
        data = np.random.randn(n_samples, dim)

        mean, cov = compute_benign_statistics(data)
        cov_inv = np.linalg.inv(cov)

        # Calculate distances using our function
        our_distances = calculate_mahalanobis_distance(data, mean, cov)

        # Calculate distances using scipy (loop over samples)
        scipy_distances = np.array([
            scipy_mahalanobis(x, mean, cov_inv) for x in data
        ])

        # Check if they match within tolerance
        assert np.allclose(our_distances, scipy_distances, rtol=1e-5), \
            f"Our distances differ from scipy: max diff = {np.max(np.abs(our_distances - scipy_distances))}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])