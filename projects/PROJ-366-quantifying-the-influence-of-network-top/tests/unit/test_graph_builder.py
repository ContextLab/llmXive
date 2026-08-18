"""
Unit tests for Graph Builder and Serializer (T015a).

Tests:
- T011: Unit test for bond cutoff logic.
- T016b: Unit test for node-degree stats output.
- T015a: Unit test for graph serialization.
"""
import os
import json
import pickle
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import modules
from ingest.graph_builder import build_graph_from_xyz, calculate_node_degree_stats
from ingest.graph_serializer import serialize_graph, calculate_checksum
from config import get_config, get_paths


@pytest.fixture
def temp_xyz_file():
    """Create a temporary XYZ file with a known structure for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
        # Header: 4 atoms
        f.write("4\n")
        f.write("Test structure for bond cutoff\n")
        # Atom 1 at origin
        f.write("Si 0.0 0.0 0.0\n")
        # Atom 2 at 2.35 A (bonded)
        f.write("Si 2.35 0.0 0.0\n")
        # Atom 3 at 3.5 A (not bonded, > 3.0 cutoff)
        f.write("Si 3.5 0.0 0.0\n")
        # Atom 4 at 2.35 in Y (bonded to 1)
        f.write("Si 0.0 2.35 0.0\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    import shutil
    shutil.rmtree(temp_dir)


def test_bond_cutoff_logic(temp_xyz_file):
    """
    T011: Unit test for bond cutoff logic.
    
    Verifies that atoms within 3.0 Å are connected and those outside are not.
    """
    graph = build_graph_from_xyz(temp_xyz_file, cutoff=3.0)
    
    assert graph is not None
    assert len(graph['nodes']) == 4
    
    # Check edges
    edges = graph['edges']
    
    # Expected edges: (0,1), (0,3). (0,2) should NOT exist (3.5 > 3.0)
    # Node indices: 0, 1, 2, 3
    
    # Verify specific connections
    edge_set = set(tuple(sorted(e)) for e in edges)
    
    assert (0, 1) in edge_set, "Atoms at 0.0 and 2.35 should be bonded"
    assert (0, 3) in edge_set, "Atoms at 0.0 and 2.35 (Y) should be bonded"
    assert (0, 2) not in edge_set, "Atoms at 0.0 and 3.5 should NOT be bonded"
    
    # Verify degrees
    # Node 0: connected to 1, 3 -> degree 2
    # Node 1: connected to 0 -> degree 1
    # Node 2: connected to none -> degree 0
    # Node 3: connected to 0 -> degree 1
    
    node_degrees = {n['id']: n['degree'] for n in graph['nodes']}
    assert node_degrees[0] == 2
    assert node_degrees[1] == 1
    assert node_degrees[2] == 0
    assert node_degrees[3] == 1


def test_node_degree_stats_output(temp_xyz_file):
    """
    T016b: Unit test for node-degree stats output.
    
    Verifies that the node degree statistics function returns expected structure.
    """
    graph = build_graph_from_xyz(temp_xyz_file, cutoff=3.0)
    stats = calculate_node_degree_stats([graph])
    
    assert 'mode' in stats
    assert isinstance(stats['mode'], int)
    # In our test case: degrees are [2, 1, 0, 1]. Mode is 1.
    assert stats['mode'] == 1
    
    assert 'distribution' in stats
    assert 0 in stats['distribution']
    assert 1 in stats['distribution']
    assert 2 in stats['distribution']


def test_serialization(temp_xyz_file, temp_output_dir):
    """
    T015a: Unit test for graph serialization.
    
    Verifies that a graph can be serialized to a pickle file and loaded back
    with identical content.
    """
    # Build graph
    graph_data = build_graph_from_xyz(temp_xyz_file, cutoff=3.0)
    assert graph_data is not None
    
    # Define output path
    output_file = temp_output_dir / "graph_test.pkl"
    
    # Serialize
    serialize_graph(graph_data, output_file)
    
    # Verify file exists
    assert output_file.exists(), "Serialized file was not created"
    
    # Verify checksum calculation works
    checksum = calculate_checksum(output_file)
    assert len(checksum) == 64, "SHA256 checksum should be 64 hex chars"
    
    # Deserialize and verify content
    with open(output_file, 'rb') as f:
        loaded_graph = pickle.load(f)
    
    # Verify structure
    assert loaded_graph['nodes'] == graph_data['nodes']
    assert loaded_graph['edges'] == graph_data['edges']
    assert loaded_graph['metadata'] == graph_data['metadata']


def test_serialization_schema_compliance(temp_xyz_file, temp_output_dir):
    """
    T015a: Verify serialized data matches the AtomicGraph schema requirements.
    
    Checks that the serialized object contains required fields:
    nodes (with id, coords, degree, clustering_coeff), edges, metadata.
    """
    graph_data = build_graph_from_xyz(temp_xyz_file, cutoff=3.0)
    output_file = temp_output_dir / "graph_schema_test.pkl"
    
    serialize_graph(graph_data, output_file)
    
    with open(output_file, 'rb') as f:
        loaded_graph = pickle.load(f)
    
    # Check top-level keys
    assert 'nodes' in loaded_graph
    assert 'edges' in loaded_graph
    assert 'metadata' in loaded_graph
    
    # Check node structure
    for node in loaded_graph['nodes']:
        assert 'id' in node
        assert 'coords' in node
        assert len(node['coords']) == 3
        assert 'degree' in node
        assert isinstance(node['degree'], int)
        assert 'clustering_coeff' in node
        assert isinstance(node['clustering_coeff'], float)
    
    # Check edge structure (list of pairs)
    for edge in loaded_graph['edges']:
        assert len(edge) == 2
        assert isinstance(edge[0], int)
        assert isinstance(edge[1], int)
    
    # Check metadata
    assert 'sample_id' in loaded_graph['metadata']
    assert 'cutoff' in loaded_graph['metadata']
    assert 'atom_count' in loaded_graph['metadata']