import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.data.validate_graphs import (
    load_schema,
    validate_node_attributes,
    validate_edge_attributes,
    validate_graph_metadata,
    validate_graph_structure,
    validate_graph,
    validate_all_graphs,
    GraphValidationError
)

@pytest.fixture
def valid_schema():
    return {
        "nodes": {
            "required_attributes": ["atomic_number", "formal_charge"],
            "types": {"atomic_number": "int", "formal_charge": "int"}
        },
        "edges": {
            "required_attributes": ["distance", "type"],
            "types": {"distance": "float"}
        },
        "metadata": {
            "required_attributes": ["energy_dft", "barrier_height"]
        }
    }

@pytest.fixture
def valid_graphs_df():
    # Simulating a DataFrame where 'nodes' and 'edges' are columns of lists of dicts
    data = {
        "energy_dft": [1.5, 2.0],
        "barrier_height": [0.5, 0.8],
        "nodes": [
            [{"atomic_number": 6, "formal_charge": 0}, {"atomic_number": 1, "formal_charge": 0}],
            [{"atomic_number": 29, "formal_charge": 0}, {"atomic_number": 6, "formal_charge": 0}]
        ],
        "edges": [
            [{"source": 0, "target": 1, "distance": 1.5, "type": "bond"}],
            [{"source": 0, "target": 1, "distance": 1.8, "type": "bond"}]
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def invalid_node_df():
    data = {
        "energy_dft": [1.5],
        "barrier_height": [0.5],
        "nodes": [
            [{"atomic_number": 6}] # Missing formal_charge
        ],
        "edges": [
            [{"source": 0, "target": 1, "distance": 1.5, "type": "bond"}]
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def invalid_metadata_df():
    data = {
        "energy_dft": [1.5],
        # Missing barrier_height
        "nodes": [
            [{"atomic_number": 6, "formal_charge": 0}]
        ],
        "edges": [
            [{"source": 0, "target": 1, "distance": 1.5, "type": "bond"}]
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def self_loop_df():
    data = {
        "energy_dft": [1.5],
        "barrier_height": [0.5],
        "nodes": [
            [{"atomic_number": 6, "formal_charge": 0}]
        ],
        "edges": [
            [{"source": 0, "target": 0, "distance": 0.0, "type": "loop"}] # Self loop
        ]
    }
    return pd.DataFrame(data)

def test_validate_node_attributes_valid(valid_schema, valid_graphs_df):
    is_valid, errors = validate_node_attributes(valid_graphs_df, valid_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_node_attributes_missing(valid_schema, invalid_node_df):
    is_valid, errors = validate_node_attributes(invalid_node_df, valid_schema)
    assert not is_valid
    assert any("formal_charge" in e for e in errors)

def test_validate_edge_attributes_valid(valid_schema, valid_graphs_df):
    is_valid, errors = validate_edge_attributes(valid_graphs_df, valid_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_graph_metadata_valid(valid_schema, valid_graphs_df):
    is_valid, errors = validate_graph_metadata(valid_graphs_df, valid_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_graph_metadata_missing(valid_schema, invalid_metadata_df):
    is_valid, errors = validate_graph_metadata(invalid_metadata_df, valid_schema)
    assert not is_valid
    assert any("barrier_height" in e for e in errors)

def test_validate_graph_structure_valid(valid_schema, valid_graphs_df):
    is_valid, errors = validate_graph_structure(valid_graphs_df)
    assert is_valid
    assert len(errors) == 0

def test_validate_graph_structure_self_loop(valid_schema, self_loop_df):
    is_valid, errors = validate_graph_structure(self_loop_df)
    assert not is_valid
    assert any("self-loop" in e for e in errors)

def test_validate_graph_full_valid(valid_schema, valid_graphs_df):
    is_valid, errors = validate_graph(valid_graphs_df, valid_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_graph_full_invalid(valid_schema, invalid_node_df):
    is_valid, errors = validate_graph(invalid_node_df, valid_schema)
    assert not is_valid

def test_validate_all_graphs_valid(valid_schema, valid_graphs_df, tmp_path):
    # Create a temporary parquet file
    parquet_path = tmp_path / "test_graphs.parquet"
    valid_graphs_df.to_parquet(parquet_path)
    
    # Create a temporary schema file
    schema_path = tmp_path / "schema.yaml"
    with open(schema_path, 'w') as f:
        import yaml
        yaml.dump(valid_schema, f)
    
    # Run validation
    result = validate_all_graphs(parquet_path, schema_path)
    assert result is True

def test_validate_all_graphs_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_all_graphs(tmp_path / "nonexistent.parquet")

def test_validate_all_graphs_invalid(tmp_path, invalid_node_df):
    parquet_path = tmp_path / "test_graphs.parquet"
    invalid_node_df.to_parquet(parquet_path)
    
    schema_path = tmp_path / "schema.yaml"
    valid_schema = {
        "nodes": {"required_attributes": ["atomic_number", "formal_charge"]},
        "edges": {"required_attributes": []},
        "metadata": {"required_attributes": []}
    }
    with open(schema_path, 'w') as f:
        import yaml
        yaml.dump(valid_schema, f)
    
    with pytest.raises(GraphValidationError):
        validate_all_graphs(parquet_path, schema_path)