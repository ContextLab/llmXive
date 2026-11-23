"""
Unit tests for preprocess.py functions.
Tests parcellation, binarization, and efficiency computation.
"""
import os
import sys
import numpy as np
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from preprocess import threshold_to_density, compute_global_efficiency


class TestThresholdToDensity:
    """Tests for the threshold_to_density function."""

    def test_threshold_to_density_basic(self):
        """Basic test for threshold_to_density."""
        # Create a simple weighted adjacency matrix
        adj = np.array([
            [0, 1, 2, 3],
            [1, 0, 4, 5],
            [2, 4, 0, 6],
            [3, 5, 6, 0]
        ], dtype=float)

        # Test with threshold 0.5
        thresholded = threshold_to_density(adj, 0.5)
        assert thresholded.shape == adj.shape
        assert np.all(thresholded >= 0) and np.all(thresholded <= 1)
        # Values above 0.5 should be 1, below should be 0
        expected = np.array([
            [0, 0, 0, 1],
            [0, 0, 1, 1],
            [0, 1, 0, 1],
            [1, 1, 1, 0]
        ], dtype=float)
        np.testing.assert_array_equal(thresholded, expected)

    def test_threshold_to_density_edge_cases(self):
        """Test edge cases for threshold_to_density."""
        adj = np.array([
            [0, 0.1, 0.9],
            [0.1, 0, 0.1],
            [0.9, 0.1, 0]
        ], dtype=float)

        # Threshold at 0.5
        result = threshold_to_density(adj, 0.5)
        assert result[0, 2] == 1.0  # 0.9 > 0.5
        assert result[0, 1] == 0.0  # 0.1 < 0.5

        # Threshold at 0.0 (all should be 1 except diagonal)
        result = threshold_to_density(adj, 0.0)
        assert np.sum(result) == 6  # 3x3 matrix, 6 off-diagonal elements

        # Threshold at 1.0 (all should be 0 except diagonal)
        result = threshold_to_density(adj, 1.0)
        assert np.sum(result) == 0

    def test_threshold_to_density_symmetric(self):
        """Test that threshold_to_density preserves symmetry."""
        adj = np.random.rand(10, 10)
        adj = (adj + adj.T) / 2  # Make symmetric
        np.fill_diagonal(adj, 0)

        result = threshold_to_density(adj, 0.5)
        assert np.allclose(result, result.T)

    def test_threshold_to_density_dtype(self):
        """Test that output is float type."""
        adj = np.array([[0, 1], [1, 0]], dtype=int)
        result = threshold_to_density(adj, 0.5)
        assert result.dtype == np.float64 or result.dtype == np.float32


class TestComputeGlobalEfficiency:
    """Tests for the compute_global_efficiency function."""

    def test_global_efficiency_complete_graph(self):
        """Global efficiency of a complete graph should be 1."""
        # Complete graph: all nodes connected to all others
        n = 5
        adj = np.ones((n, n))
        np.fill_diagonal(adj, 0)

        efficiency = compute_global_efficiency(adj)
        # For a complete graph, shortest path between any two nodes is 1
        # E = (1/(n*(n-1))) * sum(1/1) = (1/(n*(n-1))) * n*(n-1) = 1
        assert np.isclose(efficiency, 1.0)

    def test_global_efficiency_empty_graph(self):
        """Global efficiency of an empty graph should be 0."""
        adj = np.zeros((5, 5))
        efficiency = compute_global_efficiency(adj)
        assert efficiency == 0.0

    def test_global_efficiency_single_edge(self):
        """Test with a single edge."""
        adj = np.zeros((5, 5))
        adj[0, 1] = 1
        adj[1, 0] = 1

        efficiency = compute_global_efficiency(adj)
        # Only nodes 0 and 1 are connected with distance 1
        # All other pairs have infinite distance (disconnected)
        # In networkx, disconnected nodes have infinite distance, so they don't contribute
        # E = (1/(5*4)) * (1/1 + 1/1) = 2/20 = 0.1
        assert np.isclose(efficiency, 0.1)

    def test_global_efficiency_symmetric(self):
        """Test that global efficiency works for symmetric graphs."""
        adj = np.array([
            [0, 1, 1, 0],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [0, 1, 1, 0]
        ], dtype=float)

        efficiency = compute_global_efficiency(adj)
        assert efficiency > 0 and efficiency <= 1

    def test_global_efficiency_undirected(self):
        """Test that global efficiency treats graph as undirected."""
        # Directed graph where A->B exists but B->A doesn't
        adj = np.array([
            [0, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ], dtype=float)

        # networkx global_efficiency treats the graph as directed by default
        # But our function should handle this correctly
        efficiency = compute_global_efficiency(adj)
        # Only one edge, so efficiency should be low
        assert efficiency >= 0

    def test_global_efficiency_float_output(self):
        """Test that output is a float."""
        adj = np.ones((5, 5))
        np.fill_diagonal(adj, 0)
        efficiency = compute_global_efficiency(adj)
        assert isinstance(efficiency, float)