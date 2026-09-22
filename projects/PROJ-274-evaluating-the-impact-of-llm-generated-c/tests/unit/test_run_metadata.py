"""
Unit tests for the run metadata module.
"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
import uuid

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.utils.run_metadata import (
    generate_run_metadata,
    save_metadata,
    load_metadata,
    ensure_metadata_dir,
    state_dir
)

def test_generate_run_metadata_structure():
    """Test that generated metadata has required fields."""
    metadata = generate_run_metadata()
    assert "RUN_ID" in metadata, "RUN_ID missing"
    assert "start_time" in metadata, "start_time missing"
    assert "project_version" in metadata, "project_version missing"
    
    # Validate types
    assert isinstance(metadata["RUN_ID"], str), "RUN_ID must be string"
    assert isinstance(metadata["start_time"], str), "start_time must be string"
    assert isinstance(metadata["project_version"], str), "project_version must be string"

def test_generate_run_metadata_uuid_format():
    """Test that RUN_ID is a valid UUID."""
    metadata = generate_run_metadata()
    # This will raise ValueError if not a valid UUID
    uuid.UUID(metadata["RUN_ID"])

def test_save_and_load_metadata():
    """Test saving and loading metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily override state_dir for testing
        original_state_dir = state_dir
        
        # We cannot easily override the module-level variable, 
        # so we test the functions that take explicit paths or rely on the module logic.
        # Instead, we test the logic by saving to a temp file and loading it back.
        # We'll use the actual state_dir but ensure it exists.
        ensure_metadata_dir()
        
        test_metadata = {
            "RUN_ID": "test-uuid-1234",
            "start_time": "2023-01-01T00:00:00Z",
            "project_version": "0.0.1-test"
        }
        
        # Save to a specific temp filename within state_dir
        temp_filename = "test_run_metadata.json"
        file_path = save_metadata(test_metadata, filename=temp_filename)
        
        # Verify file exists
        assert file_path.exists(), "Metadata file was not created"
        
        # Load it back
        loaded = load_metadata(filename=temp_filename)
        
        assert loaded is not None, "Failed to load metadata"
        assert loaded["RUN_ID"] == test_metadata["RUN_ID"], "RUN_ID mismatch"
        assert loaded["start_time"] == test_metadata["start_time"], "start_time mismatch"
        assert loaded["project_version"] == test_metadata["project_version"], "project_version mismatch"
        
        # Cleanup test file
        file_path.unlink()

def test_load_nonexistent_metadata():
    """Test loading a nonexistent file returns None."""
    result = load_metadata(filename="nonexistent_run_metadata_12345.json")
    assert result is None, "Should return None for missing file"

if __name__ == "__main__":
    test_generate_run_metadata_structure()
    test_generate_run_metadata_uuid_format()
    test_save_and_load_metadata()
    test_load_nonexistent_metadata()
    print("All tests passed.")
