"""
Unit tests for the graph‑metric computation utilities.
The tests focus on the pure‑function helpers in ``utils.graph`` rather than the
end‑to‑end script, which requires large neuroimaging data.
"""

from __future__ import annotations

import numpy as np
import networkx as nx
import pytest

from utils.graph import (
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)


@pytest.fixture
def simple_adj():
    """3‑node fully‑connected undirected graph (weights = 1)."""
    mat = np.array(
        [
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0],
        ],
        dtype=float,
    )
    return mat


def test_create_graph_from_adjacency(simple_adj):
    G = create_graph_from_adjacency(simple_adj)
    assert isinstance(G, nx.Graph)
    assert G.number_of_nodes() == 3
    # each edge should have weight 1
    for u, v, d in G.edges(data=True):
        assert d["weight"] == 1.0


def test_calculate_degree_centrality(simple_adj):
    G = create_graph_from_adjacency(simple_adj)
    deg = calculate_degree_centrality(G)
    # In a 3‑node fully connected graph, each node degree = 2
    for val in deg.values():
        assert val == 2


def test_calculate_global_efficiency(simple_adj):
    G = create_graph_from_adjacency(simple_adj)
    eff = calculate_global_efficiency(G)
    # For a fully connected graph of size 3, efficiency = 1.0
    assert pytest.approx(eff, 0.001) == 1.0


def test_calculate_clustering_coefficient(simple_adj):
    G = create_graph_from_adjacency(simple_adj)
    cc = calculate_clustering_coefficient(G)
    # Fully connected triangle has clustering coefficient 1.0
    assert pytest.approx(cc, 0.001) == 1.0


def test_calculate_shortest_path_length(simple_adj):
    G = create_graph_from_adjacency(simple_adj)
    spl = calculate_shortest_path_length(G)
    # All pairs are directly connected, path length = 1
    assert pytest.approx(spl, 0.001) == 1.0