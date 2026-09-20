"""
Contract tests for schema validation.
Validates that generated data artifacts conform to the defined JSON schemas.
"""
import json
import pytest
from pathlib import Path
from typing import Any, Dict

import yaml
import jsonschema

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"


def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON schema from the contracts directory."""
    schema_path = CONTRACTS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def validate_data_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate data against a schema using jsonschema."""
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Data validation failed: {e.message}")


class TestAtomicGraphSchema:
    """Tests for the AtomicGraph schema (T007a)."""

    @pytest.fixture
    def schema(self):
        return load_schema("atomic_graph.schema.yaml")

    def test_schema_loads(self, schema):
        """Verify the schema file is valid YAML and loads correctly."""
        assert schema is not None
        assert "type" in schema
        assert schema["type"] == "object"

    def test_valid_sample_passes(self, schema):
        """Test that a valid atomic graph structure passes validation."""
        valid_data = {
            "graph_id": "sample_01",
            "cutoff_distance": 3.0,
            "nodes": [
                {
                    "id": 0,
                    "coords": [0.0, 0.0, 0.0],
                    "degree": 4,
                    "clustering_coeff": 0.0
                },
                {
                    "id": 1,
                    "coords": [2.35, 0.0, 0.0],
                    "degree": 4,
                    "clustering_coeff": 0.0
                }
            ],
            "edges": [
                [0, 1],
                [1, 0]
            ]
        }
        validate_data_against_schema(valid_data, schema)

    def test_missing_required_field_fails(self, schema):
        """Test that missing a required field causes validation failure."""
        invalid_data = {
            "graph_id": "sample_01",
            # Missing 'nodes' and 'edges'
            "cutoff_distance": 3.0
        }
        with pytest.raises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(instance=invalid_data, schema=schema)

    def test_invalid_coord_dimension_fails(self, schema):
        """Test that coords with wrong dimension fails."""
        invalid_data = {
            "graph_id": "sample_01",
            "cutoff_distance": 3.0,
            "nodes": [
                {
                    "id": 0,
                    "coords": [0.0, 0.0],  # Should be 3D
                    "degree": 4,
                    "clustering_coeff": 0.0
                }
            ],
            "edges": []
        }
        with pytest.raises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(instance=invalid_data, schema=schema)

    def test_invalid_clustering_coeff_fails(self, schema):
        """Test that clustering coefficient outside [0, 1] fails."""
        invalid_data = {
            "graph_id": "sample_01",
            "cutoff_distance": 3.0,
            "nodes": [
                {
                    "id": 0,
                    "coords": [0.0, 0.0, 0.0],
                    "degree": 4,
                    "clustering_coeff": 1.5  # Invalid
                }
            ],
            "edges": []
        }
        with pytest.raises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(instance=invalid_data, schema=schema)


class TestThermalSampleSchema:
    """Tests for the ThermalSample schema (T007b)."""

    @pytest.fixture
    def schema(self):
        return load_schema("thermal_sample.schema.yaml")

    def test_schema_loads(self, schema):
        assert schema is not None

    def test_valid_sample_passes(self, schema):
        valid_data = {
            "graph_id": "sample_01",
            "conductivity": 1.45,
            "converged": True,
            "metadata": {
                "timestep": 1.0,
                "temperature": 300.0
            }
        }
        validate_data_against_schema(valid_data, schema)


class TestGNNOutputSchema:
    """Tests for the GNNOutput schema (T007c)."""

    @pytest.fixture
    def schema(self):
        return load_schema("gnn_output.schema.yaml")

    def test_schema_loads(self, schema):
        assert schema is not None

    def test_valid_output_passes(self, schema):
        valid_data = {
            "predicted_flux": [0.1, 0.2, 0.15],
            "loss": 0.0045,
            "epoch": 100
        }
        validate_data_against_schema(valid_data, schema)