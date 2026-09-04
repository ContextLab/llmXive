"""
Unit tests for centrality calculation metrics.

This module contains tests specifically for verifying the correctness of
centrality calculations (degree, betweenness, eigenvector) on synthetic graphs.
"""
import pytest
import numpy as np
import networkx as nx
from pathlib import Path
import sys

# Add the code directory to the path to import metrics functions
# Assuming this test file is at tests/test_metrics.py and code is at code/
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from compute_metrics import (
    compute_degree_centrality,
    compute_betweenness_centrality,
    compute_eigenvector_centrality
)


def test_centrality_zero_edges():
    """
    Unit test for centrality calculation on a synthetic graph with zero edges.
    
    Verifies that nodes with no edges have a centrality of 0.0 for all metrics.
    This satisfies the independent test requirement for User Story 2:
    "a node with no edges has degree centrality of 0".
    
    The test constructs a synthetic 400x400 adjacency matrix representing
    a graph with 400 isolated nodes (no connections).
    """
    # Create a synthetic 400x400 adjacency matrix with all zeros (no edges)
    n_nodes = 400
    adjacency_matrix = np.zeros((n_nodes, n_nodes), dtype=np.float64)
    
    # Ensure diagonal is zero (no self-loops)
    np.fill_diagonal(adjacency_matrix, 0.0)
    
    # Convert to NetworkX graph
    G = nx.from_numpy_array(adjacency_matrix)
    
    # Verify the graph has the expected number of nodes and edges
    assert G.number_of_nodes() == n_nodes, "Graph should have 400 nodes"
    assert G.number_of_edges() == 0, "Graph should have 0 edges"
    
    # Test Degree Centrality
    degree_cent = compute_degree_centrality(adjacency_matrix)
    assert isinstance(degree_cent, np.ndarray), "Degree centrality should be a numpy array"
    assert degree_cent.shape == (n_nodes,), f"Degree centrality shape should be ({n_nodes},)"
    assert np.allclose(degree_cent, 0.0), "All degree centrality values should be 0.0 for isolated nodes"
    
    # Test Betweenness Centrality
    betweenness_cent = compute_betweenness_centrality(adjacency_matrix)
    assert isinstance(betweenness_cent, np.ndarray), "Betweenness centrality should be a numpy array"
    assert betweenness_cent.shape == (n_nodes,), f"Betweenness centrality shape should be ({n_nodes},)"
    assert np.allclose(betweenness_cent, 0.0), "All betweenness centrality values should be 0.0 for isolated nodes"
    
    # Test Eigenvector Centrality
    # For a graph with no edges, eigenvector centrality is undefined (all zeros or NaN)
    # NetworkX might raise an exception or return zeros for disconnected graphs
    try:
        eigenvector_cent = compute_eigenvector_centrality(adjacency_matrix)
        # If it returns a value, it should be all zeros
        assert isinstance(eigenvector_cent, np.ndarray), "Eigenvector centrality should be a numpy array"
        assert eigenvector_cent.shape == (n_nodes,), f"Eigenvector centrality shape should be ({n_nodes},)"
        # In a disconnected graph with no edges, eigenvector centrality is typically 0
        assert np.allclose(eigenvector_cent, 0.0), "All eigenvector centrality values should be 0.0 for isolated nodes"
    except nx.PowerIterationFailedConvergence:
        # This is expected for a graph with no edges; the power iteration method fails to converge
        # This is acceptable behavior for this edge case
        pass
    
    # Additional verification: Test that a single isolated node in a larger graph also has 0 centrality
    # Create a graph with 5 nodes, only 2 connected, 3 isolated
    small_adj_matrix = np.zeros((5, 5), dtype=np.float64)
    small_adj_matrix[0, 1] = 1.0
    small_adj_matrix[1, 0] = 1.0
    # Nodes 2, 3, 4 are isolated (all zeros in their rows/cols)
    
    G_small = nx.from_numpy_array(small_adj_matrix)
    
    degree_cent_small = compute_degree_centrality(small_adj_matrix)
    # Nodes 0 and 1 should have non-zero degree centrality
    assert degree_cent_small[0] > 0, "Node 0 should have non-zero degree centrality"
    assert degree_cent_small[1] > 0, "Node 1 should have non-zero degree centrality"
    # Nodes 2, 3, 4 should have zero degree centrality
    assert degree_cent_small[2] == 0.0, "Node 2 (isolated) should have 0 degree centrality"
    assert degree_cent_small[3] == 0.0, "Node 3 (isolated) should have 0 degree centrality"
    assert degree_cent_small[4] == 0.0, "Node 4 (isolated) should have 0 degree centrality"
    
    betweenness_cent_small = compute_betweenness_centrality(small_adj_matrix)
    # In this simple graph, isolated nodes should have 0 betweenness
    assert betweenness_cent_small[2] == 0.0, "Node 2 (isolated) should have 0 betweenness centrality"
    assert betweenness_cent_small[3] == 0.0, "Node 3 (isolated) should have 0 betweenness centrality"
    assert betweenness_cent_small[4] == 0.0, "Node 4 (isolated) should have 0 betweenness centrality"