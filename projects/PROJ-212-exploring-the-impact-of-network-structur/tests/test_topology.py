import pytest
import sys
from pathlib import Path
import networkx as nx
import numpy as np
import math

# Ensure we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from src.topology import compute_metrics


class TestComputeMetrics:
    """
    Unit tests for src/topology.py metrics calculation.
    Implements TDD approach for T010.
    """

    def test_degree_distribution_sum_equals_edges(self):
        """
        Test that the sum of the degree distribution values equals twice the number of edges.
        In any undirected graph: sum(degrees) = 2 * |E|
        """
        # Create a simple graph: 4 nodes in a square (cycle)
        # Nodes: 0-1-2-3-0
        # Edges: (0,1), (1,2), (2,3), (3,0) -> 4 edges
        G = nx.cycle_graph(4)
        
        metrics = compute_metrics(G)
        
        degree_dist = metrics['degree_distribution']
        # degree_distribution returns a dict: {degree: count}
        # Sum of counts should equal number of nodes, but sum of (degree * count) should equal 2*|E|
        total_degree_sum = sum(deg * count for deg, count in degree_dist.items())
        expected_sum = 2 * G.number_of_edges()
        
        assert total_degree_sum == expected_sum, \
            f"Sum of degrees ({total_degree_sum}) should equal 2 * edges ({expected_sum})"

    def test_clustering_coefficient_bounds(self):
        """
        Test that the average clustering coefficient is within valid bounds [0, 1].
        """
        # Test 1: Complete graph (clustering should be 1.0)
        G_complete = nx.complete_graph(5)
        metrics_complete = compute_metrics(G_complete)
        cc_complete = metrics_complete['clustering_coefficient']
        assert 0.0 <= cc_complete <= 1.0, \
            f"Clustering coefficient {cc_complete} for complete graph must be in [0, 1]"
        assert math.isclose(cc_complete, 1.0, rel_tol=1e-9), \
            f"Complete graph clustering should be 1.0, got {cc_complete}"

        # Test 2: Cycle graph (clustering should be 0 for N > 3)
        G_cycle = nx.cycle_graph(10)
        metrics_cycle = compute_metrics(G_cycle)
        cc_cycle = metrics_cycle['clustering_coefficient']
        assert 0.0 <= cc_cycle <= 1.0, \
            f"Clustering coefficient {cc_cycle} for cycle graph must be in [0, 1]"
        assert math.isclose(cc_cycle, 0.0, abs_tol=1e-9), \
            f"Cycle graph clustering should be 0.0, got {cc_cycle}"

        # Test 3: Random graph (should be in [0, 1])
        G_random = nx.erdos_renyi_graph(20, 0.3, seed=42)
        metrics_random = compute_metrics(G_random)
        cc_random = metrics_random['clustering_coefficient']
        assert 0.0 <= cc_random <= 1.0, \
            f"Clustering coefficient {cc_random} for random graph must be in [0, 1]"

    def test_path_length_disconnected_graph(self):
        """
        Test that average path length is infinity (or handled correctly) for disconnected graphs.
        """
        # Create a disconnected graph: two separate triangles
        G1 = nx.complete_graph(3)
        G2 = nx.complete_graph(3)
        G_disconnected = nx.disjoint_union(G1, G2)
        
        metrics = compute_metrics(G_disconnected)
        avg_path_length = metrics['average_path_length']
        
        # For disconnected graphs, average path length is undefined (infinity)
        # NetworkX returns infinity for disconnected components
        assert math.isinf(avg_path_length), \
            f"Average path length for disconnected graph should be infinity, got {avg_path_length}"
        
        # Also verify the graph is indeed disconnected
        assert not nx.is_connected(G_disconnected), \
            "Test setup failed: graph should be disconnected"

    def test_metrics_return_structure(self):
        """
        Test that compute_metrics returns a dictionary with expected keys.
        """
        G = nx.barabasi_albert_graph(20, 2, seed=42)
        metrics = compute_metrics(G)
        
        expected_keys = [
            'num_nodes',
            'num_edges',
            'density',
            'degree_distribution',
            'clustering_coefficient',
            'average_path_length',
            'is_connected'
        ]
        
        for key in expected_keys:
            assert key in metrics, f"Missing expected key '{key}' in metrics output"
        
        assert isinstance(metrics['num_nodes'], int)
        assert isinstance(metrics['num_edges'], int)
        assert isinstance(metrics['density'], float)
        assert isinstance(metrics['degree_distribution'], dict)
        assert isinstance(metrics['clustering_coefficient'], float)
        assert isinstance(metrics['is_connected'], bool)

    def test_degree_distribution_format(self):
        """
        Test that degree_distribution is a dictionary with integer keys and values.
        """
        G = nx.path_graph(10)
        metrics = compute_metrics(G)
        degree_dist = metrics['degree_distribution']
        
        assert isinstance(degree_dist, dict), "degree_distribution must be a dictionary"
        
        for degree, count in degree_dist.items():
            assert isinstance(degree, int), f"Degree key {degree} must be an integer"
            assert isinstance(count, int), f"Count value {count} must be an integer"
            assert count > 0, f"Count {count} must be positive"

    def test_clustering_coefficient_single_node(self):
        """
        Test clustering coefficient for a single node graph (edge case).
        """
        G = nx.Graph()
        G.add_node(1)
        
        metrics = compute_metrics(G)
        cc = metrics['clustering_coefficient']
        
        # For a single node with no edges, clustering is typically 0
        assert 0.0 <= cc <= 1.0, f"Clustering coefficient {cc} must be in [0, 1]"

    def test_clustering_coefficient_empty_graph(self):
        """
        Test clustering coefficient for an empty graph (no nodes).
        """
        G = nx.Graph()
        
        metrics = compute_metrics(G)
        cc = metrics['clustering_coefficient']
        
        # Should handle empty graph gracefully, typically 0.0
        assert isinstance(cc, (int, float)), "Clustering coefficient must be numeric"