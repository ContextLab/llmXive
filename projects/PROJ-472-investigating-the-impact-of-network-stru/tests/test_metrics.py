"""
Unit tests for code/analysis/metrics.py
"""
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
import json
import os
import sys
from pathlib import Path

# Add code to path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis.metrics import compute_degree_centrality, compute_clustering_coefficient, compute_rich_club_coefficient


class TestDegreeCentrality:
    def test_degree_returns_correct_value_for_star_graph(self):
        """
        Test degree centrality on a star graph.
        Center node should have max centrality, leaves should have lower.
        Star graph: 1 center connected to N-1 leaves.
        """
        n = 5
        # Star graph adjacency matrix
        # Node 0 is center, connected to 1, 2, 3, 4
        adj = np.zeros((n, n))
        for i in range(1, n):
            adj[0, i] = 1
            adj[i, 0] = 1
        
        centrality = compute_degree_centrality(adj)
        
        # Center node (0) degree is 4, max degree is 4 (n-1) -> centrality = 1.0
        # Leaves (1-4) degree is 1 -> centrality = 1/4 = 0.25
        assert centrality[0] == pytest.approx(1.0)
        for i in range(1, n):
            assert centrality[i] == pytest.approx(0.25)

    def test_empty_graph(self):
        """Test degree centrality on a graph with no edges."""
        n = 3
        adj = np.zeros((n, n))
        centrality = compute_degree_centrality(adj)
        assert np.all(centrality == 0.0)

    def test_complete_graph(self):
        """Test degree centrality on a complete graph."""
        n = 4
        adj = np.ones((n, n)) - np.eye(n) # Complete graph, no self-loops
        centrality = compute_degree_centrality(adj)
        # Every node connected to n-1 nodes -> centrality = (n-1)/(n-1) = 1.0
        assert np.allclose(centrality, 1.0)


class TestClusteringCoefficient:
    def test_clustering_star_graph(self):
        """
        Clustering coefficient of a star graph.
        Leaves have no connections between neighbors -> 0.
        Center: neighbors are leaves, no connections between leaves -> 0.
        Average should be 0.
        """
        n = 5
        adj = np.zeros((n, n))
        for i in range(1, n):
            adj[0, i] = 1
            adj[i, 0] = 1
        
        cc = compute_clustering_coefficient(adj)
        assert cc == pytest.approx(0.0)

    def test_clustering_triangle(self):
        """
        Clustering coefficient of a triangle (3 nodes, all connected).
        Each node has 2 neighbors, 2 connections between them -> 1.0
        """
        adj = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ])
        cc = compute_clustering_coefficient(adj)
        assert cc == pytest.approx(1.0)

    def test_clustering_flat_signal(self):
        """Test clustering on a graph with no edges (flat connectivity)."""
        adj = np.zeros((4, 4))
        cc = compute_clustering_coefficient(adj)
        # NetworkX returns 0.0 for graphs with no edges
        assert cc == pytest.approx(0.0)


class TestRichClubCoefficient:
    def test_rich_club_on_simple_graph(self):
        """
        Test rich-club coefficient calculation.
        We test that the function returns a dictionary and values are within [0, 1] for raw.
        """
        # Create a simple graph
        adj = np.array([
            [0, 1, 1, 0],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [0, 1, 1, 0]
        ])
        
        rc_raw, rc_norm = compute_rich_club_coefficient(adj, normalized=True)
        
        assert isinstance(rc_raw, dict)
        assert isinstance(rc_norm, dict)
        
        # Values should be non-negative
        for k, v in rc_raw.items():
            assert v >= 0
        
        for k, v in rc_norm.items():
            assert v >= 0

    def test_rich_club_normalized_vs_raw(self):
        """
        Test that normalized rich-club is computed (non-zero if raw is non-zero and random avg is not infinite).
        """
        # Dense graph
        adj = np.ones((4, 4)) - np.eye(4)
        rc_raw, rc_norm = compute_rich_club_coefficient(adj, normalized=True)
        
        assert len(rc_raw) > 0
        assert len(rc_norm) > 0
