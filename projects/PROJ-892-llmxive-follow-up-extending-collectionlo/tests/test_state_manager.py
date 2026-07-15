"""
Unit tests for code/state_manager.py functions.

These tests verify the correctness of artifact hashing, registration,
and state management.
"""
import hashlib
import yaml
import tempfile
import os
from pathlib import Path
import pytest

from state_manager import (
    compute_sha256,
    register_artifact,
    load_artifacts_state,
    save_artifacts_state,
    verify_artifact,
    get_artifact_hash
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file for testing."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Hello, World!")
    return file_path

def test_compute_sha256(sample_file):
    """Test SHA256 hash computation."""
    hash_value = compute_sha256(sample_file)
    
    assert hash_value is not None
    assert len(hash_value) == 64  # SHA256 produces 64 hex characters
    assert all(c in '0123456789abcdef' for c in hash_value)

def test_compute_sha256_consistency(sample_file):
    """Test that SHA256 hash is consistent across multiple calls."""
    hash1 = compute_sha256(sample_file)
    hash2 = compute_sha256(sample_file)
    assert hash1 == hash2

def test_register_artifact(temp_dir):
    """Test artifact registration."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("test content")
    
    artifacts = {}
    updated_state = register_artifact(
        file_path, 
        "test_artifact", 
        artifacts
    )
    
    assert "test_artifact" in updated_state
    assert updated_state["test_artifact"]["path"] == str(file_path)
    assert "hash" in updated_state["test_artifact"]

def test_verify_artifact(temp_dir):
    """Test artifact verification."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("test content")
    
    # First register the artifact
    artifacts = {}
    state = register_artifact(file_path, "test_artifact", artifacts)
    
    # Then verify it
    is_valid, _ = verify_artifact(file_path, state["test_artifact"]["hash"])
    assert is_valid

def test_verify_artifact_modified(temp_dir):
    """Test artifact verification fails when file is modified."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("test content")
    
    # Register the artifact
    artifacts = {}
    state = register_artifact(file_path, "test_artifact", artifacts)
    
    # Modify the file
    file_path.write_text("modified content")
    
    # Verification should fail
    is_valid, _ = verify_artifact(file_path, state["test_artifact"]["hash"])
    assert not is_valid

def test_save_and_load_artifacts_state(temp_dir):
    """Test saving and loading artifacts state."""
    artifacts = {
        "test_artifact": {
            "path": "data/test.txt",
            "hash": "abc123"
        }
    }
    
    state_file = temp_dir / "artifacts.yaml"
    save_artifacts_state(artifacts, state_file)
    
    # Verify file was created
    assert state_file.exists()
    
    # Load and verify content
    loaded_state = load_artifacts_state(state_file)
    assert loaded_state is not None
    assert "test_artifact" in loaded_state
    assert loaded_state["test_artifact"]["hash"] == "abc123"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
