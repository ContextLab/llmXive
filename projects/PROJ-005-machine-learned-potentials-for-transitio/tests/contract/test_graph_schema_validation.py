"""
Contract Tests for Graph Schema Validation.

These tests verify that the validation logic in `src/data/validate_graphs.py`
correctly enforces the schema defined in `contracts/dataset_graph.schema.yaml`.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import pytest
import yaml

import sys
import os

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent.parent / 'code'
sys.path.insert(0, str(code_dir))

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
    """Load the actual schema used in the project."""
    schema_path = code_dir / 'contracts' / 'dataset_graph.schema.yaml'
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_nodes():
    """Generate a list of valid node dictionaries."""
    return [
        {
            'atomic_number': 46,
            'x': 0.0,
            'y': 0.0,
            'z': 0.0,
            'is_metal': True,
            'ligand_class': 'Group_13',
            'formal_charge': 0
        },
        {
            'atomic_number': 6,
            'x': 1.5,
            'y': 0.0,
            'z': 0.0,
            'is_metal': False,
            'ligand_class': 'Group_13',
            'formal_charge': 0
        }
    ]

@pytest.fixture
def valid_edges():
    """Generate a list of valid edge dictionaries."""
    return [
        {
            'source': 0,
            'target': 1,
            'distance': 1.5,
            'edge_type': 'covalent'
        }
    ]

@pytest.fixture
def valid_metadata():
    """Generate valid graph metadata."""
    return {
        'energy_dft': -1234.56,
        'barrier_height': 15.2,
        'metal_center': 46,
        'ligand_class': 'Group_13',
        'reaction_id': 'test_reaction_001',
        'geometry_source': 'QM9-TS',
        'is_outlier': False,
        'cutoff_used': 3.5
    }

def test_load_schema_valid(sample_schema):
    """Test that the schema loads correctly."""
    assert 'properties' in sample_schema
    assert 'node_attributes' in sample_schema['properties']
    assert 'edge_attributes' in sample_schema['properties']
    assert 'graph_metadata' in sample_schema['properties']

def test_load_schema_missing_file():
    """Test that loading a missing schema raises an error."""
    with pytest.raises(FileNotFoundError):
        load_schema(Path('/nonexistent/path/schema.yaml'))

def test_validate_node_attributes_valid(valid_nodes, sample_schema):
    """Test validation of valid node attributes."""
    is_valid, errors = validate_node_attributes(valid_nodes, sample_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_node_attributes_missing_column(valid_nodes, sample_schema):
    """Test validation fails when required column is missing."""
    invalid_nodes = [dict(valid_nodes[0])]
    del invalid_nodes[0]['atomic_number']

    is_valid, errors = validate_node_attributes(invalid_nodes, sample_schema)
    assert not is_valid
    assert any('missing required field' in e for e in errors)

def test_validate_node_attributes_wrong_type(valid_nodes, sample_schema):
    """Test validation fails when column has wrong type."""
    invalid_nodes = [dict(valid_nodes[0])]
    invalid_nodes[0]['atomic_number'] = "not_an_integer"

    is_valid, errors = validate_node_attributes(invalid_nodes, sample_schema)
    assert not is_valid
    assert any('must be an integer' in e for e in errors)

def test_validate_node_attributes_invalid_ligand_class(valid_nodes, sample_schema):
    """Test validation fails when ligand_class is invalid."""
    invalid_nodes = [dict(valid_nodes[0])]
    invalid_nodes[0]['ligand_class'] = 'InvalidClass'

    is_valid, errors = validate_node_attributes(invalid_nodes, sample_schema)
    assert not is_valid
    assert any('must be one of' in e for e in errors)

def test_validate_edge_attributes_valid(valid_edges, sample_schema):
    """Test validation of valid edge attributes."""
    is_valid, errors = validate_edge_attributes(valid_edges, sample_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_edge_attributes_missing_column(valid_edges, sample_schema):
    """Test validation fails when required column is missing."""
    invalid_edges = [dict(valid_edges[0])]
    del invalid_edges[0]['source']

    is_valid, errors = validate_edge_attributes(invalid_edges, sample_schema)
    assert not is_valid
    assert any('missing required field' in e for e in errors)

def test_validate_edge_attributes_wrong_type(valid_edges, sample_schema):
    """Test validation fails when column has wrong type."""
    invalid_edges = [dict(valid_edges[0])]
    invalid_edges[0]['distance'] = "not_a_number"

    is_valid, errors = validate_edge_attributes(invalid_edges, sample_schema)
    assert not is_valid
    assert any('must be a number' in e for e in errors)

def test_validate_edge_attributes_invalid_edge_type(valid_edges, sample_schema):
    """Test validation fails when edge_type is invalid."""
    invalid_edges = [dict(valid_edges[0])]
    invalid_edges[0]['edge_type'] = 'invalid_type'

    is_valid, errors = validate_edge_attributes(invalid_edges, sample_schema)
    assert not is_valid
    assert any('must be one of' in e for e in errors)

def test_validate_graph_metadata_valid(valid_metadata, sample_schema):
    """Test validation of valid graph metadata."""
    is_valid, errors = validate_graph_metadata(valid_metadata, sample_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_graph_metadata_missing_required(valid_metadata, sample_schema):
    """Test validation fails when required metadata field is missing."""
    invalid_metadata = dict(valid_metadata)
    del invalid_metadata['energy_dft']

    is_valid, errors = validate_graph_metadata(invalid_metadata, sample_schema)
    assert not is_valid
    assert any('missing required field' in e for e in errors)

def test_validate_graph_metadata_wrong_type(valid_metadata, sample_schema):
    """Test validation fails when metadata field has wrong type."""
    invalid_metadata = dict(valid_metadata)
    invalid_metadata['metal_center'] = "not_an_integer"

    is_valid, errors = validate_graph_metadata(invalid_metadata, sample_schema)
    assert not is_valid
    assert any('must be an integer' in e for e in errors)

def test_validate_graph_metadata_invalid_ligand_class(valid_metadata, sample_schema):
    """Test validation fails when metadata ligand_class is invalid."""
    invalid_metadata = dict(valid_metadata)
    invalid_metadata['ligand_class'] = 'InvalidClass'

    is_valid, errors = validate_graph_metadata(invalid_metadata, sample_schema)
    assert not is_valid
    assert any('must be one of' in e for e in errors)

def test_validate_graph_structure_valid(valid_nodes, valid_edges):
    """Test validation of valid graph structure."""
    is_valid, errors = validate_graph_structure(valid_nodes, valid_edges)
    assert is_valid
    assert len(errors) == 0

def test_validate_graph_structure_invalid_reference(valid_nodes, valid_edges):
    """Test validation fails when edge references non-existent node."""
    invalid_edges = [dict(valid_edges[0])]
    invalid_edges[0]['source'] = 999

    is_valid, errors = validate_graph_structure(valid_nodes, invalid_edges)
    assert not is_valid
    assert any('non-existent node' in e for e in errors)

def test_validate_graph_empty_nodes(valid_edges, sample_schema):
    """Test validation fails when graph has no nodes."""
    graph_data = {
        'node_attributes': [],
        'edge_attributes': valid_edges,
        'graph_metadata': {'energy_dft': 1.0, 'barrier_height': 1.0, 'metal_center': 46, 'reaction_id': 'test'}
    }
    is_valid, errors = validate_graph(graph_data, sample_schema)
    assert not is_valid
    assert any('no nodes' in e for e in errors)

def test_validate_graph_complete_valid(valid_nodes, valid_edges, valid_metadata, sample_schema):
    """Test validation of a complete valid graph."""
    graph_data = {
        'node_attributes': valid_nodes,
        'edge_attributes': valid_edges,
        'graph_metadata': valid_metadata
    }
    is_valid, errors = validate_graph(graph_data, sample_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_graph_complete_invalid(valid_nodes, valid_edges, valid_metadata, sample_schema):
    """Test validation of a complete invalid graph."""
    graph_data = {
        'node_attributes': valid_nodes,
        'edge_attributes': valid_edges,
        'graph_metadata': dict(valid_metadata)
    }
    # Introduce an error in metadata
    graph_data['graph_metadata']['metal_center'] = "invalid"

    is_valid, errors = validate_graph(graph_data, sample_schema)
    assert not is_valid
    assert len(errors) > 0

def test_validate_graph_no_edges(valid_nodes, valid_metadata, sample_schema):
    """Test validation of a graph with no edges (valid if minItems is 0)."""
    graph_data = {
        'node_attributes': valid_nodes,
        'edge_attributes': [],
        'graph_metadata': valid_metadata
    }
    is_valid, errors = validate_graph(graph_data, sample_schema)
    # Edges minItems is 0, so this should be valid
    assert is_valid

def test_validate_graph_type_consistency(valid_nodes, valid_edges, valid_metadata, sample_schema):
    """Test that numpy types are handled correctly."""
    # Convert to numpy types
    nodes_np = []
    for n in valid_nodes:
        node_np = {
            'atomic_number': np.int64(n['atomic_number']),
            'x': np.float64(n['x']),
            'y': np.float64(n['y']),
            'z': np.float64(n['z']),
            'is_metal': bool(n['is_metal']),
            'ligand_class': n['ligand_class'],
            'formal_charge': np.int64(n['formal_charge'])
        }
        nodes_np.append(node_np)

    edges_np = []
    for e in valid_edges:
        edge_np = {
            'source': np.int64(e['source']),
            'target': np.int64(e['target']),
            'distance': np.float64(e['distance']),
            'edge_type': e['edge_type']
        }
        edges_np.append(edge_np)

    meta_np = {
        'energy_dft': np.float64(valid_metadata['energy_dft']),
        'barrier_height': np.float64(valid_metadata['barrier_height']),
        'metal_center': np.int64(valid_metadata['metal_center']),
        'ligand_class': valid_metadata['ligand_class'],
        'reaction_id': valid_metadata['reaction_id'],
        'geometry_source': valid_metadata['geometry_source'],
        'is_outlier': bool(valid_metadata['is_outlier']),
        'cutoff_used': np.float64(valid_metadata['cutoff_used'])
    }

    graph_data = {
        'node_attributes': nodes_np,
        'edge_attributes': edges_np,
        'graph_metadata': meta_np
    }

    is_valid, errors = validate_graph(graph_data, sample_schema)
    assert is_valid
    assert len(errors) == 0