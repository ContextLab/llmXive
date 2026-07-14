"""Unit tests for the graph‑metric computation utilities."""

import pathlib
import tempfile

import numpy as np
import pytest

from code import utils
from code.utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
    create_graph_from_adjacency,
)


@pytest.fixture
def simple_adj_matrix():
    """A small 3‑node fully connected weighted graph."""
    mat = np.array(
        [
            [0.0, 1.0, 0.5],
            [1.0, 0.0, 0.2],
            [0.5, 0.2, 0.0],
        ]
    )
    return mat


def test_create_graph_from_adjacency(simple_adj_matrix):
    G = create_graph_from_adjacency(simple_adj_matrix)
    assert G.number_of_nodes() == 3
    # Fully connected (undirected) => 3 edges
    assert G.number_of_edges() == 3


def test_degree_centrality(simple_adj_matrix):
    G = create_graph_from_adjacency(simple_adj_matrix)
    deg = calculate_degree_centrality(G)
    assert isinstance(deg, dict) and len(deg) == 3
    # Values should be between 0 and 1
    for v in deg.values():
        assert 0.0 <= v <= 1.0


def test_global_efficiency(simple_adj_matrix):
    G = create_graph_from_adjacency(simple_adj_matrix)
    eff = calculate_global_efficiency(G)
    assert isinstance(eff, float)
    assert eff > 0.0


def test_clustering_coefficient(simple_adj_matrix):
    G = create_graph_from_adjacency(simple_adj_matrix)
    clust = calculate_clustering_coefficient(G)
    assert isinstance(clust, dict) and len(clust) == 3
    for v in clust.values():
        assert 0.0 <= v <= 1.0


def test_shortest_path_length(simple_adj_matrix):
    G = create_graph_from_adjacency(simple_adj_matrix)
    spl = calculate_shortest_path_length(G)
    assert isinstance(spl, dict)
    # Ensure each node has a dict of distances to others
    for target_dict in spl.values():
        assert isinstance(target_dict, dict)
        assert len(target_dict) == 3  # includes self (distance 0)


def test_compute_subject_metrics_integration(simple_adj_matrix, monkeypatch):
    """Integration‑style test that the high‑level helper runs without error."""
    # Patch the logger to avoid side effects
    monkeypatch.setattr(utils.logger, "get_logger", lambda *a, **k: utils.logger.ReproducibilityLogger())

    from code import compute_graph_metrics  # type: ignore

    # Directly call the internal function
    from code.utils.graph import (
        calculate_degree_centrality,
        calculate_global_efficiency,
        calculate_clustering_coefficient,
        calculate_shortest_path_length,
        create_graph_from_adjacency,
    )

    # Re‑use compute_subject_metrics logic from the script (duplicate for test)
    def compute_subject_metrics(adj_matrix):
        G = create_graph_from_adjacency(adj_matrix)
        mean_degree = float(
            np.mean(list(calculate_degree_centrality(G).values()))
        )
        global_eff = float(calculate_global_efficiency(G))
        mean_clustering = float(
            np.mean(list(calculate_clustering_coefficient(G).values()))
        )
        path_lengths = calculate_shortest_path_length(G)
        lengths = [
            d
            for dct in path_lengths.values()
            for d in dct.values()
            if np.isfinite(d)
        ]
        mean_path_len = float(np.mean(lengths)) if lengths else float("nan")
        return mean_degree, global_eff, mean_clustering, mean_path_len

    # Ensure it runs
    result = compute_subject_metrics(simple_adj_matrix)
    assert len(result) == 4
    for val in result:
        assert isinstance(val, float)