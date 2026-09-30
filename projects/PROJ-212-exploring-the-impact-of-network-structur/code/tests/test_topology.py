import pytest
import sys
from pathlib import Path
import networkx as nx
import numpy as np
import math

# Add src to path if running directly
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.topology import compute_metrics
from data_models import NetworkGraph

class TestComputeMetrics:
    """
    Unit tests for src/topology.py compute_metrics function.
    Tests T013 requirements: degree distribution, clustering coefficient,
    average path length (handling disconnected graphs).
    """

    def test_degree_distribution_sum_equals_edges(self):
        """
        Verify that the sum of counts in degree distribution equals 2 * num_edges
        (Handshaking lemma).
        """
        # Create a known graph: Triangle (3 nodes, 3 edges)
        G = nx.cycle_graph(3)
        
        metrics = compute_metrics(G)
        
        dist = metrics["degree_distribution"]
        total_degree_count = sum(dist.values())
        expected_total_nodes = G.number_of_nodes()
        
        assert total_degree_count == expected_total_nodes, \
            f"Sum of degree counts ({total_degree_count}) should equal number of nodes ({expected_total_nodes})"
        
        # Verify edges calculation via sum of degrees / 2
        sum_degrees = sum(k * v for k, v in dist.items())
        assert sum_degrees == 2 * G.number_of_edges(), \
            "Sum of degrees must equal 2 * number of edges"

    def test_clustering_coefficient_bounds(self):
        """
        Verify clustering coefficient is between 0 and 1 inclusive.
        """
        # Test random graphs
        for i in range(5):
            G = nx.erdos_renyi_graph(20, 0.3, seed=i)
            metrics = compute_metrics(G)
            cc = metrics["clustering_coefficient"]
            
            assert 0.0 <= cc <= 1.0, \
                f"Clustering coefficient {cc} out of bounds [0, 1]"

    def test_path_length_disconnected_graph(self):
        """
        Verify that average_path_length is infinity for disconnected graphs.
        """
        # Create a disconnected graph: two separate triangles
        G = nx.disjoint_union(nx.cycle_graph(3), nx.cycle_graph(3))
        
        metrics = compute_metrics(G)
        
        assert metrics["average_path_length"] == float('inf'), \
            "Average path length should be infinity for disconnected graphs"
        
        assert metrics["is_connected"] is False, \
            "is_connected should be False for disconnected graphs"

    def test_path_length_connected_graph(self):
        """
        Verify that average_path_length is finite for connected graphs.
        """
        # Create a connected graph: Path graph
        G = nx.path_graph(10)
        
        metrics = compute_metrics(G)
        
        assert metrics["average_path_length"] != float('inf'), \
            "Average path length should be finite for connected graphs"
        
        assert metrics["is_connected"] is True, \
            "is_connected should be True for connected graphs"
        
        # Check against known value for path graph P10
        # Average shortest path for P_n is approx (n^2 - 1) / (3n) for large n,
        # exact calculation: sum_{i<j} (j-i) / (n(n-1)/2)
        # For n=10: sum = 165, pairs = 45, avg = 165/45 = 3.666...
        expected_avg = 165 / 45
        assert math.isclose(metrics["average_path_length"], expected_avg, rel_tol=1e-9), \
            f"Average path length {metrics['average_path_length']} != expected {expected_avg}"

    def test_barabasi_albert_properties(self):
        """
        Specific test for Barabási-Albert graph properties as mentioned in T013 verification.
        """
        # Generate BA graph
        G = nx.barabasi_albert_graph(50, 2, seed=42)
        
        metrics = compute_metrics(G)
        
        # BA graphs are connected (usually)
        assert metrics["is_connected"] is True, "BA graph should be connected"
        
        # Clustering should be positive
        assert metrics["clustering_coefficient"] > 0, "BA graph should have positive clustering"
        
        # Path length should be finite
        assert metrics["average_path_length"] != float('inf'), "BA graph path length should be finite"
        
        # Degree distribution should exist and sum to N
        assert sum(metrics["degree_distribution"].values()) == 50, "Degree distribution sum must equal N"

    def test_empty_graph_handling(self):
        """
        Test behavior with an empty graph.
        """
        G = nx.Graph()
        
        metrics = compute_metrics(G)
        
        assert metrics["num_nodes"] == 0
        assert metrics["num_edges"] == 0
        assert metrics["average_degree"] == 0.0
        assert metrics["clustering_coefficient"] == 0.0
        assert metrics["average_path_length"] == float('inf')
        assert metrics["is_connected"] is False

    def test_network_graph_wrapper(self):
        """
        Test that the function works with the NetworkGraph dataclass wrapper.
        """
        nx_G = nx.complete_graph(5)
        wrapped_G = NetworkGraph(graph=nx_G, id="test-1")
        
        metrics = compute_metrics(wrapped_G)
        
        assert metrics["num_nodes"] == 5
        assert metrics["num_edges"] == 10
        assert metrics["is_connected"] is True