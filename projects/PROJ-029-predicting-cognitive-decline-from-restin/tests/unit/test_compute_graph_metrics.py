"""Unit tests for the graph‑metric computation utilities."""

import numpy as np
import pandas as pd
import pytest

from utils.graph import (
    create_graph_from_adjacency,
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
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


def test_create_graph_from_adjacency(simple_matrix):
    G = create_graph_from_adjacency(simple_matrix)
    assert G.number_of_nodes() == 3
    # Fully connected undirected graph should have 3 edges
    assert G.number_of_edges() == 3


def test_degree_centrality(simple_matrix):
    G = create_graph_from_adjacency(simple_matrix)
    deg = calculate_degree_centrality(G)
    assert isinstance(deg, dict)
    assert len(deg) == 3
    # In a fully connected graph each node degree should be 2 (weighted sum)
    for val in deg.values():
        assert val > 0


def test_global_efficiency(simple_matrix):
    G = create_graph_from_adjacency(simple_matrix)
    eff = calculate_global_efficiency(G)
    assert isinstance(eff, float)
    assert eff > 0


def test_clustering_coefficient(simple_matrix):
    G = create_graph_from_adjacency(simple_matrix)
    coeff = calculate_clustering_coefficient(G)
    assert isinstance(coeff, dict)
    assert len(coeff) == 3


def test_shortest_path_length(simple_matrix):
    G = create_graph_from_adjacency(simple_matrix)
    apl = calculate_shortest_path_length(G)
    assert isinstance(apl, float)
    assert apl > 0