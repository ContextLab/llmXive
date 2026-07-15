"""
Unit tests for versioning module.
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest

from code.versioning import (
    compute_sha256,
    compute_directory_hash,
    ensure_state_directory,
    load_state,
    save_state,
    update_artifact_state,
    record_pipeline_run,
    get_artifact_hash,
    verify_artifact_integrity,
    get_project_state_summary
)

@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content for hashing")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_dir():
    """Create a temporary directory with files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a subdirectory
        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        
        # Create files
        (Path(tmpdir) / "file1.txt").write_text("content 1")
        (Path(tmpdir) / "file2.txt").write_text("content 2")
        (subdir / "file3.txt").write_text("content 3")
        
        yield tmpdir

@pytest.fixture
def temp_state_file():
    """Create a temporary state file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_compute_sha256(temp_file):
    """Test SHA-256 computation on a file."""
    hash1 = compute_sha256(temp_file)
    hash2 = compute_sha256(temp_file)
    assert len(hash1) == 64  # SHA-256 hex length
    assert hash1 == hash2

def test_compute_directory_hash(temp_dir):
    """Test directory hash computation."""
    hash1 = compute_directory_hash(temp_dir)
    hash2 = compute_directory_hash(temp_dir)
    assert len(hash1) == 64
    assert hash1 == hash2

def test_ensure_state_directory():
    """Test state directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir) / "state" / "projects"
        result = ensure_state_directory(str(base))
        assert result.exists()
        assert result.is_dir()

def test_load_state_nonexistent(temp_state_file):
    """Test loading a non-existent state file."""
    state = load_state(temp_state_file)
    assert state == {"artifacts": {}, "runs": [], "last_updated": None}

def test_save_and_load_state(temp_state_file):
    """Test saving and loading state."""
    test_state = {
        "artifacts": {"test.txt": {"path": "test.txt", "hash": "abc123"}},
        "runs": [{"timestamp": "2023-01-01T00:00:00"}],
        "last_updated": "2023-01-01T00:00:00"
    }
    
    save_state(test_state, temp_state_file)
    loaded = load_state(temp_state_file)
    
    assert loaded["artifacts"] == test_state["artifacts"]
    assert loaded["runs"] == test_state["runs"]
    assert loaded["last_updated"] == test_state["last_updated"]

def test_update_artifact_state(temp_file, temp_state_file):
    """Test updating artifact state."""
    update_artifact_state(temp_file, temp_state_file)
    
    state = load_state(temp_state_file)
    artifact_name = os.path.basename(temp_file)
    
    assert artifact_name in state["artifacts"]
    assert state["artifacts"][artifact_name]["path"] == os.path.relpath(temp_file)
    assert "hash" in state["artifacts"][artifact_name]
    assert "updated" in state["artifacts"][artifact_name]

def test_record_pipeline_run(temp_state_file):
    """Test recording a pipeline run."""
    metrics = {"duration": 10.5, "success": True}
    record_pipeline_run(temp_state_file, metrics)
    
    state = load_state(temp_state_file)
    assert len(state["runs"]) == 1
    assert state["runs"][0]["metrics"] == metrics
    assert "timestamp" in state["runs"][0]

def test_get_artifact_hash(temp_file):
    """Test getting artifact hash."""
    hash_val = get_artifact_hash(temp_file)
    assert len(hash_val) == 64

def test_get_artifact_hash_nonexistent():
    """Test getting hash for non-existent file."""
    assert get_artifact_hash("nonexistent_file.txt") is None

def test_verify_artifact_integrity(temp_file, temp_state_file):
    """Test artifact integrity verification."""
    update_artifact_state(temp_file, temp_state_file)
    state = load_state(temp_state_file)
    artifact_name = os.path.basename(temp_file)
    expected_hash = state["artifacts"][artifact_name]["hash"]
    
    assert verify_artifact_integrity(temp_file, expected_hash, temp_state_file) is True
    assert verify_artifact_integrity(temp_file, "wrong_hash", temp_state_file) is False

def test_get_project_state_summary(temp_state_file):
    """Test getting project state summary."""
    # Add some data
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test")
        temp_path = f.name
    
    try:
        update_artifact_state(temp_path, temp_state_file)
        record_pipeline_run(temp_state_file)
        
        summary = get_project_state_summary(temp_state_file)
        
        assert "last_updated" in summary
        assert "artifact_count" in summary
        assert "run_count" in summary
        assert "artifacts" in summary
        assert summary["artifact_count"] == 1
        assert summary["run_count"] == 1
    finally:
        os.unlink(temp_path)
