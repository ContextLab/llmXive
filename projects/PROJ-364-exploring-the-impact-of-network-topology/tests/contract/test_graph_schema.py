import json
import yaml
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

# Load the schema
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "graph.schema.yaml"

@pytest.fixture
def schema():
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_graph_data():
    return {
        "sample_id": "sample_001",
        "material_type": "graphene",
        "threshold_nm": 2.0,
        "nodes": [
            {"id": 0, "x": 0.0, "y": 0.0},
            {"id": 1, "x": 1.5, "y": 1.5},
            {"id": 2, "x": 3.0, "y": 0.0}
        ],
        "edges": [
            {"source": 0, "target": 1, "distance_nm": 2.12},
            {"source": 1, "target": 2, "distance_nm": 2.12}
        ],
        "metrics": {
            "node_count": 3,
            "edge_count": 2,
            "density": 0.666,
            "average_degree": 1.333,
            "global_clustering_coefficient": 0.0,
            "average_path_length": 1.5,
            "is_connected": True,
            "lcc_fraction": 1.0,
            "percolation_threshold": None,
            "degree_distribution": {"1": 0, "2": 3},
            "zero_defect_flag": False
        },
        "metadata": {
            "created_at": "2023-10-27T10:00:00Z",
            "source_file": "data/raw/sample_001.csv",
            "checksum": "abc123def456",
            "lattice_correction_applied": False,
            "r_lattice_nm": 0.246
        }
    }

@pytest.fixture
def valid_zero_defect_data():
    return {
        "sample_id": "sample_002",
        "material_type": "MoS2",
        "threshold_nm": 2.0,
        "nodes": [],
        "edges": [],
        "metrics": {
            "node_count": 0,
            "edge_count": 0,
            "density": 0.0,
            "average_degree": 0.0,
            "global_clustering_coefficient": None,
            "average_path_length": None,
            "is_connected": False,
            "lcc_fraction": 0.0,
            "percolation_threshold": None,
            "degree_distribution": {},
            "zero_defect_flag": True
        },
        "metadata": {
            "created_at": "2023-10-27T10:00:00Z",
            "source_file": "data/raw/sample_002.csv",
            "checksum": "xyz789",
            "lattice_correction_applied": False,
            "r_lattice_nm": 0.316
        }
    }

def test_graph_schema_validates_correct_data(schema, valid_graph_data):
    """Test that a valid graph object passes validation."""
    validate(instance=valid_graph_data, schema=schema)

def test_graph_schema_handles_null_clustering(schema, valid_zero_defect_data):
    """Test that null values for clustering/path length are allowed for zero-defect cases."""
    validate(instance=valid_zero_defect_data, schema=schema)

def test_graph_schema_rejects_missing_required_fields(schema, valid_graph_data):
    """Test that missing required fields cause validation failure."""
    invalid_data = valid_graph_data.copy()
    del invalid_data["sample_id"]
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_graph_schema_rejects_invalid_material_type(schema, valid_graph_data):
    """Test that invalid material types are rejected."""
    invalid_data = valid_graph_data.copy()
    invalid_data["material_type"] = "unknown_material"
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_graph_schema_rejects_missing_metadata_fields(schema, valid_graph_data):
    """Test that missing metadata fields cause validation failure."""
    invalid_data = valid_graph_data.copy()
    invalid_data["metadata"] = {"created_at": "2023-10-27T10:00:00Z"}
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_graph_schema_allows_null_percolation_threshold(schema, valid_graph_data):
    """Test that null percolation_threshold is allowed."""
    valid_graph_data["metrics"]["percolation_threshold"] = None
    validate(instance=valid_graph_data, schema=schema)

def test_graph_schema_validates_edge_structure(schema, valid_graph_data):
    """Test that edges must have source, target, and distance_nm."""
    invalid_edge = valid_graph_data["edges"].copy()
    invalid_edge[0] = {"source": 0, "target": 1} # Missing distance
    invalid_data = valid_graph_data.copy()
    invalid_data["edges"] = invalid_edge
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)
