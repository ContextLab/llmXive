"""
Unit tests for code/utils/metrics.py
"""

import pytest
import networkx as nx
import numpy as np
from code.utils.metrics import (
    compute_clustering_coefficient,
    compute_average_path_length,
    compute_degree_distribution_stats,
    compute_graph_metrics,
)


def test_clustering_coefficient_random_graph():
    """Test clustering coefficient on a known random graph."""
    G = nx.erdos_renyi_graph(100, 0.1, seed=42)
    cc = compute_clustering_coefficient(G)
    assert 0.0 <= cc <= 1.0
    # For Erdos-Renyi, clustering coefficient approximates edge probability
    assert np.isclose(cc, 0.1, atol=0.02)


def test_clustering_coefficient_small_world():
    """Test clustering coefficient on a small-world graph."""
    G = nx.watts_strogatz_graph(100, 4, 0.1, seed=42)
    cc = compute_clustering_coefficient(G)
    assert 0.0 <= cc <= 1.0
    # Small-world graphs have high clustering
    assert cc > 0.3


def test_clustering_coefficient_empty_graph():
    """Test clustering coefficient on graphs with < 3 nodes."""
    G = nx.Graph()
    G.add_nodes_from([1, 2])
    assert compute_clustering_coefficient(G) == 0.0

    G = nx.Graph()
    assert compute_clustering_coefficient(G) == 0.0


def test_average_path_length_connected():
    """Test average path length on a connected graph."""
    G = nx.path_graph(10)
    apl = compute_average_path_length(G)
    # For a path graph of n nodes, average path length is (n+1)/3
    expected = (10 + 1) / 3.0
    assert np.isclose(apl, expected, rtol=0.01)


def test_average_path_length_disconnected():
    """Test average path length handles disconnected graphs."""
    G = nx.Graph()
    G.add_nodes_from([1, 2, 3, 4, 5])
    G.add_edge(1, 2)
    G.add_edge(3, 4)
    # Node 5 is isolated
    apl = compute_average_path_length(G)
    assert apl > 0.0
    assert np.isfinite(apl)


def test_average_path_length_single_node():
    """Test average path length on a single node graph."""
    G = nx.Graph()
    G.add_node(1)
    assert compute_average_path_length(G) == 0.0


def test_degree_distribution_stats():
    """Test degree distribution statistics."""
    G = nx.star_graph(10)  # Center has degree 10, leaves have degree 1
    stats = compute_degree_distribution_stats(G)

    assert stats["mean"] == 1.8  # (10 + 10*1) / 11
    assert stats["min"] == 1.0
    assert stats["max"] == 10.0
    assert stats["median"] == 1.0
    assert stats["std"] > 0.0


def test_degree_distribution_stats_empty():
    """Test degree distribution on empty graph."""
    G = nx.Graph()
    stats = compute_degree_distribution_stats(G)
    assert stats["mean"] == 0.0
    assert stats["std"] == 0.0
    assert stats["min"] == 0.0
    assert stats["max"] == 0.0


def test_compute_graph_metrics():
    """Test the full metrics computation pipeline."""
    G = nx.erdos_renyi_graph(50, 0.1, seed=42)
    metrics = compute_graph_metrics(G)

    assert "clustering_coefficient" in metrics
    assert "average_path_length" in metrics
    assert "degree_stats" in metrics
    assert "num_nodes" in metrics
    assert "num_edges" in metrics
    assert "density" in metrics

    assert metrics["num_nodes"] == 50
    assert 0.0 <= metrics["clustering_coefficient"] <= 1.0
    assert metrics["average_path_length"] > 0.0
    assert metrics["degree_stats"]["mean"] > 0.0
    assert metrics["density"] > 0.0
