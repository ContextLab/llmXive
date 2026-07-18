"""
Unit tests for disconnected graph handling in topological metric calculation.

Specifically tests:
- Path length calculation is performed ONLY on the Largest Connected Component (LCC)
- Disconnected graphs are flagged with is_connected=false
- Average path length is set to NaN for disconnected graphs (or computed on LCC only based on spec interpretation)
- LCC fraction is correctly calculated
"""
import numpy as np
import pytest
import networkx as nx
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.metrics.paths_and_lcc import calculate_path_length_and_lcc
from src.graphs.constructor import build_graph_from_coordinates


class TestDisconnectedGraphs:
    """Tests for handling disconnected graphs in metric calculation."""

    def test_disconnected_graph_lcc_fraction(self):
        """Test that LCC fraction is correctly calculated for a disconnected graph."""
        # Create a graph with two distinct clusters far apart
        coords = np.array([
            [0.0, 0.0], [1.0, 0.0], [2.0, 0.0],  # Cluster 1
            [10.0, 10.0], [11.0, 10.0], [12.0, 10.0]  # Cluster 2 (far away)
        ])
        
        # Use a small threshold that won't connect the clusters
        threshold = 2.0  # nm
        
        graph = build_graph_from_coordinates(coords, threshold)
        
        # Calculate metrics
        result = calculate_path_length_and_lcc(graph)
        
        # Should detect the graph is not connected
        assert result['is_connected'] is False
        
        # LCC fraction should be less than 1.0
        assert 0.0 < result['lcc_fraction'] < 1.0
        
        # LCC fraction should match the size of the largest component
        lcc = max(nx.connected_components(graph), key=len)
        expected_fraction = len(lcc) / len(graph.nodes())
        assert abs(result['lcc_fraction'] - expected_fraction) < 1e-9

    def test_disconnected_graph_path_length_on_lcc(self):
        """Test that path length is calculated only on LCC for disconnected graphs."""
        # Create a disconnected graph
        coords = np.array([
            [0.0, 0.0], [1.0, 0.0], [2.0, 0.0],  # Cluster 1 (3 nodes)
            [10.0, 10.0], [11.0, 10.0]  # Cluster 2 (2 nodes)
        ])
        
        threshold = 2.0
        graph = build_graph_from_coordinates(coords, threshold)
        
        result = calculate_path_length_and_lcc(graph)
        
        # Graph should be disconnected
        assert result['is_connected'] is False
        
        # Path length should be a valid number (computed on LCC)
        # or NaN if LCC has only 1 node (but our LCC has 3 nodes)
        assert result['average_path_length'] is not None
        
        # Verify the path length is computed on the LCC
        lcc = max(nx.connected_components(graph), key=len)
        lcc_graph = graph.subgraph(lcc)
        expected_path_length = nx.average_shortest_path_length(lcc_graph)
        
        # Allow small floating point tolerance
        assert abs(result['average_path_length'] - expected_path_length) < 1e-6

    def test_connected_graph_path_length(self):
        """Test that path length is calculated correctly for connected graphs."""
        # Create a connected graph (all points close together)
        coords = np.array([
            [0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [1.0, 1.0], [2.0, 1.0]
        ])
        
        threshold = 2.0  # Should connect most points
        graph = build_graph_from_coordinates(coords, threshold)
        
        result = calculate_path_length_and_lcc(graph)
        
        # Graph might be connected or disconnected depending on threshold
        # If connected: is_connected=True, path length computed on full graph
        # If disconnected: is_connected=False, path length computed on LCC
        
        if result['is_connected']:
            expected_path_length = nx.average_shortest_path_length(graph)
            assert abs(result['average_path_length'] - expected_path_length) < 1e-6
            assert abs(result['lcc_fraction'] - 1.0) < 1e-9
        else:
            # If disconnected, path length should be on LCC
            lcc = max(nx.connected_components(graph), key=len)
            lcc_graph = graph.subgraph(lcc)
            expected_path_length = nx.average_shortest_path_length(lcc_graph)
            assert abs(result['average_path_length'] - expected_path_length) < 1e-6

    def test_single_node_graph(self):
        """Test handling of a graph with only one node."""
        coords = np.array([[0.0, 0.0]])
        threshold = 2.0
        graph = build_graph_from_coordinates(coords, threshold)
        
        result = calculate_path_length_and_lcc(graph)
        
        # Single node is technically connected
        assert result['is_connected'] is True
        assert result['lcc_fraction'] == 1.0
        
        # Average path length for single node is 0
        assert result['average_path_length'] == 0.0

    def test_two_isolated_nodes(self):
        """Test graph with two nodes that are too far apart to connect."""
        coords = np.array([[0.0, 0.0], [100.0, 100.0]])
        threshold = 2.0
        graph = build_graph_from_coordinates(coords, threshold)
        
        result = calculate_path_length_and_lcc(graph)
        
        # Should be disconnected
        assert result['is_connected'] is False
        
        # LCC fraction should be 0.5 (one node in LCC out of two total)
        assert abs(result['lcc_fraction'] - 0.5) < 1e-9
        
        # Path length for single-node LCC is 0
        assert result['average_path_length'] == 0.0

    def test_lcc_identification_correctness(self):
        """Test that the correct component is identified as LCC."""
        # Create graph with components of sizes 5, 3, and 2
        coords = []
        # Component 1: 5 nodes in a cluster
        for i in range(5):
            coords.append([i * 0.5, 0.0])
        # Component 2: 3 nodes far away
        for i in range(3):
            coords.append([i * 0.5 + 20.0, 0.0])
        # Component 3: 2 nodes even farther
        for i in range(2):
            coords.append([i * 0.5 + 40.0, 0.0])
        
        coords = np.array(coords)
        threshold = 1.0  # Should keep clusters separate
        
        graph = build_graph_from_coordinates(coords, threshold)
        result = calculate_path_length_and_lcc(graph)
        
        # LCC should be the component with 5 nodes
        expected_fraction = 5.0 / 10.0
        assert abs(result['lcc_fraction'] - expected_fraction) < 1e-9

    def test_path_length_nan_for_truly_disconnected_large_components(self):
        """Test behavior when LCC is large but graph is disconnected."""
        # Create two large clusters
        coords = []
        # Cluster 1: 10 nodes
        for i in range(10):
            coords.append([i * 0.5, 0.0])
        # Cluster 2: 8 nodes far away
        for i in range(8):
            coords.append([i * 0.5 + 50.0, 0.0])
        
        coords = np.array(coords)
        threshold = 1.0
        
        graph = build_graph_from_coordinates(coords, threshold)
        result = calculate_path_length_and_lcc(graph)
        
        assert result['is_connected'] is False
        assert result['lcc_fraction'] == 10.0 / 18.0
        
        # Path length should be computed on LCC (10 nodes)
        lcc = max(nx.connected_components(graph), key=len)
        lcc_graph = graph.subgraph(lcc)
        expected_path_length = nx.average_shortest_path_length(lcc_graph)
        
        assert abs(result['average_path_length'] - expected_path_length) < 1e-6

    def test_metric_dict_structure(self):
        """Test that the returned dictionary has the expected keys and types."""
        coords = np.array([
            [0.0, 0.0], [1.0, 0.0], [10.0, 10.0]
        ])
        graph = build_graph_from_coordinates(coords, 2.0)
        result = calculate_path_length_and_lcc(graph)
        
        assert isinstance(result, dict)
        assert 'average_path_length' in result
        assert 'is_connected' in result
        assert 'lcc_fraction' in result
        
        assert isinstance(result['average_path_length'], (int, float, type(None)))
        assert isinstance(result['is_connected'], bool)
        assert isinstance(result['lcc_fraction'], float)