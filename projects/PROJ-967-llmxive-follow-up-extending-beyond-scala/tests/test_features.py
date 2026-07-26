"""
Unit tests for feature engineering functions.
"""
import pytest
import numpy as np
import pandas as pd
import json
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from features import (
    calculate_variance_and_range,
    calculate_entropy,
    calculate_skewness_and_kurtosis,
    calculate_per_sample_stats,
    calculate_frobenius_norm_outer_product,
    calculate_global_covariance_and_eigenvalue,
    calculate_fidelity_loss
)

class TestVarianceAndRange:
    """Tests for variance and range calculations."""

    def test_normal_case(self):
        """Test with normal distribution."""
        scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        variance, range_val = calculate_variance_and_range(scores)
        
        assert abs(variance - 2.0) < 1e-6  # Population variance
        assert range_val == 4.0

    def test_constant_values(self):
        """Test with constant values (zero variance)."""
        scores = np.array([5.0, 5.0, 5.0, 5.0])
        variance, range_val = calculate_variance_and_range(scores)
        
        assert variance == 0.0
        assert range_val == 0.0

    def test_empty_array(self):
        """Test with empty array."""
        scores = np.array([])
        variance, range_val = calculate_variance_and_range(scores)
        
        assert variance == 0.0
        assert range_val == 0.0

    def test_single_value(self):
        """Test with single value."""
        scores = np.array([3.0])
        variance, range_val = calculate_variance_and_range(scores)
        
        assert variance == 0.0
        assert range_val == 0.0

class TestEntropy:
    """Tests for entropy calculations."""

    def test_uniform_distribution(self):
        """Test with uniform distribution (max entropy)."""
        scores = np.array([1.0, 1.0, 1.0, 1.0])
        entropy = calculate_entropy(scores)
        
        # Max entropy for 4 categories is log2(4) = 2.0
        assert abs(entropy - 2.0) < 1e-6

    def test_concentrated_distribution(self):
        """Test with concentrated distribution (low entropy)."""
        scores = np.array([10.0, 0.0, 0.0, 0.0])
        entropy = calculate_entropy(scores)
        
        assert entropy == 0.0

    def test_zero_sum(self):
        """Test with all zeros."""
        scores = np.array([0.0, 0.0, 0.0, 0.0])
        entropy = calculate_entropy(scores)
        
        assert entropy == 0.0

    def test_empty_array(self):
        """Test with empty array."""
        scores = np.array([])
        entropy = calculate_entropy(scores)
        
        assert entropy == 0.0

class TestSkewnessAndKurtosis:
    """Tests for skewness and kurtosis calculations."""

    def test_normal_distribution(self):
        """Test with approximately normal distribution."""
        scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        skewness, kurtosis = calculate_skewness_and_kurtosis(scores)
        
        # Skewness should be close to 0 for symmetric distribution
        assert abs(skewness) < 1.0
        # Kurtosis can vary but should be finite
        assert np.isfinite(kurtosis)

    def test_small_sample(self):
        """Test with less than 3 samples."""
        scores = np.array([1.0, 2.0])
        skewness, kurtosis = calculate_skewness_and_kurtosis(scores)
        
        assert skewness == 0.0
        assert kurtosis == 0.0

class TestPerSampleStats:
    """Tests for per-sample statistics."""

    def test_complete_stats(self):
        """Test that all stats are computed correctly."""
        scores = np.array([0.8, 0.6, 0.4, 0.2])
        stats = calculate_per_sample_stats(scores)
        
        assert 'variance' in stats
        assert 'entropy' in stats
        assert 'skewness' in stats
        assert 'kurtosis' in stats
        assert 'range' in stats
        
        assert np.isfinite(stats['variance'])
        assert np.isfinite(stats['entropy'])
        assert np.isfinite(stats['skewness'])
        assert np.isfinite(stats['kurtosis'])
        assert np.isfinite(stats['range'])

    def test_zero_variance_handling(self):
        """Test handling of zero-variance case."""
        scores = np.array([0.5, 0.5, 0.5, 0.5])
        stats = calculate_per_sample_stats(scores)
        
        assert stats['variance'] == 0.0
        assert stats['range'] == 0.0
        # Entropy should be 0 for uniform distribution
        assert stats['entropy'] == 0.0

class TestFrobeniusNorm:
    """Tests for Frobenius norm of outer product."""

    def test_basic_case(self):
        """Test basic Frobenius norm calculation."""
        scores = np.array([1.0, 2.0, 3.0, 4.0])
        norm = calculate_frobenius_norm_outer_product(scores)
        
        # Frobenius norm of outer product is ||v||^2
        expected = np.sum(scores ** 2)
        assert abs(norm - expected) < 1e-6

    def test_zero_vector(self):
        """Test with zero vector."""
        scores = np.array([0.0, 0.0, 0.0, 0.0])
        norm = calculate_frobenius_norm_outer_product(scores)
        
        assert norm == 0.0

    def test_empty_vector(self):
        """Test with empty vector."""
        scores = np.array([])
        norm = calculate_frobenius_norm_outer_product(scores)
        
        assert norm == 0.0

class TestGlobalCovarianceAndEigenvalue:
    """Tests for global covariance matrix and dominant eigenvalue."""

    def test_basic_covariance(self):
        """Test basic covariance matrix computation."""
        # Create a dataset with 10 samples and 4 dimensions
        np.random.seed(42)
        all_scores = np.random.randn(10, 4)
        
        cov_matrix, dominant_eigenvalue = calculate_global_covariance_and_eigenvalue(all_scores)
        
        assert cov_matrix.shape == (4, 4)
        assert np.isfinite(dominant_eigenvalue)
        assert dominant_eigenvalue > 0  # Covariance matrices should have non-negative eigenvalues

    def test_symmetric_matrix(self):
        """Test that covariance matrix is symmetric."""
        np.random.seed(42)
        all_scores = np.random.randn(20, 4)
        
        cov_matrix, _ = calculate_global_covariance_and_eigenvalue(all_scores)
        
        assert np.allclose(cov_matrix, cov_matrix.T)

    def test_minimum_samples(self):
        """Test with minimum required samples."""
        all_scores = np.array([
            [1.0, 2.0, 3.0, 4.0],
            [2.0, 3.0, 4.0, 5.0]
        ])
        
        cov_matrix, dominant_eigenvalue = calculate_global_covariance_and_eigenvalue(all_scores)
        
        assert cov_matrix.shape == (4, 4)
        assert np.isfinite(dominant_eigenvalue)

    def test_insufficient_samples(self):
        """Test that error is raised with insufficient samples."""
        all_scores = np.array([[1.0, 2.0, 3.0, 4.0]])
        
        with pytest.raises(ValueError, match="Need at least 2 samples"):
            calculate_global_covariance_and_eigenvalue(all_scores)

    def test_non_finite_eigenvalue(self):
        """Test handling of non-finite eigenvalue."""
        # Create data with NaN
        all_scores = np.array([
            [1.0, 2.0, 3.0, 4.0],
            [np.nan, 3.0, 4.0, 5.0]
        ])
        
        with pytest.raises(ValueError, match="not finite"):
            calculate_global_covariance_and_eigenvalue(all_scores)

class TestFidelityLoss:
    """Tests for fidelity loss calculation."""

    def test_basic_mae(self):
        """Test basic MAE calculation."""
        student = 0.7
        human = 0.8
        loss = calculate_fidelity_loss(student, human)
        
        assert abs(loss - 0.1) < 1e-6

    def test_zero_loss(self):
        """Test zero loss when scores match."""
        student = 0.5
        human = 0.5
        loss = calculate_fidelity_loss(student, human)
        
        assert loss == 0.0

    def test_negative_scores(self):
        """Test with negative scores."""
        student = -0.2
        human = 0.3
        loss = calculate_fidelity_loss(student, human)
        
        assert abs(loss - 0.5) < 1e-6
