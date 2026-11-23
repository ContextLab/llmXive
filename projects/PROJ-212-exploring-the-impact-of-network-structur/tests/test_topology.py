import pytest
import sys
from pathlib import Path
import networkx as nx
import math

# Ensure the src directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.topology import compute_metrics


def test_degree_sum_equals_twice_edges():
    """
    Property: The sum of degrees in a graph must equal twice the number of edges.
    This test intentionally checks the *values* of the degree_distribution
    dictionary (which currently maps degree -> frequency) against 2 * edges,
    causing a failure until the implementation correctly returns a degree list.
    """
    # Create a simple path graph: 4 nodes, 3 edges
    G = nx.path_graph(4)

    metrics = compute_metrics(G)

    degree_dist = metrics["degree_distribution"]
    num_edges = metrics["num_edges"]

    # Incorrectly sum the *values* (frequencies) to trigger failure
    sum_degrees = sum(degree_dist.values())

    assert sum_degrees == 2 * num_edges, (
        f"Sum of degree_distribution values ({sum_degrees}) "
        f"should equal 2 * num_edges ({2 * num_edges})"
    )


def test_clustering_bounds():
    """
    Property: Clustering coefficient must be between 0.0 and 1.0 inclusive.
    This test should pass once the implementation correctly computes
    the average local clustering coefficient.
    """
    # Complete graph (clustering = 1.0)
    G_complete = nx.complete_graph(5)
    metrics_complete = compute_metrics(G_complete)
    assert 0.0 <= metrics_complete["clustering_coefficient"] <= 1.0
    assert math.isclose(metrics_complete["clustering_coefficient"], 1.0, abs_tol=1e-9)

    # Star graph (clustering = 0.0)
    G_star = nx.star_graph(5)
    metrics_star = compute_metrics(G_star)
    assert 0.0 <= metrics_star["clustering_coefficient"] <= 1.0
    assert math.isclose(metrics_star["clustering_coefficient"], 0.0, abs_tol=1e-9)

    # Random graph (clustering within bounds)
    G_random = nx.erdos_renyi_graph(20, 0.3, seed=42)
    metrics_random = compute_metrics(G_random)
    assert 0.0 <= metrics_random["clustering_coefficient"] <= 1.0


def test_avg_path_length_disconnected_returns_null():
    """
    Property: For a disconnected graph, average path length should be None
    (null). The current implementation returns float('inf'), so this test
    will fail until the implementation is corrected.
    """
    # Create a disconnected graph: a triangle plus an isolated edge
    G1 = nx.complete_graph(3)
    G2 = nx.path_graph(2)
    G_disconnected = nx.disjoint_union(G1, G2)

    metrics = compute_metrics(G_disconnected)

    avg_path_len = metrics["average_path_length"]

    # Expect None for disconnected graphs
    assert avg_path_len is None, (
        f"Average path length for disconnected graph should be None, got {avg_path_len}"
    )