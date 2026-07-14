"""
Unit tests for T019: Graph metrics computation.
Tests the core logic of process_single_subject_matrix without needing full data files.
"""
import pytest
import numpy as np
import networkx as nx
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.graph import calculate_global_efficiency, calculate_clustering_coefficient, calculate_degree_centrality
from code.utils.graph import calculate_shortest_path_length
# We will import the function directly if possible, or mock the logic
# Since process_single_subject_matrix is in 03_compute_graph_metrics, we test the logic
# by replicating the core steps or testing the utils it depends on.

def test_degree_centrality():
    """Test degree centrality calculation on a simple graph."""
    # Create a star graph: one central node connected to 4 others
    G = nx.star_graph(4)
    centrality = calculate_degree_centrality(G)
    # Central node should have centrality 1.0 (connected to all 4 others out of 4 possible)
    # Others should have centrality 0.25 (connected to 1 out of 4)
    assert abs(centrality[0] - 1.0) < 1e-6
    for i in range(1, 5):
        assert abs(centrality[i] - 0.25) < 1e-6

def test_global_efficiency():
    """Test global efficiency calculation."""
    # Complete graph of 4 nodes: efficiency should be 1.0
    G = nx.complete_graph(4)
    eff = calculate_global_efficiency(G)
    assert abs(eff - 1.0) < 1e-6
    
    # Path graph: efficiency should be lower
    G_path = nx.path_graph(4)
    eff_path = calculate_global_efficiency(G_path)
    assert 0 < eff_path < 1.0

def test_clustering_coefficient():
    """Test clustering coefficient calculation."""
    # Triangle graph: clustering coefficient should be 1.0
    G = nx.complete_graph(3)
    clustering = calculate_clustering_coefficient(G)
    assert abs(clustering - 1.0) < 1e-6
    
    # Star graph: central node has 0 clustering (neighbors not connected), leaves have 0
    G_star = nx.star_graph(4)
    clustering_star = calculate_clustering_coefficient(G_star)
    assert clustering_star == 0.0

def test_shortest_path_length():
    """Test average shortest path length."""
    # Complete graph: average path length is 1.0
    G = nx.complete_graph(4)
    avg_len = nx.average_shortest_path_length(G)
    assert abs(avg_len - 1.0) < 1e-6
    
    # Path graph 1-2-3-4: average path length is (1+2+3+1+2+1)/6 = 10/6 = 1.666...
    G_path = nx.path_graph(4)
    avg_len_path = nx.average_shortest_path_length(G_path)
    assert abs(avg_len_path - 1.6666666666666667) < 1e-5

def test_symmetrization():
    """Test that asymmetric matrices are symmetrized correctly."""
    # Create an asymmetric matrix
    A = np.array([[0, 1, 2], [0, 0, 3], [0, 0, 0]], dtype=float)
    # Symmetrize
    A_sym = (A + A.T) / 2.0
    expected = np.array([[0, 0.5, 1], [0.5, 0, 1.5], [1, 1.5, 0]], dtype=float)
    assert np.allclose(A_sym, expected)

def test_disconnected_graph_handling():
    """Test that disconnected graphs are handled by using largest component."""
    # Create a graph with two disconnected components
    G = nx.Graph()
    G.add_edges_from([(1, 2), (2, 3)]) # Component 1
    G.add_edges_from([(4, 5)])        # Component 2
    
    # Largest component is {1, 2, 3}
    largest_cc = max(nx.connected_components(G), key=len)
    G_largest = G.subgraph(largest_cc).copy()
    
    assert len(G_largest.nodes()) == 3
    assert nx.is_connected(G_largest)

def test_matrix_to_graph_conversion():
    """Test conversion of numpy matrix to networkx graph."""
    # 3x3 identity matrix (no edges)
    A = np.eye(3)
    G = nx.from_numpy_array(A)
    assert G.number_of_edges() == 0
    
    # Complete graph adjacency (0 on diag, 1 elsewhere)
    A_complete = np.ones((3, 3)) - np.eye(3)
    G_complete = nx.from_numpy_array(A_complete)
    assert G_complete.number_of_edges() == 3 # (3*2)/2
    assert nx.is_connected(G_complete)