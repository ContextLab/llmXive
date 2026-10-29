"""
Unit tests for the structural metrics utilities.
"""
import math

import networkx as nx

# Import metric functions from the project's utils package
from code.utils.metrics import (
    calculate_assortativity,
    calculate_average_path_length,
    calculate_clustering_coefficient,
    calculate_structural_metrics,
)


def test_assortativity_regular_graph():
    # A regular graph (e.g., cycle) should have assortativity defined as 0.0
    G = nx.cycle_graph(6)  # each node degree = 2
    assort = calculate_assortativity(G)
    assert math.isclose(assort, 0.0, abs_tol=1e-9)


def test_average_path_length_path_graph():
    # For a simple path graph the average shortest path length is known
    G = nx.path_graph(5)  # nodes 0‑4
    avg_len = calculate_average_path_length(G)
    # The exact value for a path of length 5 is 2.0
    assert math.isclose(avg_len, 2.0, rel_tol=1e-6)


def test_clustering_coefficient_path_graph():
    # Path graphs have zero clustering
    G = nx.path_graph(5)
    clustering = calculate_clustering_coefficient(G)
    assert math.isclose(clustering, 0.0, abs_tol=1e-9)


def test_structural_metrics_contains_all_keys():
    G = nx.erdos_renyi_graph(n=10, p=0.3, seed=42)
    metrics = calculate_structural_metrics(G)

    expected_keys = {
        "assortativity",
        "average_path_length",
        "clustering_coefficient",
        "num_nodes",
        "num_edges",
    }
    assert expected_keys.issubset(metrics.keys())
    # Basic sanity checks on returned types
    assert isinstance(metrics["assortativity"], float)
    assert isinstance(metrics["average_path_length"], float)
    assert isinstance(metrics["clustering_coefficient"], float)
    assert isinstance(metrics["num_nodes"], int)
    assert isinstance(metrics["num_edges"], int)
