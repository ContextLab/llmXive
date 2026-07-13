"""
Unit tests for graph metric calculation functions.
Tests degree, efficiency, clustering coefficient, and path length calculations.
"""
import numpy as np
import networkx as nx
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
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
    """Tests for graph construction from adjacency matrices."""

    def test_create_graph_from_adjacency_binary(self):
        """Test creating a graph from a binary adjacency matrix."""
        adj_matrix = np.array([
            [0, 1, 1, 0],
            [1, 0, 1, 1],
            [1, 1, 0, 0],
            [0, 1, 0, 0]
        ], dtype=float)

        G = create_graph_from_adjacency(adj_matrix)

        assert isinstance(G, nx.Graph)
        assert G.number_of_nodes() == 4
        assert G.number_of_edges() == 4

    def test_create_graph_from_adjacency_weighted(self):
        """Test creating a graph from a weighted adjacency matrix."""
        adj_matrix = np.array([
            [0, 0.5, 0.8, 0.0],
            [0.5, 0, 0.9, 0.3],
            [0.8, 0.9, 0, 0.0],
            [0.0, 0.3, 0.0, 0]
        ], dtype=float)

        G = create_graph_from_adjacency(adj_matrix, weighted=True)

        assert isinstance(G, nx.Graph)
        assert G.number_of_nodes() == 4
        assert G.number_of_edges() == 4
        assert G[0][1]['weight'] == pytest.approx(0.5)
        assert G[0][2]['weight'] == pytest.approx(0.8)

    def test_create_graph_from_adjacency_symmetric(self):
        """Test that non-symmetric matrices are handled (made symmetric)."""
        adj_matrix = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [1, 0, 0]
        ], dtype=float)

        G = create_graph_from_adjacency(adj_matrix)

        # Should be symmetric
        assert G.number_of_nodes() == 3
        # Edge (0,2) should exist because (2,0) exists
        assert G.has_edge(0, 2)


class TestDegreeCentrality:
    """Tests for degree centrality calculations."""

    def test_degree_centrality_complete_graph(self):
        """Test degree centrality on a complete graph."""
        n = 5
        adj_matrix = np.ones((n, n)) - np.eye(n)

        G = create_graph_from_adjacency(adj_matrix)
        centrality = calculate_degree_centrality(G)

        # In a complete graph, degree centrality should be (n-1)/(n-1) = 1.0
        for node in G.nodes():
            assert centrality[node] == pytest.approx(1.0)

    def test_degree_centrality_star_graph(self):
        """Test degree centrality on a star graph."""
        # Star graph: node 0 connected to all others
        adj_matrix = np.zeros((5, 5))
        for i in range(1, 5):
            adj_matrix[0, i] = 1
            adj_matrix[i, 0] = 1

        G = create_graph_from_adjacency(adj_matrix)
        centrality = calculate_degree_centrality(G)

        # Center node should have highest centrality
        assert centrality[0] == pytest.approx(1.0)
        # Leaf nodes should have lower centrality
        for i in range(1, 5):
            assert centrality[i] == pytest.approx(0.25)  # 1/(n-1)


class TestGlobalEfficiency:
    """Tests for global efficiency calculations."""

    def test_global_efficiency_complete_graph(self):
        """Test global efficiency on a complete graph."""
        n = 5
        adj_matrix = np.ones((n, n)) - np.eye(n)

        G = create_graph_from_adjacency(adj_matrix)
        efficiency = calculate_global_efficiency(G)

        # In a complete graph, efficiency should be 1.0
        assert efficiency == pytest.approx(1.0)

    def test_global_efficiency_disconnected_graph(self):
        """Test global efficiency on a disconnected graph."""
        # Two disconnected nodes
        adj_matrix = np.array([
            [0, 0],
            [0, 0]
        ], dtype=float)

        G = create_graph_from_adjacency(adj_matrix)
        efficiency = calculate_global_efficiency(G)

        # Disconnected graph should have efficiency 0
        assert efficiency == pytest.approx(0.0)


class TestClusteringCoefficient:
    """Tests for clustering coefficient calculations."""

    def test_clustering_coefficient_complete_graph(self):
        """Test clustering coefficient on a complete graph."""
        n = 5
        adj_matrix = np.ones((n, n)) - np.eye(n)

        G = create_graph_from_adjacency(adj_matrix)
        clustering = calculate_clustering_coefficient(G)

        # In a complete graph, clustering coefficient should be 1.0
        assert clustering == pytest.approx(1.0)

    def test_clustering_coefficient_tree(self):
        """Test clustering coefficient on a tree (should be 0)."""
        # Star graph is a tree
        adj_matrix = np.zeros((5, 5))
        for i in range(1, 5):
            adj_matrix[0, i] = 1
            adj_matrix[i, 0] = 1

        G = create_graph_from_adjacency(adj_matrix)
        clustering = calculate_clustering_coefficient(G)

        # Trees have no triangles, so clustering coefficient is 0
        assert clustering == pytest.approx(0.0)


class TestLocalEfficiency:
    """Tests for local efficiency calculations."""

    def test_local_efficiency_complete_graph(self):
        """Test local efficiency on a complete graph."""
        n = 5
        adj_matrix = np.ones((n, n)) - np.eye(n)

        G = create_graph_from_adjacency(adj_matrix)
        efficiency = calculate_local_efficiency(G)

        # In a complete graph, local efficiency should be 1.0
        assert efficiency == pytest.approx(1.0)


class TestShortestPathLength:
    """Tests for shortest path length calculations."""

    def test_shortest_path_length_complete_graph(self):
        """Test shortest path length on a complete graph."""
        n = 5
        adj_matrix = np.ones((n, n)) - np.eye(n)

        G = create_graph_from_adjacency(adj_matrix)
        avg_path_length = calculate_shortest_path_length(G)

        # In a complete graph, all paths are length 1
        assert avg_path_length == pytest.approx(1.0)

    def test_shortest_path_length_line_graph(self):
        """Test shortest path length on a line graph."""
        # Line graph: 0-1-2-3-4
        adj_matrix = np.zeros((5, 5))
        for i in range(4):
            adj_matrix[i, i+1] = 1
            adj_matrix[i+1, i] = 1

        G = create_graph_from_adjacency(adj_matrix)
        avg_path_length = calculate_shortest_path_length(G)

        # Average path length for line graph of 5 nodes is 2.0
        # Paths: (0,1)=1, (0,2)=2, (0,3)=3, (0,4)=4,
        #        (1,2)=1, (1,3)=2, (1,4)=3,
        #        (2,3)=1, (2,4)=2,
        #        (3,4)=1
        # Sum = 1+2+3+4+1+2+3+1+2+1 = 20
        # Count = 10 pairs
        # Average = 20/10 = 2.0
        assert avg_path_length == pytest.approx(2.0)
