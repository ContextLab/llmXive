"""
Unit test for network topology metrics.

This test verifies that the `compute_topological_metrics` function from
`generate_networks` correctly computes the clustering coefficient and the
average shortest path length for a simple, analytically tractable graph.
"""

import pytest
import networkx as nx

# The function under test is part of the public API of `generate_networks`.
from generate_networks import compute_topological_metrics


def _extract_metric(metrics: dict, *possible_keys):
    """
    Helper to retrieve a metric value from the dictionary returned by
    ``compute_topological_metrics``.  The implementation of that function may
    use different key names (e.g. ``clustering`` vs ``clustering_coeff``), so
    we try a list of possible keys and raise a clear error if none are found.
    """
    for key in possible_keys:
        if key in metrics:
            return metrics[key]
    raise KeyError(
        f"None of the expected keys {possible_keys} were present in the metrics dict: {list(metrics)}"
    )


def test_clustering_coefficient_accuracy():
    """
    For a complete graph of three nodes the clustering coefficient is 1.0
    and the average shortest path length is also 1.0.  The test constructs
    this graph, runs the metric extractor and checks that the returned
    values match the analytical expectations within a tight tolerance.
    """
    # Build a fully connected triangle graph.
    G = nx.complete_graph(3)

    # Compute metrics using the project's implementation.
    metrics = compute_topological_metrics(G)

    # Extract values, being tolerant to possible key naming variations.
    clustering = _extract_metric(metrics, "clustering_coeff", "clustering")
    avg_path_len = _extract_metric(
        metrics, "average_path_length", "avg_path_length", "average_shortest_path"
    )

    # Expected values for a K3 graph.
    assert pytest.approx(clustering, rel=1e-6) == 1.0
    assert pytest.approx(avg_path_len, rel=1e-6) == 1.0