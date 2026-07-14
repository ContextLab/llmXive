"""Unit tests for the graph‑metric computation utilities.

The tests focus on the ``compute_subject_metrics`` helper in
``code/03_compute_graph_metrics.py``. They construct a tiny synthetic adjacency
matrix where the expected metrics can be derived analytically.
"""
import numpy as np
import pytest

from code._03_compute_graph_metrics import compute_subject_metrics  # type: ignore


@pytest.fixture
def simple_adj():
    # A 3‑node fully connected undirected graph (weights = 1)
    mat = np.array(
        [
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0],
        ],
        dtype=float,
    )
    return mat


def test_compute_subject_metrics_fully_connected(simple_adj):
    metrics = compute_subject_metrics(simple_adj)

    # In a fully connected 3‑node graph:
    # - Degree centrality for each node = 2 / (N‑1) = 1.0
    # - Average degree = 1.0
    # - Global efficiency = 1.0 (all shortest paths length = 1)
    # - Clustering coefficient = 1.0 (each node's neighbours are connected)
    # - Average shortest path length = 1.0
    assert pytest.approx(metrics["degree"], rel=1e-6) == 1.0
    assert pytest.approx(metrics["global_efficiency"], rel=1e-6) == 1.0
    assert pytest.approx(metrics["clustering_coefficient"], rel=1e-6) == 1.0
    assert pytest.approx(metrics["average_path_length"], rel=1e-6) == 1.0