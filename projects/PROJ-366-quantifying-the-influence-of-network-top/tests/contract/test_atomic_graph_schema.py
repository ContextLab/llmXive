"""
Contract test for AtomicGraph schema (T007a).
Validates that the schema file exists, is valid YAML, and can be loaded
by the jsonschema library.
"""
import os
import pytest
import json
import yaml
from jsonschema import validate, ValidationError
from pathlib import Path

# Resolve path relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "atomic_graph.schema.yaml"

@pytest.fixture
def schema():
    """Load the AtomicGraph schema."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_sample_graph():
    """Create a minimal valid graph instance for testing."""
    return {
        "nodes": [
            {
                "id": 0,
                "coords": [0.0, 0.0, 0.0],
                "degree": 4,
                "clustering_coeff": 0.5
            },
            {
                "id": 1,
                "coords": [2.35, 0.0, 0.0],
                "degree": 4,
                "clustering_coeff": 0.3
            }
        ],
        "edges": [
            [0, 1]
        ],
        "metadata": {
            "cutoff_distance": 3.0,
            "atom_count": 2,
            "bond_count": 1,
            "source_file": "sample_01.xyz"
        }
    }

@pytest.fixture
def invalid_node_missing_coords():
    """Create an invalid graph with missing coords."""
    return {
        "nodes": [
            {
                "id": 0,
                "degree": 4,
                "clustering_coeff": 0.5
            }
        ],
        "edges": [],
        "metadata": {
            "cutoff_distance": 3.0,
            "atom_count": 1,
            "bond_count": 0,
            "source_file": "test.xyz"
        }
    }

@pytest.fixture
def invalid_edge_format():
    """Create an invalid graph with malformed edges."""
    return {
        "nodes": [
            {
                "id": 0,
                "coords": [0.0, 0.0, 0.0],
                "degree": 0,
                "clustering_coeff": 0.0
            }
        ],
        "edges": [
            [0, 1, 2]  # Edge must be exactly 2 items
        ],
        "metadata": {
            "cutoff_distance": 3.0,
            "atom_count": 1,
            "bond_count": 1,
            "source_file": "test.xyz"
        }
    }

def test_schema_loads_and_is_valid_json_schema(schema):
    """Test that the schema is valid YAML and conforms to JSON Schema structure."""
    assert "type" in schema
    assert schema["type"] == "object"
    assert "required" in schema
    assert "properties" in schema

def test_valid_graph_passes_validation(schema, valid_sample_graph):
    """Test that a valid graph instance passes schema validation."""
    validate(instance=valid_sample_graph, schema=schema)

def test_missing_coords_fails_validation(schema, invalid_node_missing_coords):
    """Test that missing 'coords' field causes validation failure."""
    with pytest.raises(ValidationError):
        validate(instance=invalid_node_missing_coords, schema=schema)

def test_invalid_edge_format_fails_validation(schema, invalid_edge_format):
    """Test that malformed edge array causes validation failure."""
    with pytest.raises(ValidationError):
        validate(instance=invalid_edge_format, schema=schema)

def test_schema_structure_matches_requirements(schema):
    """Verify the schema explicitly defines the required structure from T007a."""
    # Check nodes structure
    assert "nodes" in schema["properties"]
    node_item = schema["properties"]["nodes"]["items"]
    assert "id" in node_item["properties"]
    assert "coords" in node_item["properties"]
    assert "degree" in node_item["properties"]
    assert "clustering_coeff" in node_item["properties"]
    
    # Check coords constraints
    coords_prop = node_item["properties"]["coords"]
    assert coords_prop["minItems"] == 3
    assert coords_prop["maxItems"] == 3

def test_schema_file_is_readable():
    """Test that the schema file is readable and valid YAML."""
    assert SCHEMA_PATH.exists()
    with open(SCHEMA_PATH, 'r') as f:
        try:
            yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Schema file is not valid YAML: {e}")