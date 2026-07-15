import pytest
import numpy as np
import networkx as nx
import os
import tempfile
from pathlib import Path

# Import the functions to test
from code.utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)
from code.utils.io import save_numpy, load_csv
from code.utils.logger import get_logger

logger = get_logger("test_graph_metrics")


class TestGraphMetrics:
    """Unit tests for graph metric calculation functions."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a simple test graph (a ring of 5 nodes)
        self.num_nodes = 5
        self.matrix = np.zeros((self.num_nodes, self.num_nodes))
        for i in range(self.num_nodes):
            self.matrix[i, (i + 1) % self.num_nodes] = 1.0
            self.matrix[(i + 1) % self.num_nodes, i] = 1.0
        
        self.G = nx.from_numpy_array(self.matrix)

    def test_degree_centrality(self):
        """Test degree centrality calculation."""
        degree = calculate_degree_centrality(self.G)
        # In a ring of 5, each node has degree 2, centrality = 2/(5-1) = 0.5
        assert isinstance(degree, (int, float))
        assert degree == pytest.approx(0.5, rel=1e-6)

    def test_global_efficiency(self):
        """Test global efficiency calculation."""
        efficiency = calculate_global_efficiency(self.G)
        assert isinstance(efficiency, (int, float))
        assert efficiency >= 0.0
        # For a ring of 5, average shortest path is 1.5, so efficiency is 1/1.5 = 0.666...
        assert efficiency == pytest.approx(0.666, rel=0.1)

    def test_clustering_coefficient(self):
        """Test clustering coefficient calculation."""
        clustering = calculate_clustering_coefficient(self.G)
        assert isinstance(clustering, (int, float))
        # In a ring, no triangles, so clustering should be 0
        assert clustering == 0.0

    def test_shortest_path_length(self):
        """Test average shortest path length calculation."""
        path_length = calculate_shortest_path_length(self.G)
        assert isinstance(path_length, (int, float))
        # For a ring of 5, average shortest path is 1.5
        assert path_length == pytest.approx(1.5, rel=1e-6)

    def test_complete_graph(self):
        """Test metrics on a complete graph."""
        n = 4
        complete_matrix = np.ones((n, n))
        np.fill_diagonal(complete_matrix, 0.0)
        G_complete = nx.from_numpy_array(complete_matrix)
        
        degree = calculate_degree_centrality(G_complete)
        # In complete graph of 4, degree centrality = (n-1)/(n-1) = 1.0
        assert degree == pytest.approx(1.0, rel=1e-6)

        efficiency = calculate_global_efficiency(G_complete)
        # Efficiency = 1.0 for complete graph
        assert efficiency == pytest.approx(1.0, rel=1e-6)

    def test_disconnected_graph(self):
        """Test handling of disconnected graph."""
        # Two separate nodes
        matrix = np.zeros((2, 2))
        G = nx.from_numpy_array(matrix)
        
        # Should not crash, but return NaN or 0
        try:
            path_length = calculate_shortest_path_length(G)
            # If it returns a number, it should be infinity or handled
            assert not np.isnan(path_length) or path_length == np.inf
        except nx.NetworkXError:
            # Expected for disconnected graph with no path
            pass

class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_end_to_end_metrics(self):
        """Test end-to-end metric computation."""
        # Create a random symmetric matrix
        np.random.seed(42)
        n = 10
        matrix = np.random.rand(n, n)
        matrix = (matrix + matrix.T) / 2
        np.fill_diagonal(matrix, 0.0)
        
        G = nx.from_numpy_array(matrix)
        
        degree = calculate_degree_centrality(G)
        efficiency = calculate_global_efficiency(G)
        clustering = calculate_clustering_coefficient(G)
        path_length = calculate_shortest_path_length(G)
        
        # Verify all metrics are computed
        assert isinstance(degree, (int, float))
        assert isinstance(efficiency, (int, float))
        assert isinstance(clustering, (int, float))
        assert isinstance(path_length, (int, float))
        
        # Verify ranges
        assert 0.0 <= degree <= 1.0
        assert 0.0 <= efficiency <= 1.0
        assert 0.0 <= clustering <= 1.0
        assert path_length >= 0.0