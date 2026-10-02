"""
Contract tests for graph schema validation.
These tests ensure that the validation logic in validate_graphs.py
correctly enforces the schema defined in dataset_graph.schema.yaml.
"""
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import yaml

from src.data.validate_graphs import (
    load_schema,
    validate_node_attributes,
    validate_edge_attributes,
    validate_graph_metadata,
    validate_graph_structure,
    validate_graph,
    GraphValidationError
)

@pytest.fixture
def sample_schema():
    """Load the actual schema file for testing."""
    schema_path = Path(__file__).resolve().parent.parent.parent / "contracts" / "dataset_graph.schema.yaml"
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_nodes():
    """Create valid node data."""
    return [
        {
            "atomic_number": 46,
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "is_metal": True,
            "ligand_class": "Group_13",
            "formal_charge": 0
        },
        {
            "atomic_number": 6,
            "x": 1.5,
            "y": 0.0,
            "z": 0.0,
            "is_metal": False,
            "ligand_class": "Group_13",
            "formal_charge": 0
        }
    ]

@pytest.fixture
def valid_edges():
    """Create valid edge data."""
    return [
        {
            "source": 0,
            "target": 1,
            "distance": 1.5,
            "edge_type": "coordination"
        }
    ]

@pytest.fixture
def valid_metadata():
    """Create valid metadata."""
    return {
        "energy_dft": -1234.567,
        "barrier_height": 15.5,
        "metal_center": 46,
        "ligand_class": "Group_13",
        "reaction_id": "test_reaction_001",
        "geometry_source": "QM9-TS",
        "is_outlier": False,
        "cutoff_used": 3.5
    }

def test_load_schema_valid(sample_schema):
    """Test that the schema loads correctly."""
    assert sample_schema is not None
    assert "properties" in sample_schema
    assert "node_attributes" in sample_schema["properties"]
    assert "edge_attributes" in sample_schema["properties"]
    assert "graph_metadata" in sample_schema["properties"]

def test_load_schema_missing_file():
    """Test that loading a missing schema file raises an error."""
    with pytest.raises(FileNotFoundError):
        load_schema(Path("/nonexistent/path/schema.yaml"))

def test_validate_node_attributes_valid(valid_nodes, sample_schema):
    """Test validation of valid node attributes."""
    errors = validate_node_attributes(valid_nodes, sample_schema)
    assert len(errors) == 0

def test_validate_node_attributes_missing_column(valid_nodes, sample_schema):
    """Test validation fails when required column is missing."""
    invalid_nodes = [
        {
            "atomic_number": 46,
            "x": 0.0,
            "y": 0.0
            # Missing 'z' which is required
        }
    ]
    errors = validate_node_attributes(invalid_nodes, sample_schema)
    assert any("z" in error for error in errors)

def test_validate_node_attributes_wrong_type(valid_nodes, sample_schema):
    """Test validation fails when attribute has wrong type."""
    invalid_nodes = [
        {
            "atomic_number": "not_an_integer",  # Should be integer
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "is_metal": True,
            "ligand_class": "Group_13",
            "formal_charge": 0
        }
    ]
    errors = validate_node_attributes(invalid_nodes, sample_schema)
    assert any("atomic_number" in error and "integer" in error for error in errors)

def test_validate_edge_attributes_valid(valid_edges, sample_schema):
    """Test validation of valid edge attributes."""
    errors = validate_edge_attributes(valid_edges, sample_schema)
    assert len(errors) == 0

def test_validate_edge_attributes_missing_column(valid_edges, sample_schema):
    """Test validation fails when required column is missing."""
    invalid_edges = [
        {
            "source": 0,
            # Missing 'target' which is required
            "distance": 1.5,
            "edge_type": "coordination"
        }
    ]
    errors = validate_edge_attributes(invalid_edges, sample_schema)
    assert any("target" in error for error in errors)

def test_validate_edge_attributes_wrong_type(valid_edges, sample_schema):
    """Test validation fails when edge attribute has wrong type."""
    invalid_edges = [
        {
            "source": 0,
            "target": 1,
            "distance": "not_a_number",  # Should be number
            "edge_type": "coordination"
        }
    ]
    errors = validate_edge_attributes(invalid_edges, sample_schema)
    assert any("distance" in error and "number" in error for error in errors)

def test_validate_graph_metadata_valid(valid_metadata, sample_schema):
    """Test validation of valid metadata."""
    errors = validate_graph_metadata(valid_metadata, sample_schema)
    assert len(errors) == 0

def test_validate_graph_metadata_missing_field(valid_metadata, sample_schema):
    """Test validation fails when required metadata field is missing."""
    invalid_metadata = valid_metadata.copy()
    del invalid_metadata["energy_dft"]  # Required field
    errors = validate_graph_metadata(invalid_metadata, sample_schema)
    assert any("energy_dft" in error for error in errors)

def test_validate_graph_metadata_wrong_type(valid_metadata, sample_schema):
    """Test validation fails when metadata field has wrong type."""
    invalid_metadata = valid_metadata.copy()
    invalid_metadata["energy_dft"] = "not_a_number"  # Should be number
    errors = validate_graph_metadata(invalid_metadata, sample_schema)
    assert any("energy_dft" in error and "number" in error for error in errors)

def test_validate_graph_structure_valid(valid_nodes, valid_edges, sample_schema):
    """Test validation of valid graph structure."""
    errors = validate_graph_structure(valid_nodes, valid_edges, sample_schema)
    assert len(errors) == 0

def test_validate_graph_structure_self_loops_disallowed(valid_nodes, sample_schema):
    """Test that self-loops are detected as invalid."""
    edges_with_self_loop = [
        {
            "source": 0,
            "target": 0,  # Self-loop
            "distance": 0.0,
            "edge_type": "coordination"
        }
    ]
    errors = validate_graph_structure(valid_nodes, edges_with_self_loop, sample_schema)
    assert any("self-loop" in error.lower() for error in errors)

def test_validate_graph_full_valid(valid_nodes, valid_edges, valid_metadata, sample_schema):
    """Test full graph validation with valid data."""
    is_valid, errors = validate_graph(valid_nodes, valid_edges, valid_metadata, sample_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_graph_full_invalid(valid_nodes, valid_edges, valid_metadata, sample_schema):
    """Test full graph validation with invalid data."""
    # Create invalid metadata
    invalid_metadata = valid_metadata.copy()
    invalid_metadata["energy_dft"] = "not_a_number"
    
    is_valid, errors = validate_graph(valid_nodes, valid_edges, invalid_metadata, sample_schema)
    assert not is_valid
    assert len(errors) > 0

def test_validate_all_graphs_valid(tmp_path, sample_schema):
    """Test validation of a parquet file with valid graphs."""
    # Create a mock parquet file with valid graphs
    graphs_data = [
        {
            "node_attributes": [
                {"atomic_number": 46, "x": 0.0, "y": 0.0, "z": 0.0, "is_metal": True, "ligand_class": "Group_13", "formal_charge": 0}
            ],
            "edge_attributes": [
                {"source": 0, "target": 0, "distance": 0.0, "edge_type": "coordination"}
            ],
            "graph_metadata": {
                "energy_dft": -1234.567,
                "barrier_height": 15.5,
                "metal_center": 46,
                "ligand_class": "Group_13",
                "reaction_id": "test_001",
                "geometry_source": "QM9-TS",
                "is_outlier": False,
                "cutoff_used": 3.5
            }
        }
    ]
    
    # Save to parquet (simplified: storing as JSON for testing, actual implementation uses parquet)
    # For testing purposes, we'll create a DataFrame that mimics the structure
    df = pd.DataFrame([{
        "nodes": g["node_attributes"],
        "edges": g["edge_attributes"],
        "metadata": g["graph_metadata"]
    } for g in graphs_data])
    
    parquet_path = tmp_path / "test_graphs.parquet"
    df.to_parquet(parquet_path)
    
    # Validate
    valid_count, invalid_count, errors = validate_all_graphs(parquet_path, sample_schema)
    
    assert valid_count == 1
    assert invalid_count == 0
    assert len(errors) == 0

def test_validate_all_graphs_mixed(tmp_path, sample_schema):
    """Test validation of a parquet file with mixed valid/invalid graphs."""
    # Create a mock parquet file with mixed graphs
    valid_graph = {
        "nodes": [
            {"atomic_number": 46, "x": 0.0, "y": 0.0, "z": 0.0, "is_metal": True, "ligand_class": "Group_13", "formal_charge": 0}
        ],
        "edges": [
            {"source": 0, "target": 0, "distance": 0.0, "edge_type": "coordination"}
        ],
        "metadata": {
            "energy_dft": -1234.567,
            "barrier_height": 15.5,
            "metal_center": 46,
            "ligand_class": "Group_13",
            "reaction_id": "test_001",
            "geometry_source": "QM9-TS",
            "is_outlier": False,
            "cutoff_used": 3.5
        }
    }
    
    invalid_graph = {
        "nodes": [
            {"atomic_number": "not_int", "x": 0.0, "y": 0.0, "z": 0.0, "is_metal": True, "ligand_class": "Group_13", "formal_charge": 0}
        ],
        "edges": [
            {"source": 0, "target": 0, "distance": 0.0, "edge_type": "coordination"}
        ],
        "metadata": {
            "energy_dft": -1234.567,
            "barrier_height": 15.5,
            "metal_center": 46,
            "ligand_class": "Group_13",
            "reaction_id": "test_002",
            "geometry_source": "QM9-TS",
            "is_outlier": False,
            "cutoff_used": 3.5
        }
    }
    
    df = pd.DataFrame([
        {
            "nodes": valid_graph["nodes"],
            "edges": valid_graph["edges"],
            "metadata": valid_graph["metadata"]
        },
        {
            "nodes": invalid_graph["nodes"],
            "edges": invalid_graph["edges"],
            "metadata": invalid_graph["metadata"]
        }
    ])
    
    parquet_path = tmp_path / "test_graphs_mixed.parquet"
    df.to_parquet(parquet_path)
    
    # Validate
    valid_count, invalid_count, errors = validate_all_graphs(parquet_path, sample_schema)
    
    assert valid_count == 1
    assert invalid_count == 1
    assert len(errors) == 1
    assert any("atomic_number" in str(error) for error in errors[0]["errors"])