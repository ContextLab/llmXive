"""
Unit tests for utils.graph_utils
"""

import pytest
import networkx as nx

from utils.graph_utils import (
    is_dag,
    nesting_depth,
    branching_factor,
    longest_path,
    get_random_valid_path_different_from_reference,
)

def test_is_dag_true():
    G = nx.DiGraph()
    G.add_edges_from([(1, 2), (2, 3)])
    assert is_dag(G) is True

def test_is_dag_false():
    G = nx.DiGraph()
    G.add_edges_from([(1, 2), (2, 3), (3, 1)])  # creates a cycle
    assert is_dag(G) is False

def test_nesting_depth():
    G = nx.DiGraph()
    G.add_edges_from([(1, 2), (2, 3), (3, 4)])
    # longest path has 4 nodes
    assert nesting_depth(G) == 4

def test_branching_factor():
    G = nx.DiGraph()
    G.add_edges_from([(1, 2), (1, 3), (2, 4), (3, 4)])
    # in-degrees: node1=0, node2=1, node3=1, node4=2 => mean = (0+1+1+2)/4 = 1.0
    assert branching_factor(G) == pytest.approx(1.0)

def test_longest_path():
    G = nx.DiGraph()
    G.add_edges_from([(5, 1), (1, 2), (2, 3), (3, 4)])
    assert longest_path(G) == [5, 1, 2, 3, 4]

def test_get_random_valid_path_different_from_reference():
    G = nx.DiGraph()
    G.add_edges_from([
        (0, 1), (1, 2), (0, 2),  # two distinct paths from 0 to 2
    ])
    reference = [0, 1, 2]
    # The function should find the alternative path [0, 2]
    path = get_random_valid_path_different_from_reference(G, reference, max_attempts=10)
    assert path is not None
    assert path != reference
    # Ensure path is valid
    assert all(G.has_edge(u, v) for u, v in zip(path, path[1:]))
