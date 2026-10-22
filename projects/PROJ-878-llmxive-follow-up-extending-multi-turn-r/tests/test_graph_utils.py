import pytest
import networkx as nx
from code.utils.graph_utils import (
    is_dag, nesting_depth, branching_factor, 
    longest_path, get_random_valid_path_different_from_reference
)

def test_acyclicity():
    G_dag = nx.DiGraph([(0, 1), (1, 2)])
    G_cycle = nx.DiGraph([(0, 1), (1, 2), (2, 0)])
    assert is_dag(G_dag) is True
    assert is_dag(G_cycle) is False

def test_metrics():
    G = nx.DiGraph()
    # Path: 0 -> 1 -> 2 -> 3 (Length 4 nodes)
    G.add_edges_from([(0, 1), (1, 2), (2, 3)])
    # Add branching: 0 -> 2
    G.add_edge(0, 2)
    
    assert nesting_depth(G) == 4
    assert longest_path(G) == [0, 1, 2, 3]
    # Non-roots: 1(in=1), 2(in=2), 3(in=1). Avg = 4/3 = 1.333
    assert branching_factor(G) == pytest.approx(1.333, rel=1e-3)

def test_path_perturbation():
    G = nx.DiGraph()
    # Two paths from 0 to 3: [0, 1, 2, 3] and [0, 3]
    G.add_edges_from([(0, 1), (1, 2), (2, 3), (0, 3)])
    ref = [0, 1, 2, 3]
    alt = get_random_valid_path_different_from_reference(G, ref)
    assert alt is not None
    assert alt == [0, 3]
    assert alt != ref