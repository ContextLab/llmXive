"""
Unit tests for the distance‑based cutoff logic implemented in
``code/generate_networks.py`` (task T012).

The tests verify:
  * Correct computation of the nearest‑neighbor distance.
  * Proper scaling of the cutoff with the supplied factor.
  * Automatic retry up to ``2.0×`` the original factor when the initial
    graph is disconnected.
"""

import numpy as np
import pytest

from generate_networks import (
    nearest_neighbor_distance,
    build_graph,
    generate_connected_graph,
)
import networkx as nx


@pytest.fixture
def linear_positions():
    """
    Five points placed on the x‑axis at unit spacing:
    0, 1, 2, 3, 4.
    """
    return np.array([[i, 0.0, 0.0] for i in range(5)], dtype=float)


def test_nearest_neighbor_distance(linear_positions):
    nn = nearest_neighbor_distance(linear_positions)
    assert nn == pytest.approx(1.0, rel=1e-6), "Nearest‑neighbor distance should be 1.0 for unit‑spaced line"


@pytest.mark.parametrize("factor,expected_connected", [
    (0.5, False),   # cutoff = 0.5 < NN, graph disconnected
    (1.0, True),    # cutoff = 1.0 connects neighbours => chain => connected
    (1.5, True),    # larger cutoff also yields connectivity
])
def test_build_graph_connectivity(linear_positions, factor, expected_connected):
    nn = nearest_neighbor_distance(linear_positions)
    cutoff = factor * nn
    G = build_graph(linear_positions, cutoff)
    assert nx.is_connected(G) == expected_connected


def test_generate_connected_graph_retries_up_to_max_factor(linear_positions):
    """
    Start with a factor that is too small (0.4).  The function should
    automatically increase the factor in steps of 0.1 until the graph
    becomes connected or the max factor (2.0) is reached.
    """
    G, final_factor = generate_connected_graph(linear_positions, factor=0.4, max_factor=2.0, step=0.1)

    # The final graph must be connected.
    assert nx.is_connected(G), "Graph should be connected after retries"

    # The final factor must be >= the initial factor and <= max_factor.
    assert 0.4 <= final_factor <= 2.0

    # For this simple line, a factor of 1.0 already yields connectivity.
    # Therefore the algorithm should stop at 1.0 (or the first factor that
    # produces a connected graph).  We allow a small tolerance for the
    # incremental rounding logic.
    assert final_factor == pytest.approx(1.0, rel=1e-6) or final_factor == pytest.approx(1.1, rel=1e-6)


def test_generate_connected_graph_falls_back_to_max_factor_when_never_connected():
    """
    Construct a pathological set of positions where even the max_factor
    does not produce a connected graph (e.g., two clusters far apart).
    The function should return the graph built with max_factor and the
    max_factor itself.
    """
    # Two clusters separated by distance 10, each cluster internally spaced by 1.
    cluster_a = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]], dtype=float)
    cluster_b = np.array([[10, 0, 0], [11, 0, 0], [12, 0, 0]], dtype=float)
    positions = np.vstack([cluster_a, cluster_b])

    # NN distance is 1.0, max_factor = 2.0 gives cutoff = 2.0,
    # which cannot bridge the 8‑unit gap between clusters.
    G, final_factor = generate_connected_graph(positions, factor=0.5, max_factor=2.0, step=0.5)

    assert final_factor == pytest.approx(2.0, rel=1e-6)
    assert not nx.is_connected(G), "Graph should remain disconnected when clusters are too far apart"
    # Ensure that the graph contains exactly two connected components.
    assert nx.number_connected_components(G) == 2