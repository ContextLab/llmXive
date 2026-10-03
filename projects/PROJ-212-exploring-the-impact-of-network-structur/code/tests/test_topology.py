import pytest
import sys
from pathlib import Path
import networkx as nx
import numpy as np
import math

# Ensure src is in path for imports if running directly
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from src.topology import compute_metrics
from data_models import NetworkGraph

class TestComputeMetrics:
    """Tests for src/topology.py metrics calculation."""

    def test_degree_distribution_sum_equals_edges(self):
        """Test that sum of degrees equals 2 * number of edges."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1), (1, 3)])
        
        metrics = compute_metrics(G)
        degree_stats = metrics["degree_stats"]
        
        # Sum of degrees should be 2 * |E|
        total_degree = sum([d for n, d in G.degree()])
        expected_sum = 2 * G.number_of_edges()
        
        assert total_degree == expected_sum
        # Verify our stats capture the mean correctly
        assert abs(degree_stats["mean"] - (total_degree / G.number_of_nodes())) < 1e-6

    def test_clustering_coefficient_bounds(self):
        """Test that clustering coefficients are between 0 and 1."""
        # Random graph
        G = nx.erdos_renyi_graph(50, 0.1, seed=42)
        metrics = compute_metrics(G)
        
        assert 0.0 <= metrics["clustering_coefficient"] <= 1.0
        assert 0.0 <= metrics["global_clustering"] <= 1.0

        # Complete graph (clustering should be 1)
        K = nx.complete_graph(10)
        metrics_k = compute_metrics(K)
        assert abs(metrics_k["clustering_coefficient"] - 1.0) < 1e-6
        
        # Star graph (clustering should be 0)
        S = nx.star_graph(10)
        metrics_s = compute_metrics(S)
        # Star graph has 0 clustering coefficient
        assert metrics_s["clustering_coefficient"] == 0.0

    def test_path_length_disconnected_graph(self):
        """Test that disconnected graphs return infinity for average path length."""
        # Create a disconnected graph: two separate triangles
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])
        G.add_edges_from([(4, 5), (5, 6), (6, 4)])
        
        metrics = compute_metrics(G)
        
        assert metrics["is_connected"] == False
        assert metrics["average_path_length"] == float('inf')

    def test_path_length_connected_graph(self):
        """Test that connected graphs return a finite average path length."""
        G = nx.barabasi_albert_graph(100, 2, seed=42)
        
        metrics = compute_metrics(G)
        
        assert metrics["is_connected"] == True
        assert isinstance(metrics["average_path_length"], float)
        assert not math.isinf(metrics["average_path_length"])

    def test_empty_graph(self):
        """Test behavior on an empty graph."""
        G = nx.Graph()
        metrics = compute_metrics(G)
        
        assert metrics["degree_stats"]["mean"] == 0.0
        assert metrics["is_connected"] == False
        assert metrics["average_path_length"] == float('inf')

    def test_single_node_graph(self):
        """Test behavior on a single node graph."""
        G = nx.Graph()
        G.add_node(1)
        metrics = compute_metrics(G)
        
        assert metrics["degree_stats"]["mean"] == 0.0
        assert metrics["is_connected"] == True
        # Average path length for a single node is typically 0
        assert metrics["average_path_length"] == 0.0

    def test_networkgraph_wrapper(self):
        """Test that compute_metrics works with NetworkGraph dataclass."""
        G = nx.karate_club_graph()
        wrapped_graph = NetworkGraph(id="test_001", graph=G, metadata={})
        
        metrics = compute_metrics(wrapped_graph)
        
        assert "degree_stats" in metrics
        assert "clustering_coefficient" in metrics
        assert "average_path_length" in metrics

    def test_ring_graph_analytical_clustering(self):
        """Test clustering on a ring lattice (known analytical value)."""
        # A simple ring graph where each node connects to 2 neighbors
        n = 20
        G = nx.cycle_graph(n)
        
        metrics = compute_metrics(G)
        
        # For a cycle graph, clustering coefficient is 0.75 (3/4)
        # Each node has 2 neighbors, which are connected to each other (1 edge)
        # Max possible edges between neighbors is 1. So local clustering is 1/1 = 1?
        # Wait, for a cycle graph:
        # Node i connects to i-1 and i+1.
        # Neighbors of i are {i-1, i+1}.
        # Are i-1 and i+1 connected? No, unless n=3.
        # So local clustering is 0 for n > 3.
        # Let's verify:
        if n > 3:
            assert metrics["clustering_coefficient"] == 0.0
        else:
            # For n=3 (triangle), it's 1.0
            assert metrics["clustering_coefficient"] == 1.0