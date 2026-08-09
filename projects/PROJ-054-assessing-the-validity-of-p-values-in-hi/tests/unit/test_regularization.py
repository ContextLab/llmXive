"""
Unit tests for covariance regularization utilities.
Tests for code/utils/regularization.py
"""
import numpy as np
import pytest
from utils.regularization import is_condition_number_acceptable, regularize_covariance
from utils.exceptions import HighDimensionalInstabilityError


class TestConditionNumberCheck:
    def test_well_conditioned_matrix(self):
        """Test that a well-conditioned identity matrix passes."""
        matrix = np.eye(10)
        assert is_condition_number_acceptable(matrix) is True

    def test_moderately_conditioned_matrix(self):
        """Test a matrix with moderate condition number."""
        # Create a matrix with known condition number ~100
        matrix = np.diag([100] + [1] * 9)
        assert is_condition_number_acceptable(matrix) is True

    def test_highly_conditioned_matrix(self):
        """Test a matrix that exceeds the threshold (10^12)."""
        # Create a matrix with very high condition number
        matrix = np.diag([1e13] + [1] * 9)
        assert is_condition_number_acceptable(matrix) is False

    def test_singular_matrix(self):
        """Test a singular matrix (condition number = infinity)."""
        matrix = np.zeros((10, 10))
        assert is_condition_number_acceptable(matrix) is False


class TestRegularizeCovariance:
    def test_identity_matrix_unchanged(self):
        """Test that identity matrix is returned unchanged when already acceptable."""
        matrix = np.eye(5)
        regularized = regularize_covariance(matrix)
        np.testing.assert_array_almost_equal(regularized, matrix)

    def test_regularization_adds_diagonal(self):
        """Test that regularization adds a small value to the diagonal."""
        # Create a nearly singular matrix
        matrix = np.array([[1.0, 0.99], [0.99, 1.0]])
        regularized = regularize_covariance(matrix)

        # Check that diagonal elements increased
        assert regularized[0, 0] > matrix[0, 0]
        assert regularized[1, 1] > matrix[1, 1]

        # Check that off-diagonal elements unchanged
        assert regularized[0, 1] == matrix[0, 1]
        assert regularized[1, 0] == matrix[1, 0]

    def test_high_dimensional_instability_raises(self):
        """Test that extremely ill-conditioned matrices raise an error."""
        # Create a matrix that cannot be regularized within tolerance
        matrix = np.diag([1e20] + [1] * 9)
        with pytest.raises(HighDimensionalInstabilityError):
            regularize_covariance(matrix)

    def test_output_is_symmetric(self):
        """Test that the output matrix is symmetric."""
        matrix = np.random.rand(10, 10)
        matrix = matrix @ matrix.T  # Make it symmetric positive semi-definite
        regularized = regularize_covariance(matrix)

        np.testing.assert_array_almost_equal(regularized, regularized.T)

    def test_output_is_positive_definite(self):
        """Test that the output matrix is positive definite."""
        matrix = np.random.rand(5, 5)
        matrix = matrix @ matrix.T
        # Make it nearly singular
        matrix[0, 0] = 1e-15

        regularized = regularize_covariance(matrix)

        # Check eigenvalues are positive
        eigenvalues = np.linalg.eigvalsh(regularized)
        assert np.all(eigenvalues > 0)

    def test_different_regularization_strengths(self):
        """Test that different lambda values produce different results."""
        matrix = np.array([[1.0, 0.99], [0.99, 1.0]])

        reg_weak = regularize_covariance(matrix, lambda_min=1e-6)
        reg_strong = regularize_covariance(matrix, lambda_min=1e-3)

        # Stronger regularization should add more to diagonal
        assert reg_strong[0, 0] - matrix[0, 0] > reg_weak[0, 0] - matrix[0, 0]

def test_condition_number_threshold_boundary():
    """Test behavior exactly at the threshold boundary."""
    # Create matrix with condition number exactly at 10^12
    # This tests the boundary condition
    matrix = np.diag([1e12] + [1] * 9)
    # Should be acceptable (threshold is > 10^12)
    assert is_condition_number_acceptable(matrix) is True

    # Slightly above threshold
    matrix_above = np.diag([1e12 + 1] + [1] * 9)
    assert is_condition_number_acceptable(matrix_above) is False
