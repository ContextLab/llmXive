"""
Unit tests for edge case handling functions in code/analysis/edge_cases.py.
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
    """Tests for the clamp_noise_scale function."""

    def test_no_clamping_needed(self):
        """Test when noise scale is within data range."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        noise_scale = 0.5
        epsilon = 1.0
        
        clamped, was_clamped, reason = clamp_noise_scale(data, noise_scale, epsilon)
        
        assert not was_clamped
        assert clamped == noise_scale
        assert "within acceptable range" in reason

    def test_clamping_exceeds_range(self):
        """Test when noise scale exceeds data range."""
        data = np.array([1.0, 2.0, 3.0])
        noise_scale = 10.0  # Much larger than range (2.0)
        epsilon = 0.01
        
        clamped, was_clamped, reason = clamp_noise_scale(data, noise_scale, epsilon)
        
        assert was_clamped
        assert clamped == 2.0  # Should be clamped to data range
        assert "exceeds data range" in reason
        assert "Clamped" in reason

    def test_constant_data(self):
        """Test handling of constant data (zero range)."""
        data = np.array([5.0, 5.0, 5.0])
        noise_scale = 1.0
        epsilon = 0.5
        
        clamped, was_clamped, reason = clamp_noise_scale(data, noise_scale, epsilon)
        
        assert was_clamped
        assert clamped > 0
        assert "zero range" in reason.lower()

    def test_empty_data(self):
        """Test that empty data raises an error."""
        data = np.array([])
        noise_scale = 1.0
        epsilon = 0.5
        
        with pytest.raises(ValueError, match="empty"):
            clamp_noise_scale(data, noise_scale, epsilon)

    def test_invalid_epsilon(self):
        """Test that non-positive epsilon raises an error."""
        data = np.array([1.0, 2.0])
        noise_scale = 1.0
        epsilon = 0
        
        with pytest.raises(ValueError, match="positive"):
            clamp_noise_scale(data, noise_scale, epsilon)


class TestDetectCollinearity:
    """Tests for the detect_collinearity function."""

    def test_no_collinearity(self):
        """Test with orthogonal predictors."""
        X = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0]
        ])
        
        drop_indices, messages = detect_collinearity(X)
        
        assert len(drop_indices) == 0
        assert any("No significant collinearity" in msg for msg in messages)

    def test_perfect_collinearity(self):
        """Test with perfectly collinear predictors."""
        X = np.array([
            [1.0, 1.0],
            [2.0, 2.0],
            [3.0, 3.0]
        ])
        
        drop_indices, messages = detect_collinearity(X)
        
        # Should detect collinearity and suggest dropping one
        assert len(drop_indices) > 0
        assert any("High condition number" in msg for msg in messages)

    def test_underdetermined_system(self):
        """Test with more features than samples."""
        X = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0]
        ])
        
        drop_indices, messages = detect_collinearity(X)
        
        assert len(drop_indices) > 0
        assert any("Underdetermined system" in msg for msg in messages)

    def test_single_feature(self):
        """Test with only one feature."""
        X = np.array([[1.0], [2.0], [3.0]])
        
        drop_indices, messages = detect_collinearity(X)
        
        assert len(drop_indices) == 0
        assert any("Only one predictor" in msg for msg in messages)


class TestEnforceMinSampleSize:
    """Tests for the enforce_min_sample_size function."""

    def test_valid_sample_size(self):
        """Test with sample size above minimum."""
        is_valid, msg = enforce_min_sample_size(15, min_size=10)
        
        assert is_valid
        assert "meets minimum threshold" in msg

    def test_invalid_sample_size(self):
        """Test with sample size below minimum."""
        is_valid, msg = enforce_min_sample_size(5, min_size=10)
        
        assert not is_valid
        assert "below minimum threshold" in msg

    def test_raise_on_fail(self):
        """Test that ValueError is raised when raise_on_fail is True."""
        with pytest.raises(ValueError, match="below minimum"):
            enforce_min_sample_size(5, min_size=10, raise_on_fail=True)


class TestValidateCovarianceMatrix:
    """Tests for the validate_covariance_matrix function."""

    def test_valid_covariance(self):
        """Test with a valid positive semi-definite matrix."""
        cov = np.array([[2.0, 1.0], [1.0, 2.0]])
        
        is_valid, msg = validate_covariance_matrix(cov)
        
        assert is_valid
        assert "positive semi-definite" in msg

    def test_invalid_covariance(self):
        """Test with a non-positive semi-definite matrix."""
        cov = np.array([[1.0, 2.0], [2.0, 1.0]])  # Eigenvalues: 3, -1
        
        is_valid, msg = validate_covariance_matrix(cov)
        
        assert not is_valid
        assert "not positive semi-definite" in msg

    def test_non_square_matrix(self):
        """Test with a non-square matrix."""
        cov = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        
        is_valid, msg = validate_covariance_matrix(cov)
        
        assert not is_valid
        assert "must be square" in msg


class TestHandleZeroVariance:
    """Tests for the handle_zero_variance function."""

    def test_non_zero_variance(self):
        """Test with data having non-zero variance."""
        data = np.array([1.0, 2.0, 3.0, 4.0])
        
        processed, status = handle_zero_variance(data, epsilon=0.5)
        
        np.testing.assert_array_equal(processed, data)
        assert "non-zero" in status

    def test_zero_variance(self):
        """Test with constant data."""
        data = np.array([5.0, 5.0, 5.0])
        
        processed, status = handle_zero_variance(data, epsilon=0.5)
        
        # Processed data should be different due to added noise
        assert not np.array_equal(processed, data)
        assert "Zero variance" in status


class TestGetEdgeCaseStatus:
    """Tests for the get_edge_case_status function."""

    def test_all_valid(self):
        """Test with a condition that has no edge cases."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        noise_scale = 0.1
        epsilon = 1.0
        
        status = get_edge_case_status(data, noise_scale, epsilon)
        
        assert status["overall_valid"]
        assert not status["clamp_noise"]["was_clamped"]
        assert status["min_sample_size"]["is_valid"]

    def test_multiple_issues(self):
        """Test with multiple edge cases present."""
        data = np.array([1.0, 2.0, 3.0])  # Small sample, potential noise issues
        noise_scale = 100.0  # Very large noise
        epsilon = 0.001
        
        status = get_edge_case_status(data, noise_scale, epsilon)
        
        assert not status["overall_valid"]
        assert status["clamp_noise"]["was_clamped"]
        assert not status["min_sample_size"]["is_valid"]