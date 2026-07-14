"""Unit tests for the graph‑metric computation utilities used by ``03_compute_graph_metrics.py``.\n\nThese tests exercise the metric functions in ``utils.graph`` on a tiny synthetic network.\n"""

from pathlib import Path

import numpy as np
import pytest

from utils.graph import (
    create_graph_from_adjacency,
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)


@pytest.fixture
def tiny_adj_matrix() -> np.ndarray:
    """
    A simple 3‑node fully‑connected weighted graph:\n
    node 0‑1 weight 1,\n
    node 0‑2 weight 2,\n
    node 1‑2 weight 3.\n
    The diagonal is zero.
    """
    return np.array(
        [
            [0, 1, 2],
            [1, 0, 3],
            [2, 3, 0],
        ],
        dtype=float,
    )


def test_create_graph_from_adjacency(tiny_adj_matrix):
    G = create_graph_from_adjacency(tiny_adj_matrix)
    assert G.number_of_nodes() == 3
    # Undirected graph – each edge appears once.
    assert G.number_of_edges() == 3
    # Verify an edge weight.
    assert G[0][1]["weight"] == 1.0


def test_calculate_degree_centrality(tiny_adj_matrix):
    G = create_graph_from_adjacency(tiny_adj_matrix)
    deg = calculate_degree_centrality(G)
    # Degree = sum of incident weights.
    assert pytest.approx(deg[0]) == 3.0  # 1 + 2
    assert pytest.approx(deg[1]) == 4.0  # 1 + 3
    assert pytest.approx(deg[2]) == 5.0  # 2 + 3


def test_calculate_global_efficiency(tiny_adj_matrix):
    G = create_graph_from_adjacency(tiny_adj_matrix)
    eff = calculate_global_efficiency(G)
    # For a fully connected 3‑node graph the global efficiency is 1.
    assert pytest.approx(eff, rel=1e-6) == 1.0


def test_calculate_clustering_coefficient(tiny_adj_matrix):
    G = create_graph_from_adjacency(tiny_adj_matrix)
    clustering = calculate_clustering_coefficient(G)
    # In a triangle each node has clustering coefficient 1.
    for val in clustering.values():
        assert pytest.approx(val) == 1.0


def test_calculate_shortest_path_length(tiny_adj_matrix):
    G = create_graph_from_adjacency(tiny_adj_matrix)
    avg_len = calculate_shortest_path_length(G)
    # In a triangle the shortest path between any two distinct nodes is 1.
    # Average over 3 unordered pairs => 1.0
    assert pytest.approx(avg_len) == 1.0