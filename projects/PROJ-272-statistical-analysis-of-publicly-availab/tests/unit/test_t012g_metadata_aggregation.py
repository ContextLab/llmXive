"""
Unit tests for T012g: Metadata Aggregation.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from t012g_metadata_aggregation import merge_metadata_files, load_json_file

def test_merge_metadata_files():
    """Test that merge_metadata_files correctly combines two JSON files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create input files
        partial_e_data = {
            "low_power": True,
            "group_counts": {
                "Control": 10,
                "MCI": 15,
                "AD": 8
            }
        }
        partial_h_data = {
            "valid_label_proportion": 0.85
        }
        
        partial_e_path = tmpdir_path / "metadata_partial_e.json"
        partial_h_path = tmpdir_path / "metadata_partial_h.json"
        output_path = tmpdir_path / "metadata.json"
        
        with open(partial_e_path, 'w') as f:
            json.dump(partial_e_data, f)
        with open(partial_h_path, 'w') as f:
            json.dump(partial_h_data, f)
        
        # Run the merge
        result = merge_metadata_files(partial_e_path, partial_h_path, output_path)
        
        # Verify result in memory
        assert result["low_power"] is True
        assert result["group_counts"]["Control"] == 10
        assert result["valid_label_proportion"] == 0.85
        
        # Verify file on disk
        assert output_path.exists()
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == result

def test_merge_metadata_files_missing_input():
    """Test that merge_metadata_files raises error if input is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        partial_e_path = tmpdir_path / "missing_e.json"
        partial_h_path = tmpdir_path / "missing_h.json"
        output_path = tmpdir_path / "metadata.json"
        
        with pytest.raises(FileNotFoundError):
            merge_metadata_files(partial_e_path, partial_h_path, output_path)

def test_load_json_file_invalid_json():
    """Test that load_json_file raises error for invalid JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        invalid_file = tmpdir_path / "invalid.json"
        
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            load_json_file(invalid_file)