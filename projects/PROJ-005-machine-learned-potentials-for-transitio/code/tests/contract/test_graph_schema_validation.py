"""
Contract tests for Graph Schema Validation.

These tests ensure that the validation logic in src/data/validate_graphs.py
correctly identifies valid and invalid graphs according to the schema.
"""
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from src.data.validate_graphs import (
    GraphValidationError,
    load_schema,
    validate_node_attributes,
    validate_edge_attributes,
    validate_graph_metadata,
    validate_graph_structure,
    validate_graph,
    validate_all_graphs,
    get_project_root
)


@pytest.fixture
def sample_schema(tmp_path):
    """Create a temporary schema file for testing."""
    schema = {
        "nodes": {
            "required_attributes": ["atomic_number", "formal_charge"],
            "attribute_types": {
                "atomic_number": "int",
                "formal_charge": "int",
                "element_symbol": "str"
            }
        },
        "edges": {
            "required_attributes": ["distance"],
            "attribute_types": {
                "distance": "float",
                "edge_type": "str"
            }
        },
        "metadata": {
            "required_fields": ["graph_id", "energy_dft"],
            "field_types": {
                "graph_id": "str",
                "energy_dft": "float",
                "ligand_class": "str"
            }
        },
        "graph": {
            "allow_self_loops": False,
            "require_connected": False
        }
    }

    schema_path = tmp_path / "test_schema.yaml"
    with open(schema_path, "w") as f:
        yaml.dump(schema, f)

    return schema_path, schema


@pytest.fixture
def valid_nodes():
    return pd.DataFrame({
        "atomic_number": [6, 8, 7],
        "formal_charge": [0, 0, 0],
        "element_symbol": ["C", "O", "N"]
    })


@pytest.fixture
def valid_edges():
    return pd.DataFrame({
        "source": [0, 1, 2],
        "target": [1, 2, 0],
        "distance": [1.2, 1.4, 1.3],
        "edge_type": ["single", "double", "single"]
    })


@pytest.fixture
def valid_metadata():
    return {
        "graph_id": "test_001",
        "energy_dft": -123.45,
        "ligand_class": "Group 13",
        "num_nodes": 3,
        "num_edges": 3
    }


@pytest.fixture
def valid_graph(valid_nodes, valid_edges, valid_metadata):
    return {
        "nodes": valid_nodes,
        "edges": valid_edges,
        "metadata": valid_metadata
    }


def test_load_schema_valid(sample_schema):
    path, _ = sample_schema
    schema = load_schema(path)
    assert "nodes" in schema
    assert "edges" in schema
    assert "metadata" in schema


def test_load_schema_missing_file():
    with pytest.raises(FileNotFoundError):
        load_schema(Path("/nonexistent/path/schema.yaml"))


def test_validate_node_attributes_valid(valid_nodes, sample_schema):
    _, schema = sample_schema
    errors = validate_node_attributes(valid_nodes, schema)
    assert len(errors) == 0


def test_validate_node_attributes_missing_column(valid_nodes, sample_schema):
    _, schema = sample_schema
    # Remove a required column
    bad_nodes = valid_nodes.drop(columns=["atomic_number"])
    errors = validate_node_attributes(bad_nodes, schema)
    assert len(errors) > 0
    assert "atomic_number" in str(errors[0])


def test_validate_node_attributes_wrong_type(valid_nodes, sample_schema):
    _, schema = sample_schema
    # Change type of atomic_number to float
    bad_nodes = valid_nodes.copy()
    bad_nodes["atomic_number"] = bad_nodes["atomic_number"].astype(float)
    errors = validate_node_attributes(bad_nodes, schema)
    assert len(errors) > 0
    assert "atomic_number" in str(errors[0])


def test_validate_edge_attributes_valid(valid_edges, sample_schema):
    _, schema = sample_schema
    errors = validate_edge_attributes(valid_edges, schema)
    assert len(errors) == 0


def test_validate_edge_attributes_missing_column(valid_edges, sample_schema):
    _, schema = sample_schema
    bad_edges = valid_edges.drop(columns=["distance"])
    errors = validate_edge_attributes(bad_edges, schema)
    assert len(errors) > 0
    assert "distance" in str(errors[0])


def test_validate_graph_metadata_valid(valid_metadata, sample_schema):
    _, schema = sample_schema
    errors = validate_graph_metadata(valid_metadata, schema)
    assert len(errors) == 0


def test_validate_graph_metadata_missing_field(valid_metadata, sample_schema):
    _, schema = sample_schema
    bad_meta = valid_metadata.copy()
    del bad_meta["energy_dft"]
    errors = validate_graph_metadata(bad_meta, schema)
    assert len(errors) > 0
    assert "energy_dft" in str(errors[0])


def test_validate_graph_structure_valid(valid_graph, sample_schema):
    _, schema = sample_schema
    errors = validate_graph_structure(valid_graph, schema)
    assert len(errors) == 0


def test_validate_graph_structure_self_loops_disallowed(valid_graph, sample_schema):
    _, schema = sample_schema
    # Add a self-loop
    bad_edges = valid_graph["edges"].copy()
    bad_edges = pd.concat([bad_edges, pd.DataFrame({"source": [0], "target": [0], "distance": [1.0], "edge_type": ["single"]})], ignore_index=True)
    bad_graph = valid_graph.copy()
    bad_graph["edges"] = bad_edges

    errors = validate_graph_structure(bad_graph, schema)
    assert len(errors) > 0
    assert "self-loops" in str(errors[0]).lower()


def test_validate_graph_full_valid(valid_graph, sample_schema):
    _, schema = sample_schema
    is_valid, errors = validate_graph(valid_graph, schema)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_graph_full_invalid(valid_graph, sample_schema):
    _, schema = sample_schema
    # Make nodes invalid
    bad_graph = valid_graph.copy()
    bad_graph["nodes"] = bad_graph["nodes"].drop(columns=["atomic_number"])

    is_valid, errors = validate_graph(bad_graph, schema)
    assert is_valid is False
    assert len(errors) > 0


def test_validate_all_graphs_valid(valid_graph, sample_schema):
    _, schema = sample_schema
    graphs = [valid_graph, valid_graph]
    all_valid, errors_by_idx = validate_all_graphs(graphs, schema)
    assert all_valid is True
    assert len(errors_by_idx) == 0


def test_validate_all_graphs_mixed(valid_graph, sample_schema):
    _, schema = sample_schema
    bad_graph = valid_graph.copy()
    bad_graph["nodes"] = bad_graph["nodes"].drop(columns=["atomic_number"])

    graphs = [valid_graph, bad_graph]
    all_valid, errors_by_idx = validate_all_graphs(graphs, schema)
    assert all_valid is False
    assert 1 in errors_by_idx
    assert len(errors_by_idx[1]) > 0
