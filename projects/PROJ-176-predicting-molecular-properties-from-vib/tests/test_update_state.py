import os
import tempfile
import yaml
from pathlib import Path
import pytest

# Adjust import based on project structure
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from utils.update_state import (
    compute_sha256,
    load_state,
    save_state,
    update_artifact_state,
    update_task_state,
    hash_multiple_artifacts,
    get_artifact_hash,
    verify_artifact_integrity,
    STATE_DIR
)

@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary directory for state files."""
    # Override STATE_DIR temporarily for testing
    original_dir = STATE_DIR
    # We can't easily override the global constant in the module, 
    # so we pass the temp path explicitly to functions via state_file arg
    return tmp_path

@pytest.fixture
def sample_file(tmp_path):
    """Create a sample file for hashing."""
    file_path = tmp_path / "sample.txt"
    content = "Hello, World!"
    file_path.write_text(content)
    return file_path

@pytest.fixture
def sample_large_file(tmp_path):
    """Create a larger sample file to test chunked reading."""
    file_path = tmp_path / "large.bin"
    content = b"x" * (1024 * 1024)  # 1MB
    file_path.write_bytes(content)
    return file_path

def test_compute_sha256_basic(sample_file):
    """Test basic SHA-256 computation."""
    h = compute_sha256(sample_file)
    assert len(h) == 64  # Hex string length for SHA-256
    assert all(c in '0123456789abcdef' for c in h)

def test_compute_sha256_deterministic(sample_file):
    """Test that hash is deterministic."""
    h1 = compute_sha256(sample_file)
    h2 = compute_sha256(sample_file)
    assert h1 == h2

def test_compute_sha256_large_file(sample_large_file):
    """Test hashing a large file (chunked reading)."""
    h = compute_sha256(sample_large_file)
    assert len(h) == 64

def test_compute_sha256_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/nonexistent/file.txt"))

def test_load_state_nonexistent(temp_state_dir):
    """Test loading state from a non-existent file."""
    state_file = temp_state_dir / "nonexistent.yaml"
    state = load_state(state_file)
    assert state == {"last_updated": None, "artifacts": {}, "tasks": {}}

def test_save_and_load_state(temp_state_dir):
    """Test saving and loading state."""
    state_file = temp_state_dir / "test_state.yaml"
    test_state = {
        "last_updated": "2023-01-01T00:00:00",
        "artifacts": {"file1.txt": {"hash": "abc123"}},
        "tasks": {"T001": {"status": "done"}}
    }
    save_state(test_state, state_file)
    
    loaded = load_state(state_file)
    assert loaded == test_state

def test_update_artifact_state(sample_file, temp_state_dir):
    """Test updating artifact state."""
    state_file = temp_state_dir / "test_state.yaml"
    state = update_artifact_state(sample_file, state_file)
    
    assert "artifacts" in state
    key = str(sample_file)
    assert key in state["artifacts"]
    assert "hash" in state["artifacts"][key]
    assert len(state["artifacts"][key]["hash"]) == 64
    assert "last_modified" in state["artifacts"][key]
    assert "size_bytes" in state["artifacts"][key]
    
    # Verify the hash matches the computed one
    assert state["artifacts"][key]["hash"] == compute_sha256(sample_file)

def test_update_task_state(temp_state_dir):
    """Test updating task state."""
    state_file = temp_state_dir / "test_state.yaml"
    state = update_task_state("T005", "completed", state_file, {"note": "test"})
    
    assert "tasks" in state
    assert "T005" in state["tasks"]
    assert state["tasks"]["T005"]["status"] == "completed"
    assert len(state["tasks"]["T005"]["history"]) == 1
    assert state["tasks"]["T005"]["history"][0]["details"]["note"] == "test"
    
    # Update again
    state = update_task_state("T005", "running", state_file)
    assert len(state["tasks"]["T005"]["history"]) == 2
    assert state["tasks"]["T005"]["status"] == "running"

def test_hash_multiple_artifacts(temp_state_dir):
    """Test hashing multiple artifacts."""
    temp_file = temp_state_dir.parent
    file1 = temp_file / "f1.txt"
    file2 = temp_file / "f2.txt"
    file1.write_text("data1")
    file2.write_text("data2")
    
    state_file = temp_state_dir / "test_state.yaml"
    results = hash_multiple_artifacts([file1, file2], state_file)
    
    assert str(file1) in results
    assert str(file2) in results
    assert results[str(file1)] == compute_sha256(file1)
    assert results[str(file2)] == compute_sha256(file2)

def test_get_artifact_hash(sample_file, temp_state_dir):
    """Test retrieving stored artifact hash."""
    state_file = temp_state_dir / "test_state.yaml"
    
    # Initially not found
    assert get_artifact_hash(sample_file, state_file) is None
    
    # After update
    update_artifact_state(sample_file, state_file)
    stored = get_artifact_hash(sample_file, state_file)
    assert stored == compute_sha256(sample_file)

def test_verify_artifact_integrity(sample_file, temp_state_dir):
    """Test artifact integrity verification."""
    state_file = temp_state_dir / "test_state.yaml"
    
    # First call updates and returns True
    assert verify_artifact_integrity(sample_file, state_file) is True
    
    # Modify file
    sample_file.write_text("modified")
    
    # Should return False
    assert verify_artifact_integrity(sample_file, state_file) is False

def test_verify_missing_artifact():
    """Test verifying a missing artifact raises error."""
    with pytest.raises(FileNotFoundError):
        verify_artifact_integrity(Path("/nonexistent/file.txt"))
