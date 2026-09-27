"""
Unit tests for code/utils/state_manager.py
"""
import pytest
import tempfile
import os
from pathlib import Path
from utils.state_manager import (
    compute_file_hash, 
    compute_data_hash, 
    load_state_file, 
    save_state_file,
    update_artifact_state
)

def test_compute_file_hash(tmp_path):
    """Test file hash computation on a real file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")
    
    hash_val = compute_file_hash(test_file)
    assert hash_val is not None
    assert len(hash_val) == 64  # SHA-256 hex length

def test_compute_data_hash():
    """Test hash computation on raw data."""
    data = b"test data"
    hash_val = compute_data_hash(data)
    assert hash_val is not None

def test_save_and_load_state_file(tmp_path):
    """Test saving and loading a state YAML file."""
    state_file = tmp_path / "state.yaml"
    test_state = {
        "version": "1.0",
        "artifacts": {
            "test": {"hash": "abc123"}
        }
    }
    
    save_state_file(state_file, test_state)
    loaded = load_state_file(state_file)
    
    assert loaded is not None
    assert loaded["version"] == "1.0"
    assert loaded["artifacts"]["test"]["hash"] == "abc123"

def test_update_artifact_state(tmp_path):
    """Test updating a specific artifact in state."""
    state_file = tmp_path / "state.yaml"
    initial_state = {"artifacts": {}}
    save_state_file(state_file, initial_state)
    
    update_artifact_state(state_file, "new_artifact", {"hash": "xyz789", "updated": True})
    
    loaded = load_state_file(state_file)
    assert "new_artifact" in loaded["artifacts"]
    assert loaded["artifacts"]["new_artifact"]["hash"] == "xyz789"
