"""
Unit tests for graph metric calculation.
"""
import pytest
import numpy as np
import networkx as nx

from utils.graph import (
    create_graph_from_adjacency,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_degree_centrality,
    calculate_local_efficiency,
    calculate_shortest_path_length
)


class TestGraphMetrics:
    def test_create_graph_from_adjacency(self):
        """Test graph creation from adjacency matrix."""
        # Create a simple 5x5 adjacency matrix
        adj = np.array([
            [0, 1, 1, 0, 0],
            [1, 0, 1, 1, 0],
            [1, 1, 0, 0, 1],
            [0, 1, 0, 0, 1],
            [0, 0, 1, 1, 0]
        ], dtype=float)
        
        G = create_graph_from_adjacency(adj)
        
        assert G is not None
        assert isinstance(G, nx.Graph)
        assert G.number_of_nodes() == 5
        assert G.number_of_edges() == 6

    def test_calculate_degree_centrality(self):
        """Test degree centrality calculation."""
        adj = np.array([
            [0, 1, 1, 0],
            [1, 0, 1, 1],
            [1, 1, 0, 0],
            [0, 1, 0, 0]
        ], dtype=float)
        
        G = create_graph_from_adjacency(adj)
        centrality = calculate_degree_centrality(G)
        
        assert len(centrality) == 4
        # Node 1 (index 1) should have highest degree (3)
        assert centrality[1] > centrality[0]

    def test_calculate_clustering_coefficient(self):
        """Test clustering coefficient calculation."""
        # Create a triangle
        adj = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ], dtype=float)
        
        G = create_graph_from_adjacency(adj)
        clustering = calculate_clustering_coefficient(G)
        
        assert clustering is not None
        # In a complete triangle, clustering should be 1.0
        assert abs(clustering - 1.0) < 1e-6

    def test_calculate_global_efficiency(self):
        """Test global efficiency calculation."""
        # Create a simple connected graph
        adj = np.array([
            [0, 1, 0, 0],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0]
        ], dtype=float)
        
        G = create_graph_from_adjacency(adj)
        efficiency = calculate_global_efficiency(G)
        
        assert efficiency is not None
        assert efficiency > 0
        assert efficiency <= 1.0

    def test_calculate_local_efficiency(self):
        """Test local efficiency calculation."""
        adj = np.array([
            [0, 1, 1, 0],
            [1, 0, 1, 1],
            [1, 1, 0, 0],
            [0, 1, 0, 0]
        ], dtype=float)
        
        G = create_graph_from_adjacency(adj)
        local_eff = calculate_local_efficiency(G)
        
        assert local_eff is not None
        assert local_eff > 0

    def test_calculate_shortest_path_length(self):
        """Test shortest path length calculation."""
        adj = np.array([
            [0, 1, 0, 0],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0]
        ], dtype=float)
        
        G = create_graph_from_adjacency(adj)
        paths = calculate_shortest_path_length(G)
        
        assert paths is not None
        # Path from node 0 to node 3 should be 3 hops
        assert paths[0][3] == 3

    def test_graph_with_disconnected_nodes(self):
        """Test handling of disconnected graphs."""
        adj = np.array([
            [0, 1, 0, 0],
            [1, 0, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0]
        ], dtype=float)
        
        G = create_graph_from_adjacency(adj)
        
        # Global efficiency should be lower for disconnected graph
        efficiency = calculate_global_efficiency(G)
        assert efficiency is not None
        
        # Shortest path between disconnected nodes should be infinity
        paths = calculate_shortest_path_length(G)
        assert np.isinf(paths[0][2])
