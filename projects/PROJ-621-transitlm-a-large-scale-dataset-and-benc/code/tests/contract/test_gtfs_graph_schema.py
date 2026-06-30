"""
Contract tests for the GTFSGraph schema.

Verifies that the Pydantic model correctly enforces:
- Required fields (nodes, edges, metadata)
- Data constraints (non-empty lists)
- Map-free property (no coordinates in StationNode)
"""
import pytest
from pydantic import ValidationError
from src.contracts.models import GTFSGraph, StationNode, TransferEdge, TransitLine


class TestGTFSGraphSchema:
    """Tests for the GTFSGraph Pydantic model."""

    def test_valid_graph(self):
        """Test that a valid graph is accepted."""
        data = {
            "metadata": {"source": "nyc_gtfs", "date": "2023-10-01"},
            "nodes": [
                {"station_id": "A", "name": "Station A"},
                {"station_id": "B", "name": "Station B"}
            ],
            "edges": [
                {"from_station_id": "A", "to_station_id": "B", "transfer_type": 0}
            ],
            "lines": [
                {"line_id": "L1", "short_name": "L"}
            ]
        }
        graph = GTFSGraph(**data)
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

    def test_missing_nodes(self):
        """Test that missing 'nodes' field raises ValidationError."""
        data = {
            "metadata": {"source": "nyc_gtfs"},
            # "nodes" missing
            "edges": [],
            "lines": []
        }
        with pytest.raises(ValidationError):
            GTFSGraph(**data)

    def test_empty_nodes_list(self):
        """Test that an empty nodes list raises ValidationError."""
        data = {
            "metadata": {"source": "nyc_gtfs"},
            "nodes": [],
            "edges": [],
            "lines": []
        }
        with pytest.raises(ValidationError) as exc_info:
            GTFSGraph(**data)
        
        assert "At least one node is required" in str(exc_info.value)

    def test_empty_edges_allowed(self):
        """Test that an empty edges list is allowed (isolated nodes)."""
        data = {
            "metadata": {"source": "nyc_gtfs"},
            "nodes": [{"station_id": "A", "name": "Station A"}],
            "edges": [],
            "lines": []
        }
        graph = GTFSGraph(**data)
        assert len(graph.edges) == 0

    def test_station_node_no_coordinates(self):
        """
        Test that StationNode does not accept latitude/longitude.
        """
        data = {
            "station_id": "A",
            "name": "Station A",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
        # Pydantic ignores extra fields by default. We verify the fields aren't defined.
        node = StationNode(**data)
        assert not hasattr(node, 'latitude')
        assert not hasattr(node, 'longitude')

    def test_invalid_station_id_empty(self):
        """Test that an empty station_id raises ValidationError."""
        data = {
            "station_id": "",
            "name": "Station A"
        }
        with pytest.raises(ValidationError):
            StationNode(**data)

    def test_invalid_transfer_edge_missing_stations(self):
        """Test that missing station IDs in TransferEdge raise ValidationError."""
        data = {
            "from_station_id": "",
            "to_station_id": "B"
        }
        with pytest.raises(ValidationError):
            TransferEdge(**data)
