"""
Unit tests for the structural metric utilities.
"""
import os
import sys
import tempfile

import networkx as nx

# Make sure the `code` directory is importable so that `utils.metrics`
# can be resolved (the utils package lives under `code/`).
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from utils.metrics import (
    calculate_assortativity,
    calculate_average_path_length,
    calculate_clustering_coefficient,
    calculate_structural_metrics,
)


def test_individual_metric_functions_agree_with_networkx():
    """Each wrapper should return the same value as the underlying NetworkX call."""
    # Use a simple path graph where the expected values are known.
    G = nx.path_graph(5)  # 5 nodes, 4 edges, linear chain

    # Degree assortativity for a path graph is -1.0 (perfect disassortative mixing)
    assort = calculate_assortativity(G)
    assert isinstance(assort, float)
    # Allow a tiny tolerance for floating errors.
    assert abs(assort + 1.0) < 1e-9

    # Average shortest path length for a path of 5 nodes is 2.0
    apl = calculate_average_path_length(G)
    assert isinstance(apl, float)
    assert abs(apl - 2.0) < 1e-9

    # Clustering coefficient for a tree (including a path) is 0.0
    cc = calculate_clustering_coefficient(G)
    assert isinstance(cc, float)
    assert abs(cc - 0.0) < 1e-9


def test_calculate_structural_metrics_returns_expected_dict():
    """The composite function should bundle all three metrics plus node/edge counts."""
    G = nx.complete_graph(4)  # 4 nodes, fully connected

    metrics = calculate_structural_metrics(G)

    # Expected keys
    expected_keys = {
        "assortativity",
        "average_path_length",
        "clustering_coefficient",
        "num_nodes",
        "num_edges",
    }
    assert set(metrics.keys()) == expected_keys

    # Verify each entry matches the individual wrappers
    assert metrics["assortativity"] == calculate_assortativity(G)
    assert metrics["average_path_length"] == calculate_average_path_length(G)
    assert metrics["clustering_coefficient"] == calculate_clustering_coefficient(G)
    assert metrics["num_nodes"] == G.number_of_nodes()
    assert metrics["num_edges"] == G.number_of_edges()