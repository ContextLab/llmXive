"""
Unit tests for the Regression Schema (T016a).

These tests verify that the data structures and schema definitions
correctly model the requirements for the regression analysis phase.
"""
import pytest
import json
from pathlib import Path
import sys

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from contracts.regression_schema import (
    RegressionRecord,
    get_regression_schema,
    validate_record,
    create_empty_regression_dataset
)


class TestRegressionRecord:
    """Tests for the RegressionRecord dataclass."""

    def test_create_record(self):
        """Test instantiation of a valid RegressionRecord."""
        record = RegressionRecord(
            simulation_id="sim_001",
            topology_type="barabasi_albert",
            network_size=500,
            assortativity=0.15,
            average_path_length=3.2,
            clustering_coefficient=0.45,
            density=0.01,
            is_connected=True
        )
        assert record.simulation_id == "sim_001"
        assert record.topology_type == "barabasi_albert"
        assert record.network_size == 500
        assert record.is_connected is True

    def test_to_dict(self):
        """Test conversion to dictionary."""
        record = RegressionRecord(
            simulation_id="sim_002",
            topology_type="erdos_renyi",
            network_size=500,
            assortativity=0.0,
            average_path_length=4.0,
            clustering_coefficient=0.02,
            density=0.005,
            is_connected=True
        )
        data = record.to_dict()
        assert isinstance(data, dict)
        assert data["simulation_id"] == "sim_002"
        assert "gamma" not in data  # Explicitly checking T016a constraint

    def test_from_dict(self):
        """Test reconstruction from dictionary."""
        data = {
            "simulation_id": "sim_003",
            "topology_type": "watts_strogatz",
            "network_size": 500,
            "assortativity": -0.1,
            "average_path_length": 2.8,
            "clustering_coefficient": 0.6,
            "density": 0.02,
            "is_connected": True
        }
        record = RegressionRecord.from_dict(data)
        assert record.simulation_id == "sim_003"
        assert record.topology_type == "watts_strogatz"


class TestSchemaDefinition:
    """Tests for the JSON Schema definition."""

    def test_schema_structure(self):
        """Verify the schema has the correct top-level keys."""
        schema = get_regression_schema()
        assert "$schema" in schema
        assert "title" in schema
        assert "properties" in schema
        assert "metadata" in schema["properties"]
        assert "records" in schema["properties"]

    def test_schema_enum_validation(self):
        """Verify that topology_type is restricted to valid enums."""
        schema = get_regression_schema()
        items_schema = schema["properties"]["records"]["items"]
        topology_enum = items_schema["properties"]["topology_type"]["enum"]
        
        assert "erdos_renyi" in topology_enum
        assert "barabasi_albert" in topology_enum
        assert "watts_strogatz" in topology_enum
        assert len(topology_enum) == 3

    def test_schema_required_fields(self):
        """Verify all required fields are present in the schema."""
        schema = get_regression_schema()
        items_schema = schema["properties"]["records"]["items"]
        required = items_schema["required"]
        
        expected_fields = [
            "simulation_id", "topology_type", "network_size",
            "assortativity", "average_path_length",
            "clustering_coefficient", "density", "is_connected"
        ]
        assert set(required) == set(expected_fields)

    def test_missing_gamma_flag(self):
        """Verify the schema expects missing_gamma flag in metadata."""
        schema = get_regression_schema()
        metadata_props = schema["properties"]["metadata"]["properties"]
        assert "missing_gamma" in metadata_props
        assert metadata_props["missing_gamma"]["const"] is True


class TestValidationLogic:
    """Tests for runtime validation functions."""

    def test_validate_record_valid(self):
        """Test validation of a correct record."""
        record = {
            "simulation_id": "s1",
            "topology_type": "erdos_renyi",
            "network_size": 100,
            "assortativity": 0.0,
            "average_path_length": 5.0,
            "clustering_coefficient": 0.1,
            "density": 0.05,
            "is_connected": True
        }
        assert validate_record(record) is True

    def test_validate_record_invalid_topology(self):
        """Test validation fails on invalid topology type."""
        record = {
            "simulation_id": "s1",
            "topology_type": "invalid_topology",
            "network_size": 100,
            "assortativity": 0.0,
            "average_path_length": 5.0,
            "clustering_coefficient": 0.1,
            "density": 0.05,
            "is_connected": True
        }
        assert validate_record(record) is False

    def test_validate_record_missing_field(self):
        """Test validation fails on missing required field."""
        record = {
            "simulation_id": "s1",
            "topology_type": "erdos_renyi",
            # Missing network_size
            "assortativity": 0.0,
            "average_path_length": 5.0,
            "clustering_coefficient": 0.1,
            "density": 0.05,
            "is_connected": True
        }
        assert validate_record(record) is False


class TestDatasetCreation:
    """Tests for empty dataset creation."""

    def test_empty_dataset_structure(self):
        """Verify empty dataset has correct metadata and empty records."""
        dataset = create_empty_regression_dataset()
        assert "metadata" in dataset
        assert "records" in dataset
        assert dataset["records"] == []
        assert dataset["metadata"]["missing_gamma"] is True
        assert dataset["metadata"]["version"] == "1.0.0"