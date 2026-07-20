"""
Unit tests for graph metric computation, specifically correlation matrix symmetry.

This module tests the correlation matrix generation logic to ensure that the
resulting matrices are symmetric, as required by the definition of Pearson correlation.
"""
import numpy as np
import pytest
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from graph_metrics import generate_correlation_matrix


class TestCorrelationMatrixSymmetry:
    """Test cases for correlation matrix symmetry."""

    def test_symmetry_identical_rows(self):
        """Test symmetry when rows are identical (perfect correlation)."""
        # Create a matrix where rows are identical
        data = np.ones((5, 10))
        corr_matrix = generate_correlation_matrix(data)
        
        # Check symmetry
        np.testing.assert_array_almost_equal(corr_matrix, corr_matrix.T)
        
        # Check diagonal is 1.0
        np.testing.assert_array_almost_equal(np.diag(corr_matrix), np.ones(5))

    def test_symmetry_random_data(self):
        """Test symmetry with random data."""
        np.random.seed(42)
        data = np.random.randn(20, 100)
        corr_matrix = generate_correlation_matrix(data)
        
        # Check symmetry
        np.testing.assert_array_almost_equal(corr_matrix, corr_matrix.T)

    def test_symmetry_asymmetric_input(self):
        """Test that the output is symmetric even if input has asymmetry in patterns."""
        np.random.seed(123)
        # Create data with specific patterns
        data = np.random.randn(10, 50)
        data[0] = data[1] * 2  # First row is twice the second
        data[2] = -data[3]     # Third row is negative of fourth
        
        corr_matrix = generate_correlation_matrix(data)
        
        # Check symmetry
        np.testing.assert_array_almost_equal(corr_matrix, corr_matrix.T)

    def test_symmetry_tolerance(self):
        """Test that small floating point differences don't break symmetry check."""
        np.random.seed(456)
        data = np.random.randn(15, 80)
        corr_matrix = generate_correlation_matrix(data)
        
        # Check symmetry within numerical tolerance
        diff = np.abs(corr_matrix - corr_matrix.T)
        assert np.max(diff) < 1e-10, f"Matrix not symmetric within tolerance: max diff = {np.max(diff)}"

    def test_symmetry_small_sample(self):
        """Test symmetry with minimal sample size (just enough for correlation)."""
        np.random.seed(789)
        data = np.random.randn(3, 10)
        corr_matrix = generate_correlation_matrix(data)
        
        # Check symmetry
        np.testing.assert_array_almost_equal(corr_matrix, corr_matrix.T)

    def test_symmetry_single_timepoint_failure(self):
        """Test that correlation fails appropriately with single timepoint."""
        data = np.random.randn(5, 1)
        with pytest.raises(ValueError):
            generate_correlation_matrix(data)

    def test_symmetry_constant_row_handling(self):
        """Test handling of constant rows (should result in NaN or 0 correlation)."""
        data = np.random.randn(5, 20)
        data[0] = 5.0  # Constant row
        corr_matrix = generate_correlation_matrix(data)
        
        # Check symmetry is maintained even with NaN values
        # Note: NaN != NaN, so we check symmetry excluding NaN positions
        is_symmetric = np.allclose(corr_matrix, corr_matrix.T, equal_nan=True)
        assert is_symmetric, "Matrix with constant rows is not symmetric"

    def test_symmetry_shape_preservation(self):
        """Test that output matrix shape matches input node count."""
        np.random.seed(101112)
        n_nodes = 7
        n_timepoints = 30
        data = np.random.randn(n_nodes, n_timepoints)
        corr_matrix = generate_correlation_matrix(data)
        
        assert corr_matrix.shape == (n_nodes, n_nodes), \
            f"Expected shape ({n_nodes}, {n_nodes}), got {corr_matrix.shape}"
        
        # Check symmetry
        np.testing.assert_array_almost_equal(corr_matrix, corr_matrix.T)

    def test_symmetry_deterministic(self):
        """Test that correlation is deterministic for same input."""
        np.random.seed(131415)
        data = np.random.randn(8, 40)
        
        corr1 = generate_correlation_matrix(data)
        corr2 = generate_correlation_matrix(data)
        
        # Check both are symmetric
        np.testing.assert_array_almost_equal(corr1, corr1.T)
        np.testing.assert_array_almost_equal(corr2, corr2.T)
        
        # Check they are identical
        np.testing.assert_array_almost_equal(corr1, corr2)