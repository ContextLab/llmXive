"""Unit tests for the graph‑metric helper functions used in
``code/03_compute_graph_metrics.py``.

The tests construct a small synthetic adjacency matrix and verify that
the metric functions from ``utils.graph`` return values of the expected
type and within plausible ranges.
"""
from __future__ import annotations

import numpy as np

from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)


def test_degree_centrality():
    # Simple 3‑node fully connected graph (no self‑loops)
    mat = np.array(
        [[0, 1, 1],
         [1, 0, 1],
         [1, 1, 0]],
        dtype=float,
    )
    degree = calculate_degree_centrality(mat)
    # Each node has degree 2, average degree = 2
    assert isinstance(degree, float)
    assert abs(degree - 2.0) < 1e-6


def test_global_efficiency():
    mat = np.array(
        [[0, 1, 0],
         [1, 0, 1],
         [0, 1, 0]],
        dtype=float,
    )
    efficiency = calculate_global_efficiency(mat)
    assert isinstance(efficiency, float)
    # Efficiency for this line graph is >0 and <1
    assert 0 < efficiency < 1


def test_clustering_coefficient():
    # Triangle graph – clustering coefficient should be 1
    mat = np.array(
        [[0, 1, 1],
         [1, 0, 1],
         [1, 1, 0]],
        dtype=float,
    )
    clustering = calculate_clustering_coefficient(mat)
    assert isinstance(clustering, float)
    assert abs(clustering - 1.0) < 1e-6


def test_average_shortest_path_length():
    # Simple line graph of 3 nodes
    mat = np.array(
        [[0, 1, 0],
         [1, 0, 1],
         [0, 1, 0]],
        dtype=float,
    )
    path_len = calculate_shortest_path_length(mat)
    assert isinstance(path_len, float)
    # Expected average shortest path length = (1+1+2)/3 = 4/3 ≈ 1.333
    assert abs(path_len - 4 / 3) < 1e-6