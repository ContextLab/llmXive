"""
Unit tests for edge case handling functions in edge_cases.py.
"""

import numpy as np
import pytest
from code.analysis.edge_cases import (
    clamp_noise_scale,
    detect_collinearity,
    enforce_min_sample_size,
    validate_covariance_matrix,
    handle_zero_variance,
    get_edge_case_status
)
import warnings


class TestClampNoiseScale:
    """Tests for clamp_noise_scale function."""

    def test_no_clamping_needed(self):
        """Test when noise scale is within acceptable range."""
        noise_scale = 0.5
        data_range = (0.0, 10.0)
        clamped, was_clamped = clamp_noise_scale(noise_scale, data_range)
        
        assert not was_clamped
        assert clamped == noise_scale

    def test_clamping_applied(self):
        """Test when noise scale exceeds data range."""
        noise_scale = 5.0  # 50% of data span
        data_range = (0.0, 10.0)
        clamped, was_clamped = clamp_noise_scale(noise_scale, data_range)
        
        assert was_clamped
        # Should be capped at 10% of data span (1.0)
        assert clamped <= 1.0

    def test_min_scale_enforced(self):
        """Test that minimum scale is enforced."""
        noise_scale = 1e-10
        data_range = (0.0, 10.0)
        clamped, was_clamped = clamp_noise_scale(noise_scale, data_range, min_scale=1e-6)
        
        assert clamped == 1e-6

    def test_degenerate_range(self):
        """Test handling of degenerate data range."""
        noise_scale = 1.0
        data_range = (5.0, 5.0)  # Zero span
        clamped, was_clamped = clamp_noise_scale(noise_scale, data_range, min_scale=1e-6)
        
        # Should use min_scale
        assert clamped == 1e-6


class TestDetectCollinearity:
    """Tests for detect_collinearity function."""

    def test_no_collinearity(self):
        """Test when no collinearity exists."""
        np.random.seed(42)
        X = np.random.randn(100, 3)
        X_clean, dropped, info = detect_collinearity(X, threshold=0.9)
        
        assert len(dropped) == 0
        assert info['collinear_pairs'] == []
        assert X_clean.shape == X.shape

    def test_collinearity_detected(self):
        """Test detection of collinear features."""
        np.random.seed(42)
        n = 100
        x1 = np.random.randn(n)
        x2 = x1 + 0.01 * np.random.randn(n)  # Highly correlated
        x3 = np.random.randn(n)  # Independent
        
        X = np.column_stack([x1, x2, x3])
        X_clean, dropped, info = detect_collinearity(X, threshold=0.9)
        
        assert len(dropped) == 1
        assert len(X_clean.shape) == 2
        assert X_clean.shape[1] == 2  # One feature dropped

    def test_strategy_first(self):
        """Test 'first' drop strategy."""
        np.random.seed(42)
        n = 100
        x1 = np.random.randn(n)
        x2 = x1 + 0.01 * np.random.randn(n)
        X = np.column_stack([x1, x2])
        
        _, dropped, _ = detect_collinearity(X, threshold=0.9, drop_strategy='first')
        assert 1 in dropped  # Second feature dropped

    def test_strategy_last(self):
        """Test 'last' drop strategy."""
        np.random.seed(42)
        n = 100
        x1 = np.random.randn(n)
        x2 = x1 + 0.01 * np.random.randn(n)
        X = np.column_stack([x1, x2])
        
        _, dropped, _ = detect_collinearity(X, threshold=0.9, drop_strategy='last')
        assert 0 in dropped  # First feature dropped

    def test_single_feature(self):
        """Test with single feature (no collinearity possible)."""
        X = np.random.randn(100, 1)
        X_clean, dropped, info = detect_collinearity(X)
        
        assert len(dropped) == 0
        assert X_clean.shape == X.shape


class TestEnforceMinSampleSize:
    """Tests for enforce_min_sample_size function."""

    def test_valid_sample_size(self):
        """Test with sample size above minimum."""
        sample = np.random.randn(50)
        result, error = enforce_min_sample_size(sample, min_size=10)
        
        assert result is not None
        assert error is None
        assert len(result) == 50

    def test_insufficient_sample_size(self):
        """Test with sample size below minimum."""
        sample = np.random.randn(5)
        result, error = enforce_min_sample_size(sample, min_size=10)
        
        assert result is None
        assert error is not None
        assert "below minimum" in error.lower()

    def test_raise_on_failure(self):
        """Test that ValueError is raised when raise_on_failure=True."""
        sample = np.random.randn(5)
        
        with pytest.raises(ValueError, match="below minimum"):
            enforce_min_sample_size(sample, min_size=10, raise_on_failure=True)

    def test_empty_sample(self):
        """Test with empty sample."""
        sample = np.array([])
        result, error = enforce_min_sample_size(sample, min_size=10)
        
        assert result is None
        assert error is not None
        assert "empty" in error.lower()

    def test_2d_array(self):
        """Test with 2D array (regression case)."""
        X = np.random.randn(50, 3)
        result, error = enforce_min_sample_size(X, min_size=10)
        
        assert result is not None
        assert error is None
        assert result.shape[0] == 50

    def test_2d_insufficient_rows(self):
        """Test 2D array with insufficient rows."""
        X = np.random.randn(5, 3)
        result, error = enforce_min_sample_size(X, min_size=10)
        
        assert result is None
        assert error is not None


class TestValidateCovarianceMatrix:
    """Tests for validate_covariance_matrix function."""

    def test_valid_covariance(self):
        """Test with valid positive semi-definite matrix."""
        A = np.random.randn(3, 3)
        cov = A @ A.T  # Guaranteed PSD
        
        is_valid, error = validate_covariance_matrix(cov)
        
        assert is_valid
        assert error is None

    def test_not_symmetric(self):
        """Test with non-symmetric matrix."""
        cov = np.array([[1.0, 0.5], [0.6, 1.0]])
        
        is_valid, error = validate_covariance_matrix(cov)
        
        assert not is_valid
        assert "not symmetric" in error.lower()

    def test_not_positive_definite(self):
        """Test with matrix that has negative eigenvalues."""
        cov = np.array([[1.0, 2.0], [2.0, 1.0]])  # Eigenvalues: 3, -1
        
        is_valid, error = validate_covariance_matrix(cov)
        
        assert not is_valid
        assert "not positive semi-definite" in error.lower()

    def test_non_square(self):
        """Test with non-square matrix."""
        cov = np.random.randn(3, 4)
        
        is_valid, error = validate_covariance_matrix(cov)
        
        assert not is_valid
        assert "square" in error.lower()


class TestHandleZeroVariance:
    """Tests for handle_zero_variance function."""

    def test_no_zero_variance(self):
        """Test when no zero variance features exist."""
        np.random.seed(42)
        data = np.random.randn(100, 3)
        
        stabilized, zero_indices = handle_zero_variance(data)
        
        assert len(zero_indices) == 0
        assert np.allclose(stabilized, data)

    def test_zero_variance_detected(self):
        """Test detection of zero variance features."""
        data = np.array([
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0]
        ])
        
        stabilized, zero_indices = handle_zero_variance(data, epsilon=1e-8)
        
        assert len(zero_indices) == 3  # All columns have zero variance
        # Stabilized data should not be identical to original
        assert not np.allclose(stabilized, data)

    def test_1d_array(self):
        """Test with 1D array."""
        data = np.array([1.0, 1.0, 1.0])
        
        stabilized, zero_indices = handle_zero_variance(data)
        
        assert len(zero_indices) == 1


class TestGetEdgeCaseStatus:
    """Tests for get_edge_case_status function."""

    def test_empty_results(self):
        """Test with empty results dictionary."""
        status = get_edge_case_status({})
        
        assert status['noise_clamped'] == 0
        assert status['collinearity_detected'] == 0
        assert status['samples_too_small'] == 0

    def test_with_edge_case_data(self):
        """Test with populated edge case data."""
        results = {
            'edge_cases': {
                'noise_clamped_count': 5,
                'collinearity_count': 2,
                'min_sample_violations': 1,
                'zero_var_count': 3,
                'invalid_cov_count': 0
            }
        }
        
        status = get_edge_case_status(results)
        
        assert status['noise_clamped'] == 5
        assert status['collinearity_detected'] == 2
        assert status['samples_too_small'] == 1
        assert status['zero_variance_features'] == 3
        assert status['invalid_covariance'] == 0