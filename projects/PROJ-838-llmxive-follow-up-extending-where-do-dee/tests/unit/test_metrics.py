import pytest
import networkx as nx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from metrics import calculate_global_connectivity, calculate_average_branching_factor

def test_calculate_global_connectivity():
    """Unit test for Global Connectivity calculation (T018)."""
    # Test case: 3 nodes, 2 edges
    G = nx.DiGraph()
    G.add_nodes_from([1, 2, 3])
    G.add_edges_from([(1, 2), (2, 3)])
    
    # Expected: 2 / (3 * 2) = 0.3333
    result = calculate_global_connectivity(G)
    assert result == pytest.approx(0.333333, rel=0.01)

    # Test case: 0 edges
    G_empty = nx.DiGraph()
    G_empty.add_nodes_from([1, 2, 3])
    assert calculate_global_connectivity(G_empty) == 0.0

    # Test case: < 2 nodes
    G_small = nx.DiGraph()
    G_small.add_node(1)
    assert calculate_global_connectivity(G_small) == 0.0

    # Test case: Empty graph
    G_none = nx.DiGraph()
    assert calculate_global_connectivity(G_none) == 0.0

def test_calculate_average_branching_factor():
    """Unit test for Average Branching Factor calculation (T019)."""
    # Test case: 3 nodes, edges (1->2), (2->3)
    # Out-degrees: 1:1, 2:1, 3:0 -> Sum=2, Avg=2/3
    G = nx.DiGraph()
    G.add_nodes_from([1, 2, 3])
    G.add_edges_from([(1, 2), (2, 3)])
    
    result = calculate_average_branching_factor(G)
    assert result == pytest.approx(0.666666, rel=0.01)

    # Test case: 0 nodes
    G_empty = nx.DiGraph()
    assert calculate_average_branching_factor(G_empty) == 0.0

    # Test case: Single node, no edges
    G_single = nx.DiGraph()
    G_single.add_node(1)
    assert calculate_average_branching_factor(G_single) == 0.0

def test_edge_cases_small_graphs():
    """
    Unit test for edge cases with small graphs (T055).
    Verifies behavior for N < 2 and N = 2.
    """
    # N=2, 1 edge -> Connectivity = 1 / (2*1) = 0.5
    G_two = nx.DiGraph()
    G_two.add_nodes_from([1, 2])
    G_two.add_edge(1, 2)
    assert calculate_global_connectivity(G_two) == pytest.approx(0.5, rel=0.01)

    # N=2, 0 edges -> Connectivity = 0.0
    G_two_empty = nx.DiGraph()
    G_two_empty.add_nodes_from([1, 2])
    assert calculate_global_connectivity(G_two_empty) == 0.0

    # N=1 -> Connectivity = 0.0
    G_one = nx.DiGraph()
    G_one.add_node(1)
    assert calculate_global_connectivity(G_one) == 0.0