import pytest
import numpy as np
import networkx as nx
import pandas as pd
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.graph_metrics import calculate_path_length

class TestCalculatePathLength:
    """
    Unit tests for calculate_path_length function.
    Uses synthetic small matrices to verify correctness.
    """

    def test_path_length_complete_graph(self):
        """
        Test on a complete graph (fully connected).
        For a complete graph with N nodes, the shortest path between
        any two distinct nodes is 1.
        The average shortest path length should be 1.0.
        """
        n = 5
        # Create a correlation matrix where all off-diagonal elements are high (0.9)
        # representing strong connections.
        matrix = np.ones((n, n)) * 0.9
        np.fill_diagonal(matrix, 1.0)

        # Convert to DataFrame as expected by the function
        df = pd.DataFrame(matrix)

        result = calculate_path_length(df)

        # For a complete weighted graph with positive weights,
        # the shortest path between any two nodes is the direct edge.
        # Since we use weights as distances (1 - correlation),
        # and all correlations are 0.9, distance is 0.1.
        # Average path length should be 0.1.
        # However, networkx average_shortest_path_length uses unweighted by default if not specified,
        # but we pass weight='weight'.
        # Let's verify the logic: distance = 1 - 0.9 = 0.1.
        # All pairs are directly connected with 0.1.
        # Average = 0.1.
        assert np.isclose(result, 0.1), f"Expected 0.1, got {result}"

    def test_path_length_disconnected_graph(self):
        """
        Test on a graph where some nodes are disconnected.
        NetworkX average_shortest_path_length raises NetworkXPointlessConcept
        for completely disconnected graphs or infinity for disconnected components.
        The function should handle this gracefully or return a specific value.
        """
        n = 4
        # Create a matrix with no connections (0 correlation) except diagonal
        matrix = np.zeros((n, n))
        np.fill_diagonal(matrix, 1.0)

        df = pd.DataFrame(matrix)

        # This should result in infinite path length or an error depending on implementation
        # We expect the function to handle this by returning np.inf or raising a specific exception
        # For this test, we assume the function returns np.inf for disconnected components
        result = calculate_path_length(df)
        
        # If the implementation filters for connected graphs, it might return NaN or 0
        # If it calculates on the largest component, it might be 0 (single nodes)
        # If it tries to calculate on disconnected, it raises.
        # Let's assume the function returns np.inf for disconnected graphs as per standard graph theory.
        assert np.isinf(result), f"Expected inf for disconnected graph, got {result}"

    def test_path_length_small_ring(self):
        """
        Test on a small ring graph (cycle).
        Nodes 0-1-2-3-0.
        Distances:
        0-1: 0.1 (correlation 0.9)
        0-2: 0.2 (path 0-1-2, 0.1+0.1)
        0-3: 0.1 (direct 0-3 correlation 0.9)
        ...
        """
        n = 4
        matrix = np.zeros((n, n))
        np.fill_diagonal(matrix, 1.0)
        
        # Define connections for a ring: 0-1, 1-2, 2-3, 3-0
        connections = [(0, 1), (1, 2), (2, 3), (3, 0)]
        for i, j in connections:
            matrix[i, j] = 0.9
            matrix[j, i] = 0.9

        df = pd.DataFrame(matrix)
        result = calculate_path_length(df)

        # Calculate expected average shortest path manually
        # Distances (weights = 1 - 0.9 = 0.1):
        # 0-1: 0.1
        # 0-2: min(0-1-2: 0.2, 0-3-2: 0.2) = 0.2
        # 0-3: 0.1
        # 1-2: 0.1
        # 1-3: 0.2
        # 2-3: 0.1
        # Total pairs: 4*3 = 12 directed pairs (or 6 undirected)
        # Sum of distances (undirected): 0.1 + 0.2 + 0.1 + 0.1 + 0.2 + 0.1 = 0.8
        # Average (undirected): 0.8 / 6 = 0.1333...
        # Average (directed): 1.6 / 12 = 0.1333...
        expected = 0.8 / 6
        assert np.isclose(result, expected, atol=1e-5), f"Expected {expected}, got {result}"

    def test_path_length_unchanged_by_node_order(self):
        """
        Verify that permuting the nodes (shuffling rows/cols) does not change the result.
        """
        n = 5
        matrix = np.random.rand(n, n)
        matrix = (matrix + matrix.T) / 2
        np.fill_diagonal(matrix, 1.0)
        
        df_original = pd.DataFrame(matrix)
        result_original = calculate_path_length(df_original)

        # Shuffle indices
        indices = np.random.permutation(n)
        matrix_shuffled = matrix[np.ix_(indices, indices)]
        df_shuffled = pd.DataFrame(matrix_shuffled)

        result_shuffled = calculate_path_length(df_shuffled)

        assert np.isclose(result_original, result_shuffled), \
            f"Path length changed after permutation: {result_original} vs {result_shuffled}"

    def test_path_length_single_node(self):
        """
        Test with a single node. Path length is undefined or 0.
        """
        matrix = np.array([[1.0]])
        df = pd.DataFrame(matrix)
        
        # Should handle gracefully, likely returning 0 or NaN
        result = calculate_path_length(df)
        # We expect 0 or NaN, but not an exception
        assert result == 0.0 or np.isnan(result), f"Unexpected result for single node: {result}"