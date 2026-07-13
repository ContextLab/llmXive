"""
Unit tests for graph utilities.
"""
import pytest
import numpy as np
from utils.graph import create_graph_from_adjacency, calculate_global_efficiency

def test_create_graph():
    """Test graph creation."""
    adj = np.array([[0, 1], [1, 0]])
    G = create_graph_from_adjacency(adj)
    assert G.number_of_nodes() == 2
    assert G.number_of_edges() == 1

def test_efficiency_complete():
    """Test efficiency on complete graph."""
    adj = np.ones((3, 3))
    np.fill_diagonal(adj, 0)
    eff = calculate_global_efficiency(create_graph_from_adjacency(adj))
    assert np.isclose(eff, 1.0)
