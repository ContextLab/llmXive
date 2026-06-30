"""
Unit tests for graph metric calculation (degree, efficiency, clustering, path length).
Tests the functions defined in code/utils/graph.py.
"""
import numpy as np
import networkx as nx
import pytest
import sys
from pathlib import Path

# Add code directory to path to import utils
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from utils.graph import (
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_local_efficiency,
    calculate_shortest_path_length
)


class TestGraphConstruction:
    """Tests for creating NetworkX graphs from adjacency matrices."""

    def test_create_graph_from_adjacency_symmetric(self):
        """Test creating a graph from a symmetric adjacency matrix."""
        adj_matrix = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() == 3
        assert graph.number_of_edges() == 3

    def test_create_graph_from_adjacency_weighted(self):
        """Test that edge weights are preserved from adjacency matrix."""
        adj_matrix = np.array([
            [0, 0.5, 0.8],
            [0.5, 0, 0.3],
            [0.8, 0.3, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        assert graph[0][1]['weight'] == 0.5
        assert graph[0][2]['weight'] == 0.8
        assert graph[1][2]['weight'] == 0.3

    def test_create_graph_from_adjacency_diagonal_ignored(self):
        """Test that diagonal elements (self-loops) are ignored."""
        adj_matrix = np.array([
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        # Should have 3 nodes, but no self-loops
        assert graph.number_of_nodes() == 3
        # Complete graph K3 has 3 edges
        assert graph.number_of_edges() == 3
        # Check no self-loops
        for node in graph.nodes():
            assert not graph.has_edge(node, node)


class TestGlobalEfficiency:
    """Tests for global efficiency calculation."""

    def test_global_efficiency_complete_graph(self):
        """Global efficiency of complete graph should be 1.0."""
        adj_matrix = np.ones((4, 4)) - np.eye(4)
        graph = create_graph_from_adjacency(adj_matrix)
        efficiency = calculate_global_efficiency(graph)
        assert np.isclose(efficiency, 1.0)

    def test_global_efficiency_disconnected_graph(self):
        """Global efficiency of disconnected graph with isolated nodes."""
        # Graph with 2 components: nodes 0-1 connected, node 2 isolated
        adj_matrix = np.array([
            [0, 1, 0],
            [1, 0, 0],
            [0, 0, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        # Should not crash, but return a finite value (0 for infinite distances)
        efficiency = calculate_global_efficiency(graph)
        assert efficiency >= 0.0

    def test_global_efficiency_empty_graph(self):
        """Global efficiency of empty graph (no edges) is 0."""
        adj_matrix = np.zeros((3, 3))
        graph = create_graph_from_adjacency(adj_matrix)
        efficiency = calculate_global_efficiency(graph)
        assert efficiency == 0.0


class TestLocalEfficiency:
    """Tests for local efficiency calculation."""

    def test_local_efficiency_complete_graph(self):
        """Local efficiency of complete graph should be 1.0 for all nodes."""
        adj_matrix = np.ones((4, 4)) - np.eye(4)
        graph = create_graph_from_adjacency(adj_matrix)
        local_effs = calculate_local_efficiency(graph)
        assert len(local_effs) == 4
        for eff in local_effs:
            assert np.isclose(eff, 1.0)

    def test_local_efficiency_star_graph(self):
        """Local efficiency of center node in star graph."""
        # Star graph: node 0 connected to 1, 2, 3; 1,2,3 not connected to each other
        adj_matrix = np.array([
            [0, 1, 1, 1],
            [1, 0, 0, 0],
            [1, 0, 0, 0],
            [1, 0, 0, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        local_effs = calculate_local_efficiency(graph)
        # Center node (0) neighbors are not connected, so local efficiency is 0
        assert local_effs[0] == 0.0
        # Leaf nodes have no neighbors in their neighborhood, so efficiency is 0
        assert local_effs[1] == 0.0


class TestClusteringCoefficient:
    """Tests for clustering coefficient calculation."""

    def test_clustering_coefficient_complete_graph(self):
        """Clustering coefficient of complete graph should be 1.0."""
        adj_matrix = np.ones((4, 4)) - np.eye(4)
        graph = create_graph_from_adjacency(adj_matrix)
        clustering = calculate_clustering_coefficient(graph)
        assert np.isclose(clustering, 1.0)

    def test_clustering_coefficient_star_graph(self):
        """Clustering coefficient of star graph center is 0."""
        adj_matrix = np.array([
            [0, 1, 1, 1],
            [1, 0, 0, 0],
            [1, 0, 0, 0],
            [1, 0, 0, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        clustering = calculate_clustering_coefficient(graph)
        # Center has 3 neighbors, 0 edges between them -> local clustering 0
        # Leaves have 1 neighbor, undefined local clustering (0 by convention)
        assert clustering == 0.0

    def test_clustering_coefficient_triangle(self):
        """Clustering coefficient of a single triangle."""
        adj_matrix = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        clustering = calculate_clustering_coefficient(graph)
        assert np.isclose(clustering, 1.0)


class TestDegreeCentrality:
    """Tests for degree centrality calculation."""

    def test_degree_centrality_complete_graph(self):
        """Degree centrality of complete graph nodes should be (n-1)/(n-1) = 1."""
        n = 5
        adj_matrix = np.ones((n, n)) - np.eye(n)
        graph = create_graph_from_adjacency(adj_matrix)
        degree_centrality = calculate_degree_centrality(graph)
        # Should return dict or list of centrality values
        if isinstance(degree_centrality, dict):
            values = list(degree_centrality.values())
        else:
            values = degree_centrality
        for val in values:
            assert np.isclose(val, 1.0)

    def test_degree_centrality_star_graph(self):
        """Degree centrality of star graph center vs leaves."""
        adj_matrix = np.array([
            [0, 1, 1, 1],
            [1, 0, 0, 0],
            [1, 0, 0, 0],
            [1, 0, 0, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        degree_centrality = calculate_degree_centrality(graph)
        if isinstance(degree_centrality, dict):
            values = [degree_centrality[i] for i in range(4)]
        else:
            values = degree_centrality
        # Center (node 0) has degree 3, normalized: 3/(4-1) = 1.0
        assert np.isclose(values[0], 1.0)
        # Leaves have degree 1, normalized: 1/(4-1) = 0.333...
        for i in [1, 2, 3]:
            assert np.isclose(values[i], 1/3)


class TestShortestPathLength:
    """Tests for shortest path length calculation."""

    def test_shortest_path_length_direct_connection(self):
        """Shortest path between directly connected nodes is 1."""
        adj_matrix = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        path_lengths = calculate_shortest_path_length(graph)
        # Path from 0 to 1 should be 1
        assert path_lengths[0][1] == 1.0

    def test_shortest_path_length_indirect_connection(self):
        """Shortest path between indirectly connected nodes."""
        # 0-1-2 chain
        adj_matrix = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        path_lengths = calculate_shortest_path_length(graph)
        # Path from 0 to 2 should be 2
        assert path_lengths[0][2] == 2.0

    def test_shortest_path_length_disconnected(self):
        """Shortest path between disconnected nodes is infinity."""
        adj_matrix = np.array([
            [0, 1, 0],
            [1, 0, 0],
            [0, 0, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        path_lengths = calculate_shortest_path_length(graph)
        # Path from 0 to 2 should be inf
        assert np.isinf(path_lengths[0][2])

    def test_shortest_path_length_self(self):
        """Shortest path from node to itself is 0."""
        adj_matrix = np.array([
            [0, 1],
            [1, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        path_lengths = calculate_shortest_path_length(graph)
        assert path_lengths[0][0] == 0.0


class TestIntegration:
    """Integration tests combining multiple metrics."""

    def test_full_metric_suite(self):
        """Calculate all metrics for a sample graph."""
        adj_matrix = np.array([
            [0, 1, 1, 0],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [0, 1, 1, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)

        # Calculate all metrics
        global_eff = calculate_global_efficiency(graph)
        local_effs = calculate_local_efficiency(graph)
        clustering = calculate_clustering_coefficient(graph)
        degree_cent = calculate_degree_centrality(graph)
        path_lengths = calculate_shortest_path_length(graph)

        # Verify we got results
        assert global_eff > 0
        assert len(local_effs) == 4
        assert clustering >= 0
        assert len(degree_cent) == 4 if isinstance(degree_cent, dict) else len(degree_cent) == 4
        assert path_lengths.shape == (4, 4)

    def test_symmetric_adjacency_matrix(self):
        """Ensure metrics are calculated correctly for symmetric adjacency."""
        adj_matrix = np.array([
            [0, 0.5, 0.2, 0.1],
            [0.5, 0, 0.3, 0.4],
            [0.2, 0.3, 0, 0.6],
            [0.1, 0.4, 0.6, 0]
        ])
        graph = create_graph_from_adjacency(adj_matrix)
        global_eff = calculate_global_efficiency(graph)
        assert global_eff > 0
        assert global_eff <= 1.0