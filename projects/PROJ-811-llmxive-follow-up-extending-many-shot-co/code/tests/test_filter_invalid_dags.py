"""
Unit tests for the filter_invalid_dags script.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys
import os

# Add code to path if running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.filter_invalid_dags import load_manifest, filter_invalid_entries, save_manifest, main

@pytest.fixture
def sample_manifest():
    """Create a sample manifest with mixed validity."""
    return {
        "metadata": {
            "source": "test",
            "total_entries": 5,
            "valid_entries": 5,
            "invalid_entries": 0
        },
        "entries": [
            {"example_id": "ex_001", "logical_difficulty_score": 2.0, "is_valid": True, "max_path_depth": 2},
            {"example_id": "ex_002", "logical_difficulty_score": 3.5, "is_valid": True, "max_path_depth": 4},
            {"example_id": "ex_003", "logical_difficulty_score": 1.0, "is_valid": False, "max_path_depth": 1},  # Invalid
            {"example_id": "ex_004", "logical_difficulty_score": 4.0, "is_valid": True, "max_path_depth": 5},
            {"example_id": "ex_005", "logical_difficulty_score": 2.5, "is_valid": False, "max_path_depth": 3},  # Invalid
        ]
    }

@pytest.fixture
def temp_manifest_file(sample_manifest):
    """Create a temporary JSON file with sample manifest."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_manifest, f)
        path = Path(f.name)
    yield path
    path.unlink()

def test_load_manifest_success(temp_manifest_file, sample_manifest):
    """Test loading a valid manifest file."""
    data = load_manifest(temp_manifest_file)
    assert "entries" in data
    assert len(data["entries"]) == 5
    assert data["metadata"]["source"] == "test"

def test_load_manifest_not_found():
    """Test loading a non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_manifest(Path("/nonexistent/path.json"))

def test_filter_invalid_entries(sample_manifest):
    """Test that invalid entries are removed and counts updated."""
    filtered, removed, kept = filter_invalid_entries(sample_manifest)
    
    assert removed == 2
    assert kept == 3
    assert len(filtered["entries"]) == 3
    
    # Verify only valid entries remain
    for entry in filtered["entries"]:
        assert entry["is_valid"] is True
    
    # Verify metadata update
    assert filtered["metadata"]["total_entries"] == 5
    assert filtered["metadata"]["valid_entries"] == 3
    assert filtered["metadata"]["invalid_entries"] == 2

def test_filter_all_valid():
    """Test filtering when all entries are valid."""
    manifest = {
        "metadata": {"source": "test", "total_entries": 2, "valid_entries": 2, "invalid_entries": 0},
        "entries": [
            {"example_id": "ex_001", "is_valid": True},
            {"example_id": "ex_002", "is_valid": True}
        ]
    }
    filtered, removed, kept = filter_invalid_entries(manifest)
    
    assert removed == 0
    assert kept == 2
    assert len(filtered["entries"]) == 2

def test_filter_all_invalid():
    """Test filtering when all entries are invalid."""
    manifest = {
        "metadata": {"source": "test", "total_entries": 2, "valid_entries": 2, "invalid_entries": 0},
        "entries": [
            {"example_id": "ex_001", "is_valid": False},
            {"example_id": "ex_002", "is_valid": False}
        ]
    }
    filtered, removed, kept = filter_invalid_entries(manifest)
    
    assert removed == 2
    assert kept == 0
    assert len(filtered["entries"]) == 0

def test_save_manifest(temp_manifest_file, sample_manifest):
    """Test saving the manifest."""
    # Modify data slightly to ensure it's different
    sample_manifest["metadata"]["source"] = "modified"
    
    save_manifest(sample_manifest, temp_manifest_file)
    
    # Reload and verify
    with open(temp_manifest_file, 'r') as f:
        data = json.load(f)
    
    assert data["metadata"]["source"] == "modified"
    assert len(data["entries"]) == 5

@patch('scripts.filter_invalid_dags.load_manifest')
@patch('scripts.filter_invalid_dags.filter_invalid_entries')
@patch('scripts.filter_invalid_dags.save_manifest')
def test_main_success(mock_save, mock_filter, mock_load, temp_manifest_file, sample_manifest):
    """Test the main function execution path."""
    mock_load.return_value = sample_manifest
    mock_filter.return_value = (sample_manifest, 2, 3)
    
    # Patch the global paths used in main
    with patch('scripts.filter_invalid_dags.MANIFEST_PATH', temp_manifest_file), \
         patch('scripts.filter_invalid_dags.OUTPUT_PATH', temp_manifest_file):
        
        result = main()
        
        assert result == 0
        mock_load.assert_called_once_with(temp_manifest_file)
        mock_filter.assert_called_once()
        mock_save.assert_called_once()

@patch('scripts.filter_invalid_dags.load_manifest')
def test_main_file_not_found(mock_load):
    """Test main returns error code when file not found."""
    mock_load.side_effect = FileNotFoundError("Not found")
    
    with patch('scripts.filter_invalid_dags.MANIFEST_PATH', Path("/fake/path.json")):
        result = main()
        assert result == 1
        mock_load.assert_called_once()