"""
Unit tests for graph construction functionality.
"""

import numpy as np
import pytest
import networkx as nx
from pathlib import Path

from src.graphs.constructor import (
    GraphConstructionError,
    build_graph_from_coordinates,
    construct_graphs_from_samples,
    export_graph_to_dict
)


class TestBuildGraphFromCoordinates:
    """Tests for the build_graph_from_coordinates function."""

    def test_basic_graph_construction(self):
        """Test basic graph construction from a small set of coordinates."""
        coordinates = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [2.0, 2.0]
        ])
        threshold = 1.5

        G = build_graph_from_coordinates(coordinates, threshold, sample_id="test_001")

        assert G.number_of_nodes() == 4
        # Node 0 (0,0) should connect to node 1 (1,0) and node 2 (0,1)
        # Node 3 (2,2) is too far from others
        assert G.number_of_edges() == 2
        assert G.has_edge(0, 1)
        assert G.has_edge(0, 2)
        assert not G.has_edge(0, 3)
        assert not G.has_edge(1, 3)
        assert not G.has_edge(2, 3)

    def test_threshold_edge_cases(self):
        """Test behavior at threshold boundaries."""
        # Create two points exactly at threshold distance
        coordinates = np.array([
            [0.0, 0.0],
            [2.0, 0.0]
        ])

        # At threshold: should have edge
        G_at = build_graph_from_coordinates(coordinates, 2.0, sample_id="test_002")
        assert G_at.number_of_edges() == 1

        # Below threshold: should not have edge
        G_below = build_graph_from_coordinates(coordinates, 1.9, sample_id="test_003")
        assert G_below.number_of_edges() == 0

    def test_empty_coordinates_raises_error(self):
        """Test that empty coordinates raise GraphConstructionError."""
        with pytest.raises(GraphConstructionError):
            build_graph_from_coordinates(np.array([]), 2.0, sample_id="test_empty")

    def test_none_coordinates_raises_error(self):
        """Test that None coordinates raise GraphConstructionError."""
        with pytest.raises(GraphConstructionError):
            build_graph_from_coordinates(None, 2.0, sample_id="test_none")

    def test_invalid_shape_coordinates_raises_error(self):
        """Test that invalid coordinate shapes raise GraphConstructionError."""
        # 1D array
        with pytest.raises(GraphConstructionError):
            build_graph_from_coordinates(np.array([0.0, 1.0, 2.0]), 2.0, sample_id="test_1d")

        # Wrong number of columns
        with pytest.raises(GraphConstructionError):
            build_graph_from_coordinates(np.array([[0.0, 1.0, 2.0]]), 2.0, sample_id="test_3col")

    def test_single_node_graph(self):
        """Test graph construction with a single node."""
        coordinates = np.array([[0.0, 0.0]])
        G = build_graph_from_coordinates(coordinates, 2.0, sample_id="test_single")

        assert G.number_of_nodes() == 1
        assert G.number_of_edges() == 0

    def test_edge_weight_calculation(self):
        """Test that edge weights are correctly calculated as distances."""
        coordinates = np.array([
            [0.0, 0.0],
            [3.0, 4.0]  # Distance = 5.0
        ])
        G = build_graph_from_coordinates(coordinates, 10.0, sample_id="test_weight")

        assert G.has_edge(0, 1)
        weight = G[0][1]['weight']
        assert np.isclose(weight, 5.0)


class TestConstructGraphsFromSamples:
    """Tests for the construct_graphs_from_samples function."""

    def test_multiple_samples(self):
        """Test constructing graphs from multiple samples."""
        samples = [
            {
                'sample_id': 'sample_1',
                'coordinates': np.array([[0.0, 0.0], [1.0, 0.0]])
            },
            {
                'sample_id': 'sample_2',
                'coordinates': np.array([[0.0, 0.0], [10.0, 10.0]])
            }
        ]
        threshold = 2.0

        results = construct_graphs_from_samples(samples, threshold)

        assert len(results) == 2

        # First sample should have 1 edge
        assert results[0]['node_count'] == 2
        assert results[0]['edge_count'] == 1
        assert results[0]['density'] == 1.0

        # Second sample should have 0 edges (too far apart)
        assert results[1]['node_count'] == 2
        assert results[1]['edge_count'] == 0
        assert results[1]['density'] == 0.0

    def test_mixed_valid_invalid_samples(self):
        """Test handling of samples with missing coordinates."""
        samples = [
            {
                'sample_id': 'valid_sample',
                'coordinates': np.array([[0.0, 0.0], [1.0, 0.0]])
            },
            {
                'sample_id': 'missing_coords'
                # No coordinates key
            }
        ]
        threshold = 2.0

        results = construct_graphs_from_samples(samples, threshold)

        # Should only return the valid sample
        assert len(results) == 1
        assert results[0]['sample_id'] == 'valid_sample'

    def test_graph_attribute_preservation(self):
        """Test that graphs are properly stored in results."""
        samples = [
            {
                'sample_id': 'test_graph',
                'coordinates': np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
            }
        ]
        threshold = 2.0

        results = construct_graphs_from_samples(samples, threshold)

        assert 'graph' in results[0]
        assert isinstance(results[0]['graph'], nx.Graph)
        assert results[0]['graph'].number_of_nodes() == 3


class TestExportGraphToDict:
    """Tests for the export_graph_to_dict function."""

    def test_basic_export(self):
        """Test basic graph export to dictionary."""
        G = nx.Graph()
        G.add_node(0, x=0.0, y=0.0)
        G.add_node(1, x=1.0, y=0.0)
        G.add_edge(0, 1, weight=1.0)

        result = export_graph_to_dict(G, sample_id="export_test")

        assert result['sample_id'] == 'export_test'
        assert result['metadata']['node_count'] == 2
        assert result['metadata']['edge_count'] == 1
        assert len(result['nodes']) == 2
        assert len(result['edges']) == 1

    def test_node_attributes_preserved(self):
        """Test that node position attributes are correctly exported."""
        G = nx.Graph()
        G.add_node(0, x=5.0, y=10.0)
        G.add_node(1, x=15.0, y=20.0)

        result = export_graph_to_dict(G, sample_id="attrs_test")

        nodes = {n['id']: n for n in result['nodes']}
        assert nodes[0]['x'] == 5.0
        assert nodes[0]['y'] == 10.0
        assert nodes[1]['x'] == 15.0
        assert nodes[1]['y'] == 20.0

    def test_edge_weights_preserved(self):
        """Test that edge weights are correctly exported."""
        G = nx.Graph()
        G.add_node(0, x=0.0, y=0.0)
        G.add_node(1, x=3.0, y=4.0)
        G.add_edge(0, 1, weight=5.0)

        result = export_graph_to_dict(G, sample_id="weights_test")

        assert result['edges'][0]['weight'] == 5.0

    def test_density_calculation(self):
        """Test that density is correctly calculated in export."""
        G = nx.complete_graph(4)  # 4 nodes, 6 edges, max edges = 6, density = 1.0

        result = export_graph_to_dict(G, sample_id="density_test")

        assert result['metadata']['density'] == 1.0

    def test_empty_graph_export(self):
        """Test export of an empty graph."""
        G = nx.Graph()

        result = export_graph_to_dict(G, sample_id="empty_test")

        assert result['metadata']['node_count'] == 0
        assert result['metadata']['edge_count'] == 0
        assert result['metadata']['density'] == 0.0
        assert result['metadata']['is_connected'] is False

    def test_additional_metadata(self):
        """Test that additional metadata is merged correctly."""
        G = nx.Graph()
        G.add_node(0, x=0.0, y=0.0)

        result = export_graph_to_dict(
            G,
            sample_id="meta_test",
            metadata={'custom_field': 'custom_value', 'threshold_used': 2.0}
        )

        assert result['metadata']['custom_field'] == 'custom_value'
        assert result['metadata']['threshold_used'] == 2.0

    def test_is_connected_flag(self):
        """Test that is_connected flag is correctly set."""
        # Connected graph
        G_connected = nx.Graph()
        G_connected.add_edges_from([(0, 1), (1, 2)])
        result_connected = export_graph_to_dict(G_connected, sample_id="connected")
        assert result_connected['metadata']['is_connected'] is True

        # Disconnected graph
        G_disconnected = nx.Graph()
        G_disconnected.add_edges_from([(0, 1), (2, 3)])
        result_disconnected = export_graph_to_dict(G_disconnected, sample_id="disconnected")
        assert result_disconnected['metadata']['is_connected'] is False
