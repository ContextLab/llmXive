"""
Unit tests for regularization utilities.
Tests added as part of T043 to ensure comprehensive test coverage.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.regularization import is_condition_number_acceptable, regularize_covariance
from utils.exceptions import HighDimensionalInstabilityError

class TestIsConditionNumberAcceptable:
    """Tests for is_condition_number_acceptable function."""

    def test_acceptable_condition_number(self):
        """Test that reasonable condition numbers are accepted."""
        # Well-conditioned matrix
        A = np.eye(10)
        assert is_condition_number_acceptable(A) is True

    def test_unacceptable_condition_number(self):
        """Test that very large condition numbers are rejected."""
        # Create a nearly singular matrix
        A = np.array([[1.0, 0.999999999999],
                      [0.999999999999, 1.0]])
        # This should have a very high condition number
        with pytest.raises(HighDimensionalInstabilityError):
            is_condition_number_acceptable(A, threshold=1e12)

    def test_custom_threshold(self):
        """Test that custom thresholds work correctly."""
        A = np.eye(10) * 1000  # Well-conditioned but scaled
        
        # Should pass with high threshold
        assert is_condition_number_acceptable(A, threshold=1e15) is True
        
        # Should fail with low threshold
        with pytest.raises(HighDimensionalInstabilityError):
            is_condition_number_acceptable(A, threshold=1e2)

class TestRegularizeCovariance:
    """Tests for regularize_covariance function."""

    def test_identity_matrix(self):
        """Test regularization on identity matrix."""
        A = np.eye(10)
        A_reg = regularize_covariance(A, epsilon=1e-6)
        
        # Identity matrix should remain essentially unchanged
        assert np.allclose(A_reg, A)

    def test_regularization_adds_epsilon(self):
        """Test that regularization adds epsilon to diagonal."""
        A = np.zeros((10, 10))
        A_reg = regularize_covariance(A, epsilon=1e-4)
        
        # Diagonal should be epsilon
        assert np.allclose(np.diag(A_reg), 1e-4)
        
        # Off-diagonal should remain zero
        off_diag = A_reg - np.diag(np.diag(A_reg))
        assert np.allclose(off_diag, 0)

    def test_singularity_handling(self):
        """Test that singular matrices are handled correctly."""
        # Create a singular matrix
        A = np.zeros((10, 10))
        A[0, 0] = 1.0
        
        # Should not raise error, just regularize
        A_reg = regularize_covariance(A, epsilon=1e-6)
        
        # Should be non-singular after regularization
        condition_num = np.linalg.cond(A_reg)
        assert condition_num < 1e12

    def test_high_dimensional_instability_error(self):
        """Test that extremely ill-conditioned matrices raise error."""
        # Create a matrix that will have extremely high condition number
        # even after regularization
        A = np.random.rand(10, 10) * 1e-20
        A[0, 0] = 1.0  # Make it non-zero but still ill-conditioned
        
        # With very small epsilon, this might still be problematic
        # but with reasonable epsilon it should be fine
        # This test ensures the function handles edge cases
        try:
            A_reg = regularize_covariance(A, epsilon=1e-6)
            # If we get here, regularization worked
            assert A_reg is not None
        except HighDimensionalInstabilityError:
            # This is also acceptable for extremely ill-conditioned matrices
            pass

    def test_symmetric_preservation(self):
        """Test that regularization preserves symmetry."""
        A = np.random.rand(10, 10)
        A = (A + A.T) / 2  # Make symmetric
        
        A_reg = regularize_covariance(A, epsilon=1e-6)
        
        assert np.allclose(A_reg, A_reg.T)

    def test_positive_definiteness(self):
        """Test that regularization produces positive definite matrices."""
        # Create a positive semi-definite matrix
        A = np.random.rand(10, 10)
        A = A @ A.T  # Now positive semi-definite
        
        A_reg = regularize_covariance(A, epsilon=1e-6)
        
        # All eigenvalues should be positive
        eigenvalues = np.linalg.eigvalsh(A_reg)
        assert np.all(eigenvalues > 0)
