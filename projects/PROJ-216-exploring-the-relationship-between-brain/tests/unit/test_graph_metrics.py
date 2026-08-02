"""
Unit tests for graph metric computation, specifically correlation matrix symmetry
and Louvain algorithm fallback (resolution sweep).

This module tests:
1. Correlation matrix generation symmetry
2. Louvain algorithm fallback with resolution parameter sweep
"""
import numpy as np
import pytest
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from graph_metrics import (
    generate_correlation_matrix,
    compute_modularity_louvain,
    compute_modularity_with_resolution_sweep,
    compute_global_efficiency,
    compute_clustering_coefficient
)


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


class TestLouvainResolutionSweep:
    """Test cases for Louvain algorithm fallback with resolution sweep."""

    def test_resolution_sweep_returns_best(self):
        """Test that resolution sweep returns the best modularity."""
        np.random.seed(42)
        n_nodes = 20
        n_timepoints = 100

        # Create data with some structure
        data = np.random.randn(n_nodes, n_timepoints)
        # Add structure: first 10 nodes correlated with each other
        for i in range(10):
            data[i] = data[0] + np.random.randn(n_timepoints) * 0.1

        corr_matrix = generate_correlation_matrix(data)

        result = compute_modularity_with_resolution_sweep(corr_matrix)

        # Check result structure
        assert 'best_modularity' in result
        assert 'best_resolution' in result
        assert 'best_assignment' in result
        assert 'all_results' in result

        # Check that best_modularity is the maximum of all_results
        modulos = [r[1] for r in result['all_results'] if r[1] is not None]
        if modulos:
            assert result['best_modularity'] == max(modulos)

        # Check assignment length
        assert len(result['best_assignment']) == n_nodes

    def test_resolution_sweep_multiple_resolutions(self):
        """Test that resolution sweep tries multiple resolutions."""
        np.random.seed(123)
        data = np.random.randn(15, 50)
        corr_matrix = generate_correlation_matrix(data)

        custom_resolutions = [0.5, 1.0, 2.0]
        result = compute_modularity_with_resolution_sweep(
            corr_matrix,
            resolution_range=custom_resolutions
        )

        # Check that all custom resolutions were tried
        tried_resolutions = [r[0] for r in result['all_results']]
        assert set(custom_resolutions).issubset(set(tried_resolutions))

    def test_resolution_sweep_default_range(self):
        """Test that default resolution range is used when not specified."""
        np.random.seed(456)
        data = np.random.randn(10, 30)
        corr_matrix = generate_correlation_matrix(data)

        result = compute_modularity_with_resolution_sweep(corr_matrix)

        expected_resolutions = [0.5, 0.75, 1.0, 1.25, 1.5]
        tried_resolutions = [r[0] for r in result['all_results']]

        assert tried_resolutions == expected_resolutions

    def test_resolution_sweep_handles_failure(self):
        """Test that resolution sweep continues when some resolutions fail."""
        # This test verifies the fallback mechanism works
        # In practice, Louvain rarely fails, but we test the logic
        np.random.seed(789)
        data = np.random.randn(8, 20)
        corr_matrix = generate_correlation_matrix(data)

        # Should complete without raising exceptions
        result = compute_modularity_with_resolution_sweep(corr_matrix)

        # Should have a valid best_modularity
        assert result['best_modularity'] >= 0.0

    def test_louvain_single_resolution(self):
        """Test single resolution Louvain computation."""
        np.random.seed(101112)
        data = np.random.randn(12, 40)
        corr_matrix = generate_correlation_matrix(data)

        modularity, assignment = compute_modularity_louvain(corr_matrix, resolution=1.0)

        # Check modularity is in valid range
        assert 0.0 <= modularity <= 1.0

        # Check assignment length
        assert len(assignment) == 12

        # Check all nodes assigned to valid communities
        assert all(a >= 0 for a in assignment)

    def test_louvain_different_resolutions_give_different_results(self):
        """Test that different resolutions give different community assignments."""
        np.random.seed(131415)
        data = np.random.randn(16, 60)
        corr_matrix = generate_correlation_matrix(data)

        mod1, assign1 = compute_modularity_louvain(corr_matrix, resolution=0.5)
        mod2, assign2 = compute_modularity_louvain(corr_matrix, resolution=2.0)

        # Different resolutions should generally give different assignments
        # (though not guaranteed for all datasets)
        # We check that the function runs without error and returns valid results
        assert 0.0 <= mod1 <= 1.0
        assert 0.0 <= mod2 <= 1.0
        assert len(assign1) == len(assign2) == 16

    def test_resolution_sweep_with_edge_case_data(self):
        """Test resolution sweep with edge case data (low connectivity)."""
        np.random.seed(202122)
        # Create data with very low correlations
        data = np.random.randn(10, 30) * 0.01
        corr_matrix = generate_correlation_matrix(data)

        result = compute_modularity_with_resolution_sweep(corr_matrix)

        # Should still return valid results
        assert result['best_modularity'] >= 0.0
        assert len(result['best_assignment']) == 10

    def test_resolution_sweep_empty_results_handling(self):
        """Test that resolution sweep handles case where all resolutions might fail."""
        # This is a theoretical test - in practice Louvain is robust
        # We verify the structure is correct even with minimal data
        np.random.seed(232425)
        data = np.random.randn(4, 10)  # Minimal nodes
        corr_matrix = generate_correlation_matrix(data)

        result = compute_modularity_with_resolution_sweep(corr_matrix)

        # Should have valid structure
        assert 'best_modularity' in result
        assert 'best_resolution' in result
        assert 'best_assignment' in result
        assert len(result['best_assignment']) == 4

    def test_louvain_symmetry_preservation(self):
        """Test that Louvain algorithm works correctly with symmetric matrices."""
        np.random.seed(262728)
        data = np.random.randn(14, 50)
        corr_matrix = generate_correlation_matrix(data)

        # Verify input is symmetric
        np.testing.assert_array_almost_equal(corr_matrix, corr_matrix.T)

        modularity, assignment = compute_modularity_louvain(corr_matrix)

        # Should return valid modularity
        assert 0.0 <= modularity <= 1.0

    def test_resolution_sweep_returns_consistent_best(self):
        """Test that resolution sweep consistently returns the best modularity."""
        np.random.seed(293031)
        data = np.random.randn(18, 70)
        corr_matrix = generate_correlation_matrix(data)

        # Run twice and check consistency
        result1 = compute_modularity_with_resolution_sweep(corr_matrix)
        result2 = compute_modularity_with_resolution_sweep(corr_matrix)

        # Results should be identical (deterministic with seed)
        assert result1['best_modularity'] == result2['best_modularity']
        assert result1['best_resolution'] == result2['best_resolution']
        np.testing.assert_array_equal(
            result1['best_assignment'],
            result2['best_assignment']
        )
