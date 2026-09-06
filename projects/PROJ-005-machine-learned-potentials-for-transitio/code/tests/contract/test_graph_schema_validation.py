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

# Sample Schema for testing
sample_schema = {
    "nodes": {
        "required": ["atomic_number", "formal_charge"],
        "types": {
            "atomic_number": "int",
            "formal_charge": "int",
            "coordination_number": "int"
        }
    },
    "edges": {
        "required": ["source", "target", "distance"],
        "types": {
            "source": "int",
            "target": "int",
            "distance": "float"
        }
    },
    "metadata": {
        "required": ["energy_dft", "barrier_height"],
        "types": {
            "energy_dft": "float",
            "barrier_height": "float",
            "ligand_class": "str"
        }
    }
}

# Valid test data
valid_nodes = pd.DataFrame([
    {"atomic_number": 28, "formal_charge": 0, "coordination_number": 4},
    {"atomic_number": 6, "formal_charge": 0, "coordination_number": 3}
])

valid_edges = pd.DataFrame([
    {"source": 0, "target": 1, "distance": 1.54},
    {"source": 1, "target": 0, "distance": 1.54}
])

valid_metadata = {
    "energy_dft": -123.45,
    "barrier_height": 15.2,
    "ligand_class": "Group 13"
}

valid_graph = (valid_nodes, valid_edges, valid_metadata)

def test_load_schema_valid(tmp_path):
    schema_file = tmp_path / "schema.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(sample_schema, f)
    
    loaded = load_schema(schema_file)
    assert loaded == sample_schema

def test_load_schema_missing_file():
    with pytest.raises(FileNotFoundError):
        load_schema(Path("/nonexistent/path/schema.yaml"))

def test_validate_node_attributes_valid():
    errors = validate_node_attributes(valid_nodes, sample_schema)
    assert len(errors) == 0

def test_validate_node_attributes_missing_column():
    bad_nodes = pd.DataFrame([{"atomic_number": 28}]) # missing formal_charge
    errors = validate_node_attributes(bad_nodes, sample_schema)
    assert any("Missing required node attributes" in e for e in errors)
    assert "formal_charge" in errors[0]

def test_validate_node_attributes_wrong_type():
    bad_nodes = pd.DataFrame([{"atomic_number": "not_an_int", "formal_charge": 0}])
    errors = validate_node_attributes(bad_nodes, sample_schema)
    assert any("expected int" in e for e in errors)

def test_validate_edge_attributes_valid():
    errors = validate_edge_attributes(valid_edges, sample_schema)
    assert len(errors) == 0

def test_validate_edge_attributes_missing_column():
    bad_edges = pd.DataFrame([{"source": 0}]) # missing target, distance
    errors = validate_edge_attributes(bad_edges, sample_schema)
    assert any("Missing required edge attributes" in e for e in errors)

def test_validate_graph_metadata_valid():
    errors = validate_graph_metadata(valid_metadata, sample_schema)
    assert len(errors) == 0

def test_validate_graph_metadata_missing_field():
    bad_meta = {"energy_dft": -123.45} # missing barrier_height
    errors = validate_graph_metadata(bad_meta, sample_schema)
    assert any("Missing required metadata fields" in e for e in errors)

def test_validate_graph_structure_valid():
    nodes = pd.DataFrame({"node_id": [0, 1]})
    edges = pd.DataFrame({"source": [0, 1], "target": [1, 0]})
    errors = validate_graph_structure(nodes, edges)
    assert len(errors) == 0

def test_validate_graph_structure_self_loops_disallowed():
    nodes = pd.DataFrame({"node_id": [0, 1]})
    edges = pd.DataFrame({"source": [0, 0], "target": [1, 0]}) # 0->0 is self loop
    errors = validate_graph_structure(nodes, edges)
    assert any("self-loops" in e for e in errors)

def test_validate_graph_full_valid():
    is_valid, errors = validate_graph(*valid_graph, sample_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_graph_full_invalid():
    bad_nodes = pd.DataFrame([{"atomic_number": "str"}])
    bad_edges = valid_edges
    bad_meta = valid_metadata
    is_valid, errors = validate_graph(bad_nodes, bad_edges, bad_meta, sample_schema)
    assert not is_valid
    assert len(errors) > 0

def test_validate_all_graphs_valid():
    # Mock a dataframe with nested structures
    mock_data = pd.DataFrame([{
        "graph_id": 1,
        "nodes": valid_nodes.to_dict('records'),
        "edges": valid_edges.to_dict('records'),
        "metadata": valid_metadata
    }])
    
    results = validate_all_graphs(mock_data, sample_schema)
    assert results["valid_graphs"] == 1
    assert results["invalid_graphs"] == 0
    assert len(results["errors"]) == 0

def test_validate_all_graphs_mixed():
    bad_nodes = pd.DataFrame([{"atomic_number": "str"}])
    mock_data = pd.DataFrame([
        {
            "graph_id": 1,
            "nodes": valid_nodes.to_dict('records'),
            "edges": valid_edges.to_dict('records'),
            "metadata": valid_metadata
        },
        {
            "graph_id": 2,
            "nodes": bad_nodes.to_dict('records'),
            "edges": valid_edges.to_dict('records'),
            "metadata": valid_metadata
        }
    ])
    
    results = validate_all_graphs(mock_data, sample_schema)
    assert results["valid_graphs"] == 1
    assert results["invalid_graphs"] == 1
    assert len(results["errors"]) == 1
    assert results["errors"][0]["graph_id"] == "2"