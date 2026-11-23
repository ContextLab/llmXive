"""
Tests for filter_invalid_dags.py (T017 implementation).

These tests verify that invalid traces (cycles, threshold violations) are
correctly identified and excluded from the DAG manifest.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.scripts.filter_invalid_dags import (
    load_manifest,
    is_entry_valid,
    filter_invalid_entries,
    save_manifest
)

@pytest.fixture
def sample_manifest():
    """Create a sample manifest with valid and invalid entries."""
    return {
        'metadata': {
            'total_entries': 5,
            'generation_timestamp': '2024-01-01T00:00:00Z'
        },
        'entries': [
            {
                'trace_id': 'valid_1',
                'is_valid': True,
                'dag': {
                    'nodes': [{'id': '1', 'text': 'Step 1'}],
                    'edges': []
                }
            },
            {
                'trace_id': 'invalid_cycle',
                'has_cycle': True,
                'invalid_reason': 'Cycle detected between nodes 2 and 3',
                'dag': {
                    'nodes': [
                        {'id': '1', 'text': 'Step 1'},
                        {'id': '2', 'text': 'Step 2'},
                        {'id': '3', 'text': 'Step 3'}
                    ],
                    'edges': [
                        {'from': '1', 'to': '2'},
                        {'from': '2', 'to': '3'},
                        {'from': '3', 'to': '2'}  # Cycle
                    ]
                }
            },
            {
                'trace_id': 'valid_2',
                'is_valid': True,
                'dag': {
                    'nodes': [{'id': '1', 'text': 'Step 1'}],
                    'edges': []
                }
            },
            {
                'trace_id': 'invalid_threshold',
                'invalid_reason': 'Threshold violation: >3 incoming edges',
                'dag': {
                    'nodes': [{'id': '1', 'text': 'Step 1'}],
                    'edges': []
                }
            },
            {
                'trace_id': 'valid_3',
                'is_valid': True,
                'dag': {
                    'nodes': [
                        {'id': '1', 'text': 'Step 1'},
                        {'id': '2', 'text': 'Step 2'}
                    ],
                    'edges': [{'from': '1', 'to': '2'}]
                }
            }
        ]
    }

@pytest.fixture
def temp_manifest_file(sample_manifest):
    """Create a temporary file with the sample manifest."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_manifest, f)
        temp_path = Path(f.name)
    yield temp_path
    # Cleanup
    temp_path.unlink(missing_ok=True)

def test_load_manifest_success(temp_manifest_file, sample_manifest):
    """Test successful loading of a manifest."""
    manifest = load_manifest(temp_manifest_file)
    assert manifest == sample_manifest
    assert 'entries' in manifest
    assert len(manifest['entries']) == 5

def test_load_manifest_not_found():
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_manifest(Path('/nonexistent/path/manifest.json'))

def test_filter_invalid_entries(sample_manifest):
    """Test that invalid entries are correctly filtered out."""
    filtered_manifest, valid_count, invalid_count = filter_invalid_entries(sample_manifest)
    
    # Should have 3 valid entries (valid_1, valid_2, valid_3)
    assert valid_count == 3
    assert invalid_count == 2
    
    # Check that valid entries are preserved
    trace_ids = [entry['trace_id'] for entry in filtered_manifest['entries']]
    assert 'valid_1' in trace_ids
    assert 'valid_2' in trace_ids
    assert 'valid_3' in trace_ids
    
    # Check that invalid entries are excluded
    assert 'invalid_cycle' not in trace_ids
    assert 'invalid_threshold' not in trace_ids
    
    # Check metadata updates
    assert filtered_manifest['metadata']['valid_entries'] == 3
    assert filtered_manifest['metadata']['invalid_entries'] == 2
    assert filtered_manifest['metadata']['total_entries'] == 5

def test_filter_all_valid():
    """Test filtering when all entries are valid."""
    manifest = {
        'metadata': {'total_entries': 2},
        'entries': [
            {'trace_id': 'v1', 'is_valid': True, 'dag': {'nodes': [], 'edges': []}},
            {'trace_id': 'v2', 'is_valid': True, 'dag': {'nodes': [], 'edges': []}}
        ]
    }
    
    filtered, valid_count, invalid_count = filter_invalid_entries(manifest)
    assert valid_count == 2
    assert invalid_count == 0
    assert len(filtered['entries']) == 2

def test_filter_all_invalid():
    """Test filtering when all entries are invalid."""
    manifest = {
        'metadata': {'total_entries': 2},
        'entries': [
            {'trace_id': 'i1', 'has_cycle': True},
            {'trace_id': 'i2', 'invalid_reason': 'Threshold violation'}
        ]
    }
    
    filtered, valid_count, invalid_count = filter_invalid_entries(manifest)
    assert valid_count == 0
    assert invalid_count == 2
    assert len(filtered['entries']) == 0

def test_save_manifest(sample_manifest):
    """Test saving a manifest to a file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        save_manifest(sample_manifest, temp_path)
        
        # Verify file was created
        assert temp_path.exists()
        
        # Verify content
        with open(temp_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == sample_manifest
    finally:
        temp_path.unlink(missing_ok=True)

def test_is_entry_valid_cycle_detection():
    """Test that entries with cycles are marked invalid."""
    entry = {
        'trace_id': 'test',
        'has_cycle': True,
        'invalid_reason': 'Cycle detected'
    }
    is_valid, reason = is_entry_valid(entry)
    assert not is_valid
    assert 'cycle' in reason.lower()

def test_is_entry_valid_threshold_violation():
    """Test that entries with threshold violations are marked invalid."""
    entry = {
        'trace_id': 'test',
        'invalid_reason': 'Threshold violation: >3 incoming edges'
    }
    is_valid, reason = is_entry_valid(entry)
    assert not is_valid
    assert 'threshold' in reason.lower()

def test_is_entry_valid_explicit_flag():
    """Test that explicitly marked invalid entries are rejected."""
    entry = {
        'trace_id': 'test',
        'is_valid': False,
        'invalid_reason': 'Custom reason'
    }
    is_valid, reason = is_entry_valid(entry)
    assert not is_valid

def test_is_entry_valid_valid_entry():
    """Test that valid entries are accepted."""
    entry = {
        'trace_id': 'test',
        'is_valid': True,
        'dag': {
            'nodes': [{'id': '1', 'text': 'Step 1'}],
            'edges': []
        }
    }
    is_valid, reason = is_entry_valid(entry)
    assert is_valid
    assert reason == "Valid"

def test_is_entry_valid_missing_structure():
    """Test that entries missing DAG structure are rejected."""
    entry = {
        'trace_id': 'test',
        'is_valid': True,
        'dag': {}  # Missing nodes/edges
    }
    is_valid, reason = is_entry_valid(entry)
    assert not is_valid
    assert 'structure' in reason.lower()

def test_is_entry_valid_empty_nodes():
    """Test that entries with empty nodes in non-empty trace are rejected."""
    entry = {
        'trace_id': 'test',
        'is_valid': True,
        'dag': {
            'nodes': [],
            'edges': [],
            'trace_length': 5
        }
    }
    is_valid, reason = is_entry_valid(entry)
    assert not is_valid
    assert 'no nodes' in reason.lower()