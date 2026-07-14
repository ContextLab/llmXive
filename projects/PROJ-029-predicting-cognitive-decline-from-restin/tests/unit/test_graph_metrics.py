"""
Unit tests for graph metrics computation.
"""
import pytest
import numpy as np
import networkx as nx
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length
)

from code_03_compute_graph_metrics import compute_subject_metrics, check_memory_usage


class TestGraphMetrics:
    """Tests for graph metric calculation functions."""

    def test_degree_centrality(self):
        """Test degree centrality calculation."""
        # Create a simple star graph
        G = nx.star_graph(5)
        degree = calculate_degree_centrality(G)
        
        # Center node should have highest centrality
        assert degree[0] == 1.0  # Center node
        assert all(d == 0.2 for d in degree[1:])  # Peripheral nodes

    def test_global_efficiency(self):
        """Test global efficiency calculation."""
        # Complete graph has efficiency = 1
        G = nx.complete_graph(5)
        efficiency = calculate_global_efficiency(G)
        assert efficiency == 1.0

    def test_clustering_coefficient(self):
        """Test clustering coefficient calculation."""
        # Triangle has clustering coefficient = 1
        G = nx.complete_graph(3)
        clustering = calculate_clustering_coefficient(G)
        assert clustering == 1.0

    def test_shortest_path_length(self):
        """Test average shortest path length calculation."""
        # Complete graph has path length = 1
        G = nx.complete_graph(5)
        path_length = calculate_shortest_path_length(G)
        assert path_length == 1.0

    def test_compute_subject_metrics(self):
        """Test full subject metrics computation."""
        # Create a random symmetric adjacency matrix
        np.random.seed(42)
        n_nodes = 10
        matrix = np.random.rand(n_nodes, n_nodes)
        matrix = (matrix + matrix.T) / 2  # Make symmetric
        np.fill_diagonal(matrix, 0)  # Remove self-loops
        
        metrics = compute_subject_metrics(matrix, "test_subject")
        
        assert metrics is not None
        assert metrics["subject_id"] == "test_subject"
        assert "global_efficiency" in metrics
        assert "clustering_coefficient" in metrics
        assert "average_path_length" in metrics
        assert "mean_degree_centrality" in metrics
        assert metrics["n_nodes"] == n_nodes

    def test_memory_usage_check(self):
        """Test memory usage monitoring."""
        ram_gb = check_memory_usage()
        assert 0 < ram_gb < 100  # Should be reasonable (not negative, not absurdly high)

    def test_disconnected_graph(self):
        """Test handling of disconnected graph."""
        # Create a graph with two disconnected components
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2)])
        G.add_edges_from([(3, 4), (4, 5)])
        
        # Should not crash
        efficiency = calculate_global_efficiency(G)
        assert efficiency is not None
        assert efficiency >= 0

    def test_single_node_graph(self):
        """Test handling of single node graph."""
        G = nx.Graph()
        G.add_node(0)
        
        # Should handle gracefully
        degree = calculate_degree_centrality(G)
        assert degree[0] == 0.0

    def test_metrics_values_in_range(self):
        """Test that metrics are within expected ranges."""
        np.random.seed(42)
        matrix = np.random.rand(10, 10)
        matrix = (matrix + matrix.T) / 2
        np.fill_diagonal(matrix, 0)
        
        metrics = compute_subject_metrics(matrix, "test")
        
        # Efficiency should be between 0 and 1
        assert 0 <= metrics["global_efficiency"] <= 1
        
        # Clustering coefficient should be between 0 and 1
        assert 0 <= metrics["clustering_coefficient"] <= 1
        
        # Path length should be positive
        assert metrics["average_path_length"] > 0