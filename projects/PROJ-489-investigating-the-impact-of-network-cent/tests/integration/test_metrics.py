import pytest
import numpy as np
import sys
import os

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from metrics import validate_connectivity_matrix, compute_waking_connectivity

class TestConnectivityMatrixValidation:
    """Integration tests for connectivity matrix validation (T023)."""

    def test_symmetric_matrix_valid(self):
        """Test that a symmetric matrix with values in (0, 1) passes validation."""
        # Create a symmetric matrix
        n = 5
        matrix = np.random.rand(n, n)
        matrix = (matrix + matrix.T) / 2
        
        # Ensure off-diagonal values are strictly between 0 and 1
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i, j] = np.clip(matrix[i, j], 0.01, 0.99)
        
        # Set diagonal to 1.0
        np.fill_diagonal(matrix, 1.0)
        
        result = validate_connectivity_matrix(matrix)
        
        assert result['is_symmetric'] is True
        assert result['values_in_range'] is True
        assert result['is_valid'] is True

    def test_asymmetric_matrix_fails(self):
        """Test that an asymmetric matrix fails validation."""
        n = 5
        matrix = np.random.rand(n, n)
        # Make it asymmetric
        matrix[0, 1] = 0.5
        matrix[1, 0] = 0.6
        
        result = validate_connectivity_matrix(matrix)
        
        assert result['is_symmetric'] is False
        assert result['is_valid'] is False

    def test_values_outside_range_fails(self):
        """Test that a matrix with values outside (0, 1) fails validation."""
        n = 5
        matrix = np.ones((n, n))
        matrix[0, 1] = 1.5  # Value > 1
        
        result = validate_connectivity_matrix(matrix)
        
        assert result['values_in_range'] is False
        assert result['is_valid'] is False

    def test_diagonal_not_one_fails(self):
        """Test that a matrix with diagonal not equal to 1 fails validation."""
        n = 5
        matrix = np.eye(n) * 0.5  # Diagonal is 0.5, not 1.0
        
        result = validate_connectivity_matrix(matrix)
        
        assert result['values_in_range'] is False
        assert result['is_valid'] is False

    def test_values_exactly_zero_or_one_fails(self):
        """Test that off-diagonal values exactly 0 or 1 fail validation."""
        n = 5
        matrix = np.ones((n, n)) * 0.5
        matrix[0, 1] = 0.0  # Exactly 0
        matrix[1, 0] = 0.0
        
        result = validate_connectivity_matrix(matrix)
        
        assert result['values_in_range'] is False
        assert result['is_valid'] is False

    def test_realistic_connectivity_matrix(self):
        """Test with a more realistic connectivity matrix structure."""
        n = 10
        # Create a matrix with varying connection strengths
        matrix = np.random.rand(n, n)
        matrix = (matrix + matrix.T) / 2
        
        # Apply a decay based on distance (simulating brain connectivity)
        for i in range(n):
            for j in range(n):
                if i != j:
                    distance = abs(i - j)
                    matrix[i, j] *= np.exp(-0.1 * distance)
                    matrix[i, j] = np.clip(matrix[i, j], 0.01, 0.99)
        
        np.fill_diagonal(matrix, 1.0)
        
        result = validate_connectivity_matrix(matrix)
        
        assert result['is_symmetric'] is True
        assert result['values_in_range'] is True
        assert result['is_valid'] is True