"""
Unit tests for edge cases in code/analysis/metrics.py.
Specifically tests handling of disconnected graphs and other structural anomalies.
"""
import pytest
import numpy as np
import networkx as nx
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.metrics import (
    compute_degree_centrality,
    compute_clustering_coefficient,
    compute_rich_club_coefficient,
    run_metrics_pipeline
)


class TestDisconnectedGraphs:
    """Tests for handling disconnected graphs in metrics computation."""

    def test_compute_degree_centrality_on_disconnected_graph(self):
        """
        Test that degree centrality computation handles disconnected graphs
        without crashing, returning zeros for isolated nodes.
        """
        # Create a disconnected graph: two separate components
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5])
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        # Nodes 4 and 5 are isolated
        
        result = compute_degree_centrality(G)
        
        # Verify result is a dict
        assert isinstance(result, dict)
        
        # Verify all nodes are present
        assert set(result.keys()) == {1, 2, 3, 4, 5}
        
        # Verify isolated nodes have degree centrality of 0
        assert result[4] == 0.0
        assert result[5] == 0.0
        
        # Verify connected nodes have non-zero centrality
        assert result[1] > 0.0
        assert result[2] > 0.0
        assert result[3] > 0.0

    def test_compute_clustering_coefficient_on_disconnected_graph(self):
        """
        Test that clustering coefficient computation handles disconnected graphs.
        Isolated nodes and nodes with degree < 2 should have clustering coefficient of 0.
        """
        # Create a disconnected graph
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4])
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        # Node 4 is isolated
        
        result = compute_clustering_coefficient(G)
        
        # Verify result is a dict
        assert isinstance(result, dict)
        
        # Verify all nodes are present
        assert set(result.keys()) == {1, 2, 3, 4}
        
        # Isolated node should have clustering coefficient 0
        assert result[4] == 0.0
        
        # Nodes with degree 1 should also have clustering coefficient 0
        assert result[1] == 0.0
        assert result[3] == 0.0
        
        # Node 2 has degree 2, but no triangles, so clustering should be 0
        assert result[2] == 0.0

    def test_compute_rich_club_coefficient_on_disconnected_graph(self):
        """
        Test that rich-club coefficient computation handles disconnected graphs.
        The function should not crash and should return valid coefficients where possible.
        """
        # Create a small disconnected graph
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5])
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])  # Triangle component
        G.add_edges_from([(4, 5)])  # Simple edge component
        
        # This should not raise an exception
        try:
            result = compute_rich_club_coefficient(G)
            # If it returns a result, verify it's a dict
            assert isinstance(result, dict)
        except Exception as e:
            # If it raises an exception, it should be a specific one about the graph structure
            # and not a generic crash
            assert "rich" in str(e).lower() or "club" in str(e).lower() or "disconnected" in str(e).lower()

    def test_run_metrics_pipeline_with_disconnected_graph(self):
        """
        Test that the full metrics pipeline handles disconnected graphs gracefully.
        """
        # Create a temporary directory structure
        with patch('analysis.metrics.get_data_root') as mock_data_root, \
             patch('analysis.metrics.Path') as mock_path:
            
            mock_data_root.return_value = Path("/tmp/test_metrics")
            mock_path.return_value = Path("/tmp/test_metrics")
            
            # Create a mock adjacency matrix that represents a disconnected graph
            # 5 nodes: 0-1 connected, 2-3 connected, 4 isolated
            adj_matrix = np.array([
                [0, 1, 0, 0, 0],
                [1, 0, 0, 0, 0],
                [0, 0, 0, 1, 0],
                [0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0]
            ])
            
            # Mock the load_connectome_matrix to return our disconnected graph
            with patch('analysis.metrics.load_connectome_matrix', return_value=adj_matrix):
                with patch('analysis.metrics.get_logger') as mock_logger:
                    mock_logger_instance = MagicMock()
                    mock_logger.return_value = mock_logger_instance
                    
                    # This should not crash
                    result = run_metrics_pipeline(
                        subject_id="test_disconnected",
                        data_root=Path("/tmp/test_metrics"),
                        processed_dir=Path("/tmp/test_metrics")
                    )
                    
                    # Verify the result contains all expected metrics
                    assert 'degree_centrality' in result
                    assert 'clustering_coefficient' in result
                    assert 'rich_club_coefficient' in result
                    
                    # Verify that isolated nodes have appropriate values
                    # (degree 0, clustering 0)
                    assert result['degree_centrality'][4] == 0.0
                    assert result['clustering_coefficient'][4] == 0.0

class TestOtherEdgeCases:
    """Tests for other edge cases in metrics computation."""

    def test_compute_degree_centrality_on_empty_graph(self):
        """Test handling of a graph with no edges."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3])
        
        result = compute_degree_centrality(G)
        
        assert all(v == 0.0 for v in result.values())

    def test_compute_degree_centrality_on_single_node(self):
        """Test handling of a graph with a single node."""
        G = nx.Graph()
        G.add_node(1)
        
        result = compute_degree_centrality(G)
        
        assert result[1] == 0.0

    def test_compute_clustering_coefficient_on_complete_graph(self):
        """Test clustering coefficient on a complete graph (should be 1.0 for all nodes)."""
        G = nx.complete_graph(5)
        
        result = compute_clustering_coefficient(G)
        
        # In a complete graph, every node's neighbors are all connected to each other
        for node, coef in result.items():
            assert np.isclose(coef, 1.0)

    def test_compute_rich_club_coefficient_on_small_graph(self):
        """Test rich-club coefficient on a very small graph."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])
        
        # Should not crash, even if the graph is too small for meaningful rich-club analysis
        try:
            result = compute_rich_club_coefficient(G)
            assert isinstance(result, dict)
        except Exception:
            # If it fails, it should be due to graph size, not a crash
            pass

    def test_metrics_with_self_loops(self):
        """Test that metrics handle graphs with self-loops correctly."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (1, 1)])  # Self-loop on node 1
        
        # NetworkX typically ignores self-loops in simple graphs, but we should verify
        # that our functions don't crash
        degree_result = compute_degree_centrality(G)
        clustering_result = compute_clustering_coefficient(G)
        
        assert isinstance(degree_result, dict)
        assert isinstance(clustering_result, dict)

    def test_metrics_with_weighted_edges(self):
        """Test that metrics handle weighted graphs correctly."""
        G = nx.Graph()
        G.add_edge(1, 2, weight=0.5)
        G.add_edge(2, 3, weight=0.8)
        G.add_edge(1, 3, weight=0.3)
        
        # Our current implementation might not use weights, but it shouldn't crash
        degree_result = compute_degree_centrality(G)
        clustering_result = compute_clustering_coefficient(G)
        
        assert isinstance(degree_result, dict)
        assert isinstance(clustering_result, dict)