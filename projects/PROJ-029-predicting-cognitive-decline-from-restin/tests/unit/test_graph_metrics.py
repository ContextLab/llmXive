"""Unit tests for the graph‑metric computation helpers."""

import numpy as np
import pytest

from utils.graph import (
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_shortest_path_length,
    create_graph_from_adjacency,
)


@pytest.fixture
def simple_matrix():
    """A tiny 3‑node fully‑connected weighted adjacency matrix."""
    return np.array(
        [
            [0.0, 1.0, 0.5],
            [1.0, 0.0, 0.2],
            [0.5, 0.2, 0.0],
        ]
    )


def test_create_graph(simple_matrix):
    G = create_graph_from_adjacency(simple_matrix)
    assert G.number_of_nodes() == 3
    # Fully connected undirected graph => 3 edges
    assert G.number_of_edges() == 3


def test_degree_centrality(simple_matrix):
    G = create_graph_from_adjacency(simple_matrix)
    deg = calculate_degree_centrality(G)
    # Degree centrality for undirected graph = degree / (n-1)
    expected = {0: 2 / 2, 1: 2 / 2, 2: 2 / 2}
    for n in deg:
        assert pytest.approx(deg[n]) == expected[n]


def test_global_efficiency(simple_matrix):
    G = create_graph_from_adjacency(simple_matrix)
    eff = calculate_global_efficiency(G)
    # For a fully connected 3‑node graph, global efficiency = 1.0
    assert pytest.approx(eff) == 1.0


def test_clustering_coefficient(simple_matrix):
    G = create_graph_from_adjacency(simple_matrix)
    clust = calculate_clustering_coefficient(G)
    # Fully connected triangle => clustering coefficient 1 for each node
    for v in clust.values():
        assert pytest.approx(v) == 1.0


def test_shortest_path_length(simple_matrix):
    G = create_graph_from_adjacency(simple_matrix)
    spl = calculate_shortest_path_length(G)
    # Direct connections => shortest path = 1 for each pair
    for v in spl.values():
        assert pytest.approx(v) == 1.0