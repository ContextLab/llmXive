"""
Unit tests for Run Metadata initialization (Task T010b).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.run_metadata import (
    ensure_metadata_dir,
    generate_run_metadata,
    save_metadata,
    load_metadata
)

def test_generate_run_metadata_structure():
    """Test that generated metadata has required keys."""
    metadata = generate_run_metadata()
    assert "RUN_ID" in metadata, "RUN_ID key missing"
    assert "start_time" in metadata, "start_time key missing"
    assert "project_version" in metadata, "project_version key missing"
    
def test_run_id_is_uuid():
    """Test that RUN_ID is a valid UUID string."""
    metadata = generate_run_metadata()
    run_id = metadata["RUN_ID"]
    # Basic UUID format check (8-4-4-4-12 hex)
    parts = run_id.split('-')
    assert len(parts) == 5, "UUID should have 5 parts"
    assert len(parts[0]) == 8
    assert len(parts[1]) == 4
    assert len(parts[2]) == 4
    assert len(parts[3]) == 4
    assert len(parts[4]) == 12

def test_start_time_is_iso_format():
    """Test that start_time is in ISO 8601 format."""
    metadata = generate_run_metadata()
    start_time = metadata["start_time"]
    # Attempt to parse ISO format
    try:
        datetime.fromisoformat(start_time)
    except ValueError:
        assert False, f"start_time '{start_time}' is not a valid ISO 8601 format"

def test_save_and_load_metadata(tmp_path):
    """Test saving and loading metadata to/from a file."""
    metadata = generate_run_metadata()
    output_file = tmp_path / "test_metadata.json"
    
    save_metadata(metadata, output_file)
    assert output_file.exists(), "Output file was not created"
    
    loaded_metadata = load_metadata(output_file)
    assert loaded_metadata == metadata, "Loaded metadata does not match saved metadata"

def test_json_validity(tmp_path):
    """Test that the saved file is valid JSON."""
    metadata = generate_run_metadata()
    output_file = tmp_path / "test_metadata.json"
    
    save_metadata(metadata, output_file)
    
    with open(output_file, 'r') as f:
        try:
            json.load(f)
        except json.JSONDecodeError:
            assert False, "Saved file is not valid JSON"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])