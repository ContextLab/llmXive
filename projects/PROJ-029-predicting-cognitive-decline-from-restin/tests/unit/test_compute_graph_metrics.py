"""Unit tests for the graph‑metric computation utilities."""

import pathlib
import numpy as np
import pandas as pd

from code import utils
from code.utils.graph import (
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_local_efficiency,
    calculate_shortest_path_length,
)

# Simple synthetic adjacency matrix for a small complete graph (3 nodes)
# This is only used to sanity‑check the helper functions – the main script
# works on real data and is exercised in the integration tests.
SIMPLE_MATRIX = np.array(
    [
        [0.0, 1.0, 1.0],
        [1.0, 0.0, 1.0],
        [1.0, 1.0, 0.0],
    ]
)


def test_degree_centrality():
    G = utils.graph.create_graph_from_adjacency(SIMPLE_MATRIX)
    deg = calculate_degree_centrality(G)
    # In a complete graph of 3 nodes each node has degree 2.
    assert all(v == 2 for v in deg.values())


def test_global_efficiency():
    G = utils.graph.create_graph_from_adjacency(SIMPLE_MATRIX)
    eff = calculate_global_efficiency(G)
    # For a complete graph the global efficiency is 1.0
    assert abs(eff - 1.0) < 1e-6


def test_clustering_coefficient():
    G = utils.graph.create_graph_from_adjacency(SIMPLE_MATRIX)
    cc = calculate_clustering_coefficient(G)
    # Complete graph clustering coefficient is 1.0
    assert abs(cc - 1.0) < 1e-6


def test_local_efficiency():
    G = utils.graph.create_graph_from_adjacency(SIMPLE_MATRIX)
    le = calculate_local_efficiency(G)
    # For a complete graph local efficiency equals global efficiency
    assert abs(le - 1.0) < 1e-6


def test_shortest_path_length():
    G = utils.graph.create_graph_from_adjacency(SIMPLE_MATRIX)
    spl = calculate_shortest_path_length(G)
    # In a complete graph the shortest path between distinct nodes is 1
    assert abs(spl - 1.0) < 1e-6