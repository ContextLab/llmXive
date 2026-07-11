"""
Tests for the filter_invalid_dags.py script functionality.

These tests verify that invalid traces (cycles, invalid flags) are 
correctly removed from the DAG manifest.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.filter_invalid_dags import (
    load_manifest,
    filter_invalid_entries,
    save_manifest,
    main
)
from src.parser_utils import load_json_file, save_json_file

@pytest.fixture
def sample_manifest():
    """Create a sample manifest with valid and invalid entries."""
    return {
        "metadata": {
            "version": "1.0",
            "generated_by": "test"
        },
        "entries": [
            {
                "trace_id": "valid_1",
                "is_valid": True,
                "cycle_detected": False,
                "depth": 5,
                "content": "valid trace 1"
            },
            {
                "trace_id": "invalid_cycle",
                "is_valid": True,  # Explicitly valid but has cycle
                "cycle_detected": True,
                "depth": 3,
                "content": "trace with cycle"
            },
            {
                "trace_id": "invalid_flag",
                "is_valid": False,
                "cycle_detected": False,
                "depth": 4,
                "content": "invalid trace"
            },
            {
                "trace_id": "valid_2",
                "is_valid": True,
                "cycle_detected": False,
                "depth": 6,
                "content": "valid trace 2"
            },
            {
                "trace_id": "double_invalid",
                "is_valid": False,
                "cycle_detected": True,
                "depth": 2,
                "content": "double invalid"
            }
        ]
    }

@pytest.fixture
def temp_manifest_file(sample_manifest):
    """Create a temporary manifest file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_manifest, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()

def test_load_manifest_success(temp_manifest_file, sample_manifest):
    """Test successful loading of manifest."""
    manifest = load_manifest(temp_manifest_file)
    assert manifest == sample_manifest
    assert len(manifest["entries"]) == 5

def test_load_manifest_not_found():
    """Test loading non-existent file raises error."""
    non_existent = Path("/tmp/non_existent_manifest.json")
    with pytest.raises(FileNotFoundError):
        load_manifest(non_existent)

def test_filter_invalid_entries(sample_manifest):
    """Test that invalid entries are correctly filtered."""
    filtered_manifest, removed_ids = filter_invalid_entries(sample_manifest)
    
    # Should remove 3 invalid entries: invalid_cycle, invalid_flag, double_invalid
    assert len(removed_ids) == 3
    assert set(removed_ids) == {"invalid_cycle", "invalid_flag", "double_invalid"}
    
    # Remaining entries should be valid
    assert len(filtered_manifest["entries"]) == 2
    remaining_ids = {e["trace_id"] for e in filtered_manifest["entries"]}
    assert remaining_ids == {"valid_1", "valid_2"}
    
    # Metadata should be updated
    assert filtered_manifest["metadata"]["filtered_count"] == 3
    assert filtered_manifest["metadata"]["valid_count"] == 2
    assert set(filtered_manifest["metadata"]["removed_trace_ids"]) == set(removed_ids)

def test_filter_all_valid():
    """Test filtering when all entries are valid."""
    manifest = {
        "metadata": {"version": "1.0"},
        "entries": [
            {"trace_id": "v1", "is_valid": True, "cycle_detected": False},
            {"trace_id": "v2", "is_valid": True, "cycle_detected": False}
        ]
    }
    
    filtered, removed = filter_invalid_entries(manifest)
    
    assert len(removed) == 0
    assert len(filtered["entries"]) == 2

def test_filter_all_invalid():
    """Test filtering when all entries are invalid."""
    manifest = {
        "metadata": {"version": "1.0"},
        "entries": [
            {"trace_id": "i1", "is_valid": False, "cycle_detected": False},
            {"trace_id": "i2", "is_valid": True, "cycle_detected": True}
        ]
    }
    
    filtered, removed = filter_invalid_entries(manifest)
    
    assert len(removed) == 2
    assert len(filtered["entries"]) == 0
    assert filtered["metadata"]["valid_count"] == 0

def test_save_manifest(temp_manifest_file, sample_manifest):
    """Test saving manifest to file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = Path(f.name)
    
    try:
        save_manifest(sample_manifest, output_path)
        assert output_path.exists()
        
        # Verify content
        loaded = load_json_file(output_path)
        assert loaded == sample_manifest
    finally:
        if output_path.exists():
            output_path.unlink()

@patch('scripts.filter_invalid_dags.get_config')
@patch('scripts.filter_invalid_dags.load_manifest')
@patch('scripts.filter_invalid_dags.filter_invalid_entries')
@patch('scripts.filter_invalid_dags.save_manifest')
def test_main_success(mock_save, mock_filter, mock_load, mock_config, 
                     sample_manifest, temp_manifest_file):
    """Test main function successful execution."""
    # Setup mocks
    mock_config.return_value.get_processed_dir.return_value = temp_manifest_file.parent
    mock_load.return_value = sample_manifest
    mock_filter.return_value = (sample_manifest, [])
    
    result = main()
    
    assert result == 0
    mock_load.assert_called_once()
    mock_filter.assert_called_once()
    mock_save.assert_called_once()

@patch('scripts.filter_invalid_dags.get_config')
def test_main_file_not_found(mock_config, temp_manifest_file):
    """Test main function when manifest not found."""
    mock_config.return_value.get_processed_dir.return_value = Path("/nonexistent")
    
    result = main()
    
    assert result == 1