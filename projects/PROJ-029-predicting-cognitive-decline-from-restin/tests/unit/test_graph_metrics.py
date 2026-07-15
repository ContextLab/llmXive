"""Unit tests for graph metric calculation."""
import pytest
import numpy as np
import networkx as nx
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
    create_graph_from_adjacency,
)
from code_03_compute_graph_metrics import compute_subject_metrics


class TestGraphMetrics:
    """Test suite for graph metric functions."""

    def test_degree_centrality_complete_graph(self):
        """Test degree centrality on a complete graph."""
        # Complete graph with 5 nodes
        G = nx.complete_graph(5)
        centrality = calculate_degree_centrality(G)
        # In a complete graph, every node is connected to every other node
        # Degree centrality should be (n-1)/(n-1) = 1.0 for each node
        # Mean should be 1.0
        assert centrality == pytest.approx(1.0, rel=1e-5)

    def test_degree_centrality_empty_graph(self):
        """Test degree centrality on an empty graph."""
        G = nx.Graph()
        centrality = calculate_degree_centrality(G)
        assert centrality == 0.0

    def test_global_efficiency_complete_graph(self):
        """Test global efficiency on a complete graph."""
        G = nx.complete_graph(5)
        efficiency = calculate_global_efficiency(G)
        # For a complete graph, efficiency is 1.0
        assert efficiency == pytest.approx(1.0, rel=1e-5)

    def test_global_efficiency_empty_graph(self):
        """Test global efficiency on an empty graph."""
        G = nx.Graph()
        efficiency = calculate_global_efficiency(G)
        assert efficiency == 0.0

    def test_clustering_coefficient_complete_graph(self):
        """Test clustering coefficient on a complete graph."""
        G = nx.complete_graph(5)
        clustering = calculate_clustering_coefficient(G)
        # Complete graph has clustering coefficient 1.0
        assert clustering == pytest.approx(1.0, rel=1e-5)

    def test_clustering_coefficient_empty_graph(self):
        """Test clustering coefficient on an empty graph."""
        G = nx.Graph()
        clustering = calculate_clustering_coefficient(G)
        assert clustering == 0.0

    def test_shortest_path_complete_graph(self):
        """Test shortest path on a complete graph."""
        G = nx.complete_graph(5)
        path_length = calculate_shortest_path_length(G)
        # In a complete graph, all nodes are directly connected
        assert path_length == pytest.approx(1.0, rel=1e-5)

    def test_shortest_path_disconnected(self):
        """Test shortest path on a disconnected graph."""
        # Create two disconnected components
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])
        path_length = calculate_shortest_path_length(G)
        # Should return average of largest component
        assert path_length == pytest.approx(1.0, rel=1e-5)

    def test_compute_subject_metrics(self):
        """Test the full metric computation pipeline."""
        # Create a simple adjacency matrix (5x5)
        np.random.seed(42)
        adj = np.random.rand(5, 5)
        adj = (adj + adj.T) / 2  # Symmetrize
        np.fill_diagonal(adj, 0)  # No self-loops

        metrics = compute_subject_metrics(adj, threshold=0.3)

        # Check that all expected metrics are present
        assert "degree" in metrics
        assert "global_efficiency" in metrics
        assert "clustering_coefficient" in metrics
        assert "average_path_length" in metrics

        # Check that values are reasonable
        assert 0 <= metrics["degree"] <= 1
        assert 0 <= metrics["global_efficiency"] <= 1
        assert 0 <= metrics["clustering_coefficient"] <= 1
        assert metrics["average_path_length"] >= 0

    def test_compute_subject_metrics_threshold(self):
        """Test that thresholding affects the metrics."""
        # Create a dense adjacency matrix
        np.random.seed(42)
        adj = np.ones((5, 5))
        np.fill_diagonal(adj, 0)

        # With threshold 0.5, all edges remain
        metrics_dense = compute_subject_metrics(adj, threshold=0.5)

        # With threshold 1.0, all edges are removed (since max value is 1.0)
        metrics_sparse = compute_subject_metrics(adj, threshold=1.0)

        # Degree should be lower (or zero) in the sparse case
        assert metrics_sparse["degree"] <= metrics_dense["degree"]

    def test_compute_subject_metrics_empty(self):
        """Test computation on an empty graph."""
        adj = np.zeros((5, 5))
        metrics = compute_subject_metrics(adj, threshold=0.5)

        assert metrics["degree"] == 0.0
        assert metrics["global_efficiency"] == 0.0
        assert metrics["clustering_coefficient"] == 0.0
        assert metrics["average_path_length"] == 0.0

    def test_create_graph_from_adjacency(self):
        """Test graph creation from adjacency matrix."""
        adj = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        G = create_graph_from_adjacency(adj)

        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 2
        assert nx.is_connected(G)
