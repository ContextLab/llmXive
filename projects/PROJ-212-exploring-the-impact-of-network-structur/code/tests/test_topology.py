import pytest
import networkx as nx
import numpy as np
from src.topology import compute_metrics
from data_models import NetworkGraph

class TestComputeMetrics:
    """Unit tests for the compute_metrics function in src/topology.py."""

    def test_barabasi_albert_graph(self):
        """Test metrics calculation on a Barabási-Albert graph."""
        # Create a Barabási-Albert graph (N=100, m=2)
        G = nx.barabasi_albert_graph(100, 2)
        
        # Wrap in NetworkGraph if needed, or pass directly
        metrics = compute_metrics(G)

        # Assertions
        assert metrics["number_of_nodes"] == 100
        assert metrics["number_of_edges"] > 0
        assert metrics["is_connected"] is True
        assert metrics["mean_degree"] > 0
        assert metrics["average_path_length"] != float('inf')
        assert 0 <= metrics["clustering_coefficient"] <= 1
        assert 0 <= metrics["average_clustering"] <= 1

    def test_complete_graph(self):
        """Test metrics on a complete graph (K_n)."""
        n = 10
        G = nx.complete_graph(n)
        metrics = compute_metrics(G)

        # In a complete graph, every node connects to every other node
        expected_degree = n - 1
        expected_clustering = 1.0  # Complete graphs are fully clustered
        
        assert metrics["number_of_nodes"] == n
        assert metrics["mean_degree"] == expected_degree
        assert metrics["clustering_coefficient"] == expected_clustering
        assert metrics["average_clustering"] == expected_clustering
        assert metrics["is_connected"] is True

    def test_disconnected_graph(self):
        """Test handling of a disconnected graph (average path length should be infinity)."""
        # Create two separate triangles
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])
        G.add_edges_from([(3, 4), (4, 5), (5, 3)])
        
        metrics = compute_metrics(G)

        assert metrics["number_of_nodes"] == 6
        assert metrics["is_connected"] is False
        assert metrics["average_path_length"] == float('inf')
        # Clustering should still be calculable (1.0 for two triangles)
        assert metrics["clustering_coefficient"] == 1.0

    def test_empty_graph(self):
        """Test handling of an empty graph."""
        G = nx.Graph()
        metrics = compute_metrics(G)

        assert metrics["number_of_nodes"] == 0
        assert metrics["number_of_edges"] == 0
        assert metrics["is_connected"] is False
        assert metrics["mean_degree"] == 0.0
        assert metrics["average_path_length"] == float('inf')

    def test_single_node_graph(self):
        """Test handling of a graph with a single node."""
        G = nx.Graph()
        G.add_node(0)
        metrics = compute_metrics(G)

        assert metrics["number_of_nodes"] == 1
        assert metrics["number_of_edges"] == 0
        assert metrics["is_connected"] is True  # A single node is considered connected
        assert metrics["mean_degree"] == 0.0
        # Average path length for a single node is 0
        assert metrics["average_path_length"] == 0.0

    def test_network_graph_wrapper(self):
        """Test that compute_metrics works with NetworkGraph objects."""
        G = nx.karate_club_graph()
        wrapped_graph = NetworkGraph(graph=G, source="test")
        
        metrics = compute_metrics(wrapped_graph)

        assert metrics["number_of_nodes"] == G.number_of_nodes()
        assert metrics["is_connected"] is True

    def test_degree_distribution_correctness(self):
        """Verify that degree distribution matches actual node degrees."""
        G = nx.path_graph(5)  # 0-1-2-3-4
        metrics = compute_metrics(G)
        
        # Path graph degrees: [1, 2, 2, 2, 1]
        expected_degrees = sorted([1, 2, 2, 2, 1])
        actual_degrees = sorted(metrics["degree_distribution"])
        
        assert actual_degrees == expected_degrees

    def test_clustering_bounds(self):
        """Ensure clustering coefficients are within valid bounds [0, 1]."""
        G = nx.erdos_renyi_graph(50, 0.1)
        metrics = compute_metrics(G)

        assert 0.0 <= metrics["clustering_coefficient"] <= 1.0
        assert 0.0 <= metrics["average_clustering"] <= 1.0