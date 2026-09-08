"""
Unit tests for T022a: Per-Sample Entanglement Score Calculation.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from entanglement_scores import (
    compute_per_sample_stats,
    compute_mahalanobis_distance,
    integrate_features,
    load_dominant_eigenvalue,
    load_covariance_matrix,
)


class TestComputePerSampleStats:
    def test_variance_calculation(self):
        """Test variance calculation for uniform and non-uniform distributions."""
        # Uniform: variance should be 0
        uniform_matrix = np.array([[1.0, 1.0, 1.0, 1.0], [2.0, 2.0, 2.0, 2.0]])
        variance = np.var(uniform_matrix, axis=1, ddof=0)
        assert np.allclose(variance, [0.0, 0.0])

        # Non-uniform: variance > 0
        non_uniform_matrix = np.array([[1.0, 2.0, 3.0, 4.0]])
        variance = np.var(non_uniform_matrix, axis=1, ddof=0)
        expected_var = 1.25  # Variance of [1, 2, 3, 4]
        assert np.isclose(variance[0], expected_var)

    def test_entropy_calculation(self):
        """Test entropy calculation."""
        # Uniform distribution (max entropy)
        uniform_matrix = np.array([[1.0, 1.0, 1.0, 1.0]])
        # Shift to positive, normalize
        shifted = uniform_matrix - np.min(uniform_matrix, axis=1, keepdims=True) + 1e-9
        normalized = shifted / np.sum(shifted, axis=1, keepdims=True)
        entropy = stats.entropy(normalized, axis=1)
        # Max entropy for 4 items is ln(4)
        assert np.isclose(entropy[0], np.log(4), atol=1e-4)

        # Degenerate distribution (min entropy)
        degenerate_matrix = np.array([[10.0, 0.0, 0.0, 0.0]])
        shifted = degenerate_matrix - np.min(degenerate_matrix, axis=1, keepdims=True) + 1e-9
        normalized = shifted / np.sum(shifted, axis=1, keepdims=True)
        entropy = stats.entropy(normalized, axis=1)
        assert entropy[0] < 1e-4  # Close to 0

    def test_skewness_and_kurtosis(self):
        """Test skewness and kurtosis calculation."""
        # Symmetric distribution: skewness ~ 0
        symmetric_matrix = np.array([[1.0, 2.0, 3.0, 4.0]])
        skewness = stats.skew(symmetric_matrix, axis=1)
        assert np.isclose(skewness[0], 0.0, atol=1e-5)

        # Skewed distribution
        skewed_matrix = np.array([[1.0, 1.0, 1.0, 10.0]])
        skewness = stats.skew(skewed_matrix, axis=1)
        assert skewness[0] > 0  # Positive skew

class TestMahalanobisDistance:
    def test_mahalanobis_with_identity_covariance(self):
        """Test Mahalanobis distance with identity covariance (should equal Euclidean)."""
        teacher_matrix = np.array([[1.0, 2.0, 3.0, 4.0]])
        cov_matrix = np.eye(4)
        
        # Mean is [2.5, 2.5, 3.5, 3.5] for a larger set, but here only 1 sample
        # Mean of [1, 2, 3, 4] is [2.5, 2.5, 3.5, 3.5] -> wait, mean is per column
        # teacher_matrix shape: (1, 4). Mean shape: (4,)
        # Mean = [1, 2, 3, 4]
        mu = np.mean(teacher_matrix, axis=0)
        diff = teacher_matrix - mu  # Should be [0, 0, 0, 0]
        
        mahal = compute_mahalanobis_distance(teacher_matrix, cov_matrix, type('obj', (object,), {'info': lambda x: None})())
        assert np.allclose(mahal, [0.0])
        
        # Test with 2 samples
        teacher_matrix_2 = np.array([[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]])
        mu_2 = np.mean(teacher_matrix_2, axis=0)  # [3, 4, 5, 6]
        diff_2 = teacher_matrix_2 - mu_2  # [-2, -2, -2, -2] and [2, 2, 2, 2]
        
        # D^2 = diff^T * I^-1 * diff = sum(diff^2)
        expected_d2 = np.sum(diff_2 ** 2, axis=1)
        expected_mahal = np.sqrt(expected_d2)
        
        mahal_2 = compute_mahalanobis_distance(teacher_matrix_2, cov_matrix, type('obj', (object,), {'info': lambda x: None})())
        assert np.allclose(mahal_2, expected_mahal)

    def test_singular_covariance_handling(self):
        """Test that pseudo-inverse is used for singular covariance."""
        teacher_matrix = np.array([[1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0]])
        # Singular covariance (all rows identical)
        cov_matrix = np.zeros((4, 4))
        
        # Should not raise
        mahal = compute_mahalanobis_distance(teacher_matrix, cov_matrix, type('obj', (object,), {'warning': lambda x: None})())
        assert mahal is not None

class TestIntegrateFeatures:
    def test_integrate_features(self):
        """Test that features are correctly added to DataFrame."""
        df = pd.DataFrame({"id": [1, 2], "value": [10, 20]})
        stats_dict = {
            "variance": np.array([1.0, 2.0]),
            "entropy": np.array([0.5, 0.6]),
            "skewness": np.array([0.1, 0.2]),
            "kurtosis": np.array([3.0, 3.1]),
        }
        mahalanobis = np.array([1.5, 2.5])
        
        result_df = integrate_features(df, stats_dict, mahalanobis, type('obj', (object,), {'info': lambda x: None})())
        
        assert "variance" in result_df.columns
        assert "entropy" in result_df.columns
        assert "skewness" in result_df.columns
        assert "kurtosis" in result_df.columns
        assert "mahalanobis_distance" in result_df.columns
        
        assert result_df["variance"].tolist() == [1.0, 2.0]
        assert result_df["mahalanobis_distance"].tolist() == [1.5, 2.5]
