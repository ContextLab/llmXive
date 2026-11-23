import pytest
import sys
from pathlib import Path
import networkx as nx
import numpy as np
import math

# Ensure the src directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.topology import compute_metrics


class TestComputeMetrics:
    """
    Unit tests for src/topology.py metrics calculation.
    TDD Approach: Tests defined before implementation verification.
    """

    def test_degree_distribution_sum_equals_edges(self):
        """
        Test Case: test_degree_distribution_sum_equals_edges
        Property: The sum of degrees in a graph must equal twice the number of edges.
        """
        # Create a known graph
        # 4 nodes, 3 edges in a line: 0-1-2-3
        # Degrees: 0:1, 1:2, 2:2, 3:1. Sum = 6. Edges = 3. 2*3 = 6.
        G = nx.path_graph(4)
        
        metrics = compute_metrics(G)
        
        degree_dist = metrics['degree_distribution']
        num_edges = metrics['num_edges']
        
        # Calculate sum of degrees from the distribution dict
        sum_degrees = sum(degree_dist.values())
        
        assert sum_degrees == 2 * num_edges, \
            f"Sum of degrees ({sum_degrees}) should equal 2 * num_edges ({2 * num_edges})"

    def test_clustering_coefficient_bounds(self):
        """
        Test Case: test_clustering_coefficient_bounds
        Property: Clustering coefficient must be between 0.0 and 1.0 inclusive.
        """
        # Test with a complete graph (clustering should be 1.0)
        G_complete = nx.complete_graph(5)
        metrics_complete = compute_metrics(G_complete)
        assert 0.0 <= metrics_complete['clustering_coefficient'] <= 1.0
        assert math.isclose(metrics_complete['clustering_coefficient'], 1.0, abs_tol=1e-9)

        # Test with a bipartite graph (clustering should be 0.0)
        # A star graph is bipartite and has 0 clustering
        G_bipartite = nx.star_graph(5)
        metrics_bipartite = compute_metrics(G_bipartite)
        assert 0.0 <= metrics_bipartite['clustering_coefficient'] <= 1.0
        # Star graph clustering is exactly 0
        assert math.isclose(metrics_bipartite['clustering_coefficient'], 0.0, abs_tol=1e-9)

        # Test with a random graph to ensure it stays in bounds
        G_random = nx.erdos_renyi_graph(20, 0.3, seed=42)
        metrics_random = compute_metrics(G_random)
        assert 0.0 <= metrics_random['clustering_coefficient'] <= 1.0

    def test_path_length_disconnected_graph(self):
        """
        Test Case: test_path_length_disconnected_graph
        Property: For a disconnected graph, average path length should be infinity (inf).
        """
        # Create a disconnected graph
        # Two separate components: a triangle and an isolated edge
        G1 = nx.complete_graph(3)
        G2 = nx.path_graph(2)
        G_disconnected = nx.disjoint_union(G1, G2)
        
        metrics = compute_metrics(G_disconnected)
        
        avg_path_len = metrics['average_path_length']
        
        # NetworkX returns inf for disconnected graphs when calculating average path length
        assert math.isinf(avg_path_len), \
            f"Average path length for disconnected graph should be infinity, got {avg_path_len}"

    def test_metrics_on_single_node(self):
        """
        Edge case: Single node graph.
        Expected: 0 edges, 0 clustering, 0 path length (or inf depending on definition, usually 0 for single node).
        """
        G = nx.Graph()
        G.add_node(1)
        
        metrics = compute_metrics(G)
        
        assert metrics['num_edges'] == 0
        assert metrics['num_nodes'] == 1
        # Clustering of a single node is 0
        assert metrics['clustering_coefficient'] == 0.0
        # Path length of single node is 0
        assert metrics['average_path_length'] == 0.0

    def test_metrics_on_two_connected_nodes(self):
        """
        Edge case: Two nodes connected by an edge.
        """
        G = nx.Graph()
        G.add_edge(1, 2)
        
        metrics = compute_metrics(G)
        
        assert metrics['num_edges'] == 1
        assert metrics['num_nodes'] == 2
        # Clustering of 2 nodes (no triangles possible) is 0
        assert metrics['clustering_coefficient'] == 0.0
        # Path length is 1
        assert metrics['average_path_length'] == 1.0