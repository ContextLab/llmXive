"""
Unit tests for the graph constructor module.
"""

import numpy as np
import pytest
import networkx as nx
from pathlib import Path

from src.graphs.constructor import (
    build_graph_from_coordinates,
    construct_graphs_from_samples,
    export_graph_to_dict,
    GraphConstructionError
)


class TestBuildGraphFromCoordinates:
    """Tests for the build_graph_from_coordinates function."""

    def test_empty_coordinates(self):
        """Test handling of empty coordinate array."""
        coords = np.array([]).reshape(0, 2)
        graph = build_graph_from_coordinates(coords, threshold=2.0, sample_id="test")

        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0
        assert graph.graph["is_empty"] is True
        assert graph.graph["sample_id"] == "test"

    def test_single_node(self):
        """Test graph with a single node (no edges possible)."""
        coords = np.array([[0.0, 0.0]])
        graph = build_graph_from_coordinates(coords, threshold=2.0, sample_id="single")

        assert graph.number_of_nodes() == 1
        assert graph.number_of_edges() == 0
        assert graph.graph["density"] == 0.0

    def test_two_nodes_within_threshold(self):
        """Test two nodes within threshold should have an edge."""
        coords = np.array([[0.0, 0.0], [1.0, 0.0]])  # Distance = 1.0
        graph = build_graph_from_coordinates(coords, threshold=2.0, sample_id="two_close")

        assert graph.number_of_nodes() == 2
        assert graph.number_of_edges() == 1
        assert graph.has_edge(0, 1)

    def test_two_nodes_outside_threshold(self):
        """Test two nodes outside threshold should not have an edge."""
        coords = np.array([[0.0, 0.0], [5.0, 0.0]])  # Distance = 5.0
        graph = build_graph_from_coordinates(coords, threshold=2.0, sample_id="two_far")

        assert graph.number_of_nodes() == 2
        assert graph.number_of_edges() == 0

    def test_grid_pattern(self):
        """Test a 3x3 grid with known edge count."""
        # Create 3x3 grid with spacing 1.0
        coords = []
        for x in range(3):
            for y in range(3):
                coords.append([x * 1.0, y * 1.0])
        coords = np.array(coords)

        # Threshold 1.5 should connect horizontal and vertical neighbors
        graph = build_graph_from_coordinates(coords, threshold=1.5, sample_id="grid")

        assert graph.number_of_nodes() == 9
        # Each internal node has 4 neighbors, edge nodes have 3, corners have 2
        # Total edges: 3*2 (horizontal) + 3*2 (vertical) = 12
        assert graph.number_of_edges() == 12

    def test_invalid_coordinate_shape(self):
        """Test that invalid coordinate shape raises error."""
        coords = np.array([[0.0, 0.0, 0.0]])  # 3D coordinates
        with pytest.raises(GraphConstructionError):
            build_graph_from_coordinates(coords, threshold=2.0, sample_id="invalid")

    def test_graph_metadata(self):
        """Test that graph contains all expected metadata."""
        coords = np.array([[0.0, 0.0], [1.0, 0.0]])
        graph = build_graph_from_coordinates(
            coords, threshold=2.0, sample_id="meta_test", material="MoS2"
        )

        assert graph.graph["sample_id"] == "meta_test"
        assert graph.graph["material"] == "MoS2"
        assert graph.graph["threshold"] == 2.0
        assert "node_count" in graph.graph
        assert "edge_count" in graph.graph
        assert "density" in graph.graph

    def test_degree_calculation(self):
        """Test that node degrees are correctly calculated."""
        # Create a star graph: center at (0,0), leaves at distance 1.0
        coords = np.array([
            [0.0, 0.0],  # center
            [1.0, 0.0],  # leaf 1
            [0.0, 1.0],  # leaf 2
            [-1.0, 0.0], # leaf 3
            [0.0, -1.0]  # leaf 4
        ])
        graph = build_graph_from_coordinates(coords, threshold=1.5, sample_id="star")

        # Center node should have degree 4
        assert graph.degree(0) == 4
        # Leaf nodes should have degree 1
        for i in range(1, 5):
            assert graph.degree(i) == 1


class TestConstructGraphsFromSamples:
    """Tests for the construct_graphs_from_samples function."""

    def test_multiple_samples(self):
        """Test constructing graphs from multiple samples."""
        samples = [
            {
                "sample_id": "sample1",
                "coordinates": np.array([[0.0, 0.0], [1.0, 0.0]])
            },
            {
                "sample_id": "sample2",
                "coordinates": np.array([[0.0, 0.0], [5.0, 0.0]])
            }
        ]

        results = construct_graphs_from_samples(samples)

        assert len(results) == 2
        sample_ids = [r[0] for r in results]
        assert "sample1" in sample_ids
        assert "sample2" in sample_ids

    def test_missing_sample_id(self):
        """Test handling of sample missing sample_id."""
        samples = [
            {
                "coordinates": np.array([[0.0, 0.0]])
            }
        ]

        results = construct_graphs_from_samples(samples)
        assert len(results) == 0

    def test_missing_coordinates(self):
        """Test handling of sample missing coordinates."""
        samples = [
            {
                "sample_id": "no_coords"
            }
        ]

        results = construct_graphs_from_samples(samples)
        assert len(results) == 0

    def test_mixed_valid_invalid(self):
        """Test mix of valid and invalid samples."""
        samples = [
            {
                "sample_id": "valid1",
                "coordinates": np.array([[0.0, 0.0], [1.0, 0.0]])
            },
            {
                "coordinates": np.array([[0.0, 0.0]])  # Missing sample_id
            },
            {
                "sample_id": "valid2",
                "coordinates": np.array([[0.0, 0.0]])
            }
        ]

        results = construct_graphs_from_samples(samples)
        assert len(results) == 2
        sample_ids = [r[0] for r in results]
        assert "valid1" in sample_ids
        assert "valid2" in sample_ids


class TestExportGraphToDict:
    """Tests for the export_graph_to_dict function."""

    def test_basic_export(self):
        """Test basic graph export to dictionary."""
        coords = np.array([[0.0, 0.0], [1.0, 0.0]])
        graph = build_graph_from_coordinates(coords, threshold=2.0, sample_id="export_test")

        graph_dict = export_graph_to_dict(graph)

        assert graph_dict["sample_id"] == "export_test"
        assert graph_dict["node_count"] == 2
        assert graph_dict["edge_count"] == 1
        assert len(graph_dict["nodes"]) == 2
        assert len(graph_dict["edges"]) == 1

    def test_node_structure(self):
        """Test that exported nodes have correct structure."""
        coords = np.array([[0.0, 0.0], [1.0, 0.0]])
        graph = build_graph_from_coordinates(coords, threshold=2.0, sample_id="node_test")

        graph_dict = export_graph_to_dict(graph)
        node = graph_dict["nodes"][0]

        assert "id" in node
        assert "x" in node
        assert "y" in node
        assert "degree" in node

    def test_edge_structure(self):
        """Test that exported edges have correct structure."""
        coords = np.array([[0.0, 0.0], [1.0, 0.0]])
        graph = build_graph_from_coordinates(coords, threshold=2.0, sample_id="edge_test")

        graph_dict = export_graph_to_dict(graph)
        edge = graph_dict["edges"][0]

        assert "source" in edge
        assert "target" in edge
        assert "weight" in edge

    def test_empty_graph_export(self):
        """Test export of empty graph."""
        coords = np.array([]).reshape(0, 2)
        graph = build_graph_from_coordinates(coords, threshold=2.0, sample_id="empty")

        graph_dict = export_graph_to_dict(graph)

        assert graph_dict["is_empty"] is True
        assert graph_dict["node_count"] == 0
        assert graph_dict["edge_count"] == 0
        assert len(graph_dict["nodes"]) == 0
        assert len(graph_dict["edges"]) == 0