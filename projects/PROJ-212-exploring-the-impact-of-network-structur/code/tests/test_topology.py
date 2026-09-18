import pytest
import sys
from pathlib import Path
import networkx as nx
import numpy as np
from src.topology import compute_metrics
from data_models import NetworkGraph

class TestComputeMetrics:
    """
    Unit tests for src/topology.py compute_metrics function.
    Tests cover Barabási-Albert graphs, Ring graphs, and disconnected graphs.
    """

    def test_ba_graph_degree_sum(self):
        """
        Test case: Input Barabási-Albert graph (N=10, m=2).
        Verify degree distribution sum equals edges*2.
        """
        # Create a Barabási-Albert graph
        # N=10, m=2 means each new node attaches to 2 existing nodes
        G = nx.barabasi_albert_graph(n=10, m=2, seed=42)
        
        metrics = compute_metrics(G)
        
        # Calculate expected edges
        # In BA model, number of edges is exactly m * (n - m)
        expected_edges = 2 * (10 - 2)
        assert metrics['num_edges'] == expected_edges, \
            f"Expected {expected_edges} edges, got {metrics['num_edges']}"
        
        # Sum of degrees in any graph is 2 * |E|
        degree_sum = sum(metrics['degree_distribution'].keys() * 
                       np.array(list(metrics['degree_distribution'].values())))
        # Note: keys() returns degrees, values() returns counts
        # We need to multiply degree * count and sum
        calculated_degree_sum = sum(d * c for d, c in metrics['degree_distribution'].items())
        
        expected_degree_sum = 2 * metrics['num_edges']
        assert calculated_degree_sum == expected_degree_sum, \
            f"Degree sum mismatch: calculated {calculated_degree_sum}, expected {expected_degree_sum}"

    def test_clustering_coefficient_bounds(self):
        """
        Test case: Verify clustering coefficient is >= 0 and <= 1.
        """
        # Test with a random graph
        G = nx.erdos_renyi_graph(n=50, p=0.1, seed=42)
        metrics = compute_metrics(G)
        
        cc = metrics['clustering_coefficient']
        assert 0.0 <= cc <= 1.0, \
            f"Clustering coefficient {cc} is out of bounds [0, 1]"

    def test_ring_graph_path_length(self):
        """
        Test case: Input Ring Graph (N=200).
        Verify path length is finite.
        """
        G = nx.cycle_graph(200)
        metrics = compute_metrics(G)
        
        assert metrics['is_connected'] is True, "Ring graph should be connected"
        assert metrics['average_path_length'] != float('inf'), \
            "Average path length for connected graph should be finite"
        assert isinstance(metrics['average_path_length'], float), \
            "Average path length should be a float"

    def test_disconnected_graph_path_length(self):
        """
        Test case: Disconnected graph.
        Verify average path length is infinity.
        """
        # Create two disjoint cliques
        G1 = nx.complete_graph(5)
        G2 = nx.complete_graph(5)
        G = nx.disjoint_union(G1, G2)
        
        metrics = compute_metrics(G)
        
        assert metrics['is_connected'] is False, "Graph should be detected as disconnected"
        assert metrics['average_path_length'] == float('inf'), \
            "Average path length for disconnected graph should be infinity"

    def test_networkgraph_entity_support(self):
        """
        Test case: Verify compute_metrics works with NetworkGraph dataclass.
        """
        G = nx.barabasi_albert_graph(n=20, m=3, seed=123)
        network_graph = NetworkGraph(graph=G, name="test_ba")
        
        metrics = compute_metrics(network_graph)
        
        assert 'degree_distribution' in metrics
        assert 'clustering_coefficient' in metrics
        assert 'average_path_length' in metrics
        assert metrics['num_nodes'] == 20

    def test_empty_graph_raises_error(self):
        """
        Test case: Empty graph should raise ValueError.
        """
        G = nx.Graph()
        with pytest.raises(ValueError, match="empty graph"):
            compute_metrics(G)

    def test_density_calculation(self):
        """
        Test case: Verify density is calculated correctly.
        """
        # Complete graph K5 has density 1.0
        G = nx.complete_graph(5)
        metrics = compute_metrics(G)
        
        assert abs(metrics['density'] - 1.0) < 1e-6, \
            f"Complete graph density should be 1.0, got {metrics['density']}"
        
        # Empty graph (no edges) with nodes has density 0.0
        G2 = nx.Graph()
        G2.add_nodes_from([1, 2, 3])
        metrics2 = compute_metrics(G2)
        
        assert metrics2['density'] == 0.0, \
            f"Graph with no edges should have density 0.0, got {metrics2['density']}"