"""
Unit tests for the graph serializer (T016)
"""

import json
import tempfile
from pathlib import Path

import networkx as nx
import numpy as np
import pytest

from src.graphs.serializer import (
    serialize_graph_to_dict,
    serialize_graphs_to_file,
    SerializationError,
    _sanitize_value,
)


class TestSanitizeValue:
    def test_sanitize_none(self):
        assert _sanitize_value(None) is None

    def test_sanitize_int(self):
        assert _sanitize_value(42) == 42

    def test_sanitize_float(self):
        assert _sanitize_value(3.14) == 3.14

    def test_sanitize_nan(self):
        result = _sanitize_value(float('nan'))
        assert result is None

    def test_sanitize_infinity(self):
        result = _sanitize_value(float('inf'))
        assert result is None

    def test_sanitize_list(self):
        result = _sanitize_value([1, 2, 3])
        assert result == [1, 2, 3]

    def test_sanitize_dict(self):
        result = _sanitize_value({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    def test_sanitize_set(self):
        result = _sanitize_value({3, 1, 2})
        assert result == [1, 2, 3]

    def test_sanitize_numpy_float(self):
        val = np.float64(2.5)
        result = _sanitize_value(val)
        assert isinstance(result, float)
        assert result == 2.5


class TestSerializeGraphToDict:
    @pytest.fixture
    def simple_graph(self):
        G = nx.Graph()
        G.add_node(0, x=0.0, y=0.0, defect_type="vacancy")
        G.add_node(1, x=1.0, y=0.0, defect_type="interstitial")
        G.add_edge(0, 1, distance=1.0)
        return G

    def test_basic_serialization(self, simple_graph):
        result = serialize_graph_to_dict(
            simple_graph,
            sample_id="test_001",
            material="graphene",
            threshold=2.0
        )

        assert result["sample_id"] == "test_001"
        assert result["material"] == "graphene"
        assert result["threshold_nm"] == 2.0
        assert result["node_count"] == 2
        assert result["edge_count"] == 1
        assert "nodes" in result
        assert "edges" in result
        assert "checksum" in result

    def test_node_extraction(self, simple_graph):
        result = serialize_graph_to_dict(
            simple_graph,
            sample_id="test_001",
            material="graphene",
            threshold=2.0
        )

        nodes = result["nodes"]
        assert len(nodes) == 2

        # Check first node
        assert nodes[0]["id"] == 0
        assert nodes[0]["attributes"]["x"] == 0.0
        assert nodes[0]["attributes"]["y"] == 0.0
        assert nodes[0]["attributes"]["defect_type"] == "vacancy"

    def test_edge_extraction(self, simple_graph):
        result = serialize_graph_to_dict(
            simple_graph,
            sample_id="test_001",
            material="graphene",
            threshold=2.0
        )

        edges = result["edges"]
        assert len(edges) == 1
        assert edges[0]["source"] == 0
        assert edges[0]["target"] == 1
        assert edges[0]["attributes"]["distance"] == 1.0

    def test_metadata_inclusion(self, simple_graph):
        metadata = {"custom_field": "value", "nested": {"key": 123}}
        result = serialize_graph_to_dict(
            simple_graph,
            sample_id="test_001",
            material="graphene",
            threshold=2.0,
            metadata=metadata
        )

        assert result["metadata"]["custom_field"] == "value"
        assert result["metadata"]["nested"]["key"] == 123

    def test_empty_graph(self):
        G = nx.Graph()
        result = serialize_graph_to_dict(
            G,
            sample_id="empty_001",
            material="graphene",
            threshold=2.0
        )

        assert result["node_count"] == 0
        assert result["edge_count"] == 0
        assert result["nodes"] == []
        assert result["edges"] == []

    def test_invalid_input_type(self):
        with pytest.raises(SerializationError):
            serialize_graph_to_dict(
                "not a graph",
                sample_id="test",
                material="graphene",
                threshold=2.0
            )


class TestSerializeGraphsToFile:
    @pytest.fixture
    def graphs_data(self):
        G1 = nx.Graph()
        G1.add_node(0, x=0.0, y=0.0)
        G1.add_edge(0, 0, distance=0.0)  # Self-loop for testing

        G2 = nx.Graph()
        G2.add_node(1, x=1.0, y=1.0)
        G2.add_node(2, x=2.0, y=2.0)
        G2.add_edge(1, 2, distance=1.414)

        return [
            (G1, "sample_001", "graphene", 2.0, None),
            (G2, "sample_002", "MoS2", 2.5, {"source": "synthetic"}),
        ]

    def test_write_to_file(self, graphs_data):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            samples = serialize_graphs_to_file(
                graphs_data,
                output_path,
                overwrite=True
            )

            assert len(samples) == 2
            assert "sample_001" in samples
            assert "sample_002" in samples

            # Verify file content
            with open(output_path, 'r') as f:
                content = json.load(f)

            assert len(content) == 2
            assert content[0]["sample_id"] == "sample_001"
            assert content[1]["sample_id"] == "sample_002"

            # Verify manifest was created
            manifest_path = output_path.with_suffix('.json.sha256')
            assert manifest_path.exists()

        finally:
            output_path.unlink(missing_ok=True)
            manifest_path = output_path.with_suffix('.json.sha256')
            if manifest_path.exists():
                manifest_path.unlink()

    def test_file_exists_error(self, graphs_data):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            with pytest.raises(FileExistsError):
                serialize_graphs_to_file(graphs_data, output_path, overwrite=False)
        finally:
            output_path.unlink(missing_ok=True)

    def test_overwrite_existing(self, graphs_data):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            # Write once
            serialize_graphs_to_file(graphs_data, output_path, overwrite=True)

            # Write again with overwrite
            samples = serialize_graphs_to_file(
                graphs_data,
                output_path,
                overwrite=True
            )

            assert len(samples) == 2

        finally:
            output_path.unlink(missing_ok=True)
            manifest_path = output_path.with_suffix('.json.sha256')
            if manifest_path.exists():
                manifest_path.unlink()