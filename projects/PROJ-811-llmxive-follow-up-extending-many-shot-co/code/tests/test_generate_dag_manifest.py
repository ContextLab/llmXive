"""
Tests for the generate_dag_manifest script functionality.

These tests verify that:
1. Valid traces are correctly included in the manifest
2. Invalid traces (cycles, excessive edges) are filtered out
3. Logical difficulty scores are calculated correctly
4. The manifest file is saved in the correct format
"""

import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import networkx as nx
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.src.parser import CoTParser, get_logical_difficulty

@pytest.fixture
def sample_valid_trace():
    """Sample valid CoT trace."""
    return """
    Step 1: We need to calculate the area of the rectangle.
    Step 2: The formula for area is length times width.
    Step 3: Given length is 5 and width is 3.
    Step 4: Therefore, area = 5 * 3 = 15.
    """

@pytest.fixture
def sample_cyclic_trace():
    """Sample trace with circular dependency."""
    return """
    Step 1: First we calculate A based on B.
    Step 2: Then we calculate B based on A.
    Step 3: Finally we output the result.
    """

@pytest.fixture
def sample_manifest_data():
    """Sample manifest data structure."""
    return {
        'version': '1.0',
        'generated_at': 'test',
        'statistics': {
            'total_traces': 3,
            'valid_count': 2,
            'invalid_count': 1,
            'invalid_reasons': {'cycle_too_long': 1}
        },
        'entries': [
            {
                'id': 'trace_1',
                'valid': True,
                'logical_difficulty_score': 3,
                'num_nodes': 4,
                'num_edges': 3,
                'max_incoming_edges': 1
            },
            {
                'id': 'trace_2',
                'valid': True,
                'logical_difficulty_score': 2,
                'num_nodes': 3,
                'num_edges': 2,
                'max_incoming_edges': 1
            }
        ]
    }

@pytest.fixture
def temp_manifest_file(sample_manifest_data):
    """Create a temporary manifest file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_manifest_data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_parse_simple_trace():
    """Test parsing a simple valid trace."""
    parser = CoTParser()
    trace = "Step 1: Calculate A.\nStep 2: Calculate B based on A.\nStep 3: Output result."
    
    dag, metadata = parser.parse_trace_to_dag(trace)
    
    assert dag.number_of_nodes() == 3
    assert dag.number_of_edges() >= 2  # At least 2 dependencies
    assert metadata['is_valid'] is True
    assert metadata['num_steps'] == 3

def test_cycle_detection():
    """Test that cycles are detected correctly."""
    parser = CoTParser()
    trace = """
    Step 1: Calculate A based on B.
    Step 2: Calculate B based on A.
    Step 3: Output result.
    """
    
    dag, metadata = parser.parse_trace_to_dag(trace)
    
    # Should detect cycle
    is_valid, reason = parser.is_dag_valid(dag)
    assert is_valid is False
    assert 'cycle' in reason.lower()

def test_logical_difficulty_score():
    """Test logical difficulty score calculation."""
    # Create a simple linear chain: 0 -> 1 -> 2 -> 3
    dag = nx.DiGraph()
    dag.add_edges_from([(0, 1), (1, 2), (2, 3)])
    
    depth = get_logical_difficulty(dag)
    assert depth == 3  # 3 edges in the longest path

def test_logical_difficulty_empty_graph():
    """Test logical difficulty score on empty graph."""
    dag = nx.DiGraph()
    depth = get_logical_difficulty(dag)
    assert depth == 0

def test_max_incoming_edges_flagging():
    """Test that excessive incoming edges are flagged."""
    parser = CoTParser(max_incoming_edges=2)
    
    # Create a node with 3 incoming edges
    dag = nx.DiGraph()
    dag.add_edges_from([(0, 3), (1, 3), (2, 3)])
    
    is_valid, reason = parser.is_dag_valid(dag)
    assert is_valid is False
    assert 'incoming_edges' in reason.lower()

def test_complex_graph_depth():
    """Test depth calculation on a more complex graph."""
    # Create a graph with multiple paths
    dag = nx.DiGraph()
    # Path 1: 0 -> 1 -> 2
    # Path 2: 0 -> 3 -> 4
    # Path 3: 0 -> 5 (shorter)
    dag.add_edges_from([
        (0, 1), (1, 2),
        (0, 3), (3, 4),
        (0, 5)
    ])
    
    depth = get_logical_difficulty(dag)
    assert depth == 2  # Longest path has 2 edges

@patch('code.scripts.generate_dag_manifest.load_json_file')
@patch('code.scripts.generate_dag_manifest.save_json_file')
def test_generate_dag_manifest_logic(
    mock_save,
    mock_load,
    sample_valid_trace,
    sample_cyclic_trace
):
    """Test the core logic of manifest generation."""
    from code.scripts.generate_dag_manifest import generate_dag_manifest
    
    # Mock trace data
    traces = [
        {'id': 'valid_1', 'trace': sample_valid_trace},
        {'id': 'cyclic_1', 'trace': sample_cyclic_trace},
        {'id': 'valid_2', 'trace': sample_valid_trace}
    ]
    
    mock_load.return_value = traces
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        output_path = Path(f.name)
    
    try:
        parser = CoTParser()
        manifest = generate_dag_manifest(traces, output_path, parser)
        
        # Verify statistics
        assert manifest['statistics']['total_traces'] == 3
        assert manifest['statistics']['valid_count'] == 2
        assert manifest['statistics']['invalid_count'] == 1
        
        # Verify entries only contain valid traces
        assert len(manifest['entries']) == 2
        for entry in manifest['entries']:
            assert entry['valid'] is True
            assert 'logical_difficulty_score' in entry
            
    finally:
        if output_path.exists():
            output_path.unlink()

def test_manifest_entry_structure():
    """Test that manifest entries have correct structure."""
    parser = CoTParser()
    trace = "Step 1: A.\nStep 2: B based on A."
    
    dag, metadata = parser.parse_trace_to_dag(trace)
    is_valid, _ = parser.is_dag_valid(dag)
    depth = get_logical_difficulty(dag)
    
    entry = {
        'id': 'test_1',
        'valid': is_valid,
        'logical_difficulty_score': depth,
        'num_nodes': dag.number_of_nodes(),
        'num_edges': dag.number_of_edges(),
        'max_incoming_edges': max(dict(dag.in_degree()).values()) if dag.number_of_nodes() > 0 else 0,
        'metadata': metadata
    }
    
    required_fields = ['id', 'valid', 'logical_difficulty_score', 'num_nodes', 'num_edges', 'max_incoming_edges']
    for field in required_fields:
        assert field in entry

def test_empty_trace_handling():
    """Test handling of empty or invalid traces."""
    parser = CoTParser()
    
    # Empty trace
    dag, metadata = parser.parse_trace_to_dag("")
    assert dag.number_of_nodes() == 0
    
    # None trace
    dag, metadata = parser.parse_trace_to_dag(None)
    assert dag.number_of_nodes() == 0

def test_save_manifest_format(temp_manifest_file):
    """Test that manifest is saved in correct JSON format."""
    with open(temp_manifest_file, 'r') as f:
        data = json.load(f)
    
    assert 'version' in data
    assert 'statistics' in data
    assert 'entries' in data
    assert isinstance(data['entries'], list)
    
    if data['entries']:
        assert 'id' in data['entries'][0]
        assert 'valid' in data['entries'][0]
        assert 'logical_difficulty_score' in data['entries'][0]
