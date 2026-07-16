"""
Unit tests for the hashing utility module.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.hashing import (
    compute_file_hash,
    compute_directory_hashes,
    load_state_file,
    save_state_file,
    update_state_hash,
    verify_artifact_integrity,
    get_artifact_hash,
    PROJECT_ROOT,
    STATE_DIR,
)

@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("test content for hashing")
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()

@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        # Create nested structure
        (tmp_path / "file1.txt").write_text("content 1")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.txt").write_text("content 2")
        yield tmp_path

@pytest.fixture
def mock_state_file(tmp_path):
    """Create a mock state file."""
    state_path = tmp_path / "state.yaml"
    save_state_file(state_path, {"project_id": "TEST", "artifacts": {}})
    return state_path

def test_compute_file_hash(temp_file):
    """Test that file hashing produces consistent results."""
    hash1 = compute_file_hash(temp_file)
    hash2 = compute_file_hash(temp_file)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length
    assert all(c in "0123456789abcdef" for c in hash1)

def test_compute_file_hash_different_content():
    """Test that different content produces different hashes."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f1:
        f1.write("content A")
        path1 = Path(f1.name)
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f2:
        f2.write("content B")
        path2 = Path(f2.name)
    
    try:
        hash1 = compute_file_hash(path1)
        hash2 = compute_file_hash(path2)
        assert hash1 != hash2
    finally:
        path1.unlink()
        path2.unlink()

def test_compute_file_hash_nonexistent():
    """Test that hashing a non-existent file raises an error."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash(Path("/nonexistent/path/file.txt"))

def test_compute_directory_hashes(temp_dir):
    """Test directory hashing returns all files."""
    hashes = compute_directory_hashes(temp_dir)
    
    assert len(hashes) == 2
    assert "file1.txt" in hashes
    assert "subdir/file2.txt" in hashes
    
    # Verify hashes are consistent
    assert hashes["file1.txt"] == compute_file_hash(temp_dir / "file1.txt")

def test_compute_directory_hashes_empty():
    """Test hashing an empty directory returns empty dict."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        hashes = compute_directory_hashes(Path(tmpdirname))
        assert hashes == {}

def test_compute_directory_hashes_nonexistent():
    """Test hashing a non-existent directory returns empty dict."""
    hashes = compute_directory_hashes(Path("/nonexistent/directory"))
    assert hashes == {}

def test_load_state_file_new(mock_state_file):
    """Test loading a newly created state file."""
    state = load_state_file(mock_state_file)
    assert "artifacts" in state
    assert "project_id" in state
    assert "version" in state

def test_save_and_load_state_file(tmp_path):
    """Test saving and loading state file round-trip."""
    state_path = tmp_path / "test_state.yaml"
    test_state = {
        "project_id": "TEST-001",
        "version": "1.0.0",
        "artifacts": {
            "data/file.csv": {"hash": "abc123", "updated_at": "2023-01-01T00:00:00"}
        }
    }
    
    save_state_file(state_path, test_state)
    loaded_state = load_state_file(state_path)
    
    assert loaded_state == test_state

def test_update_state_hash(tmp_path):
    """Test updating state hash with new artifacts."""
    # Create test files
    file1 = tmp_path / "test1.txt"
    file1.write_text("content 1")
    
    file2 = tmp_path / "test2.txt"
    file2.write_text("content 2")
    
    # Create state file
    state_path = tmp_path / "state.yaml"
    save_state_file(state_path, {"project_id": "TEST", "artifacts": {}})
    
    # Update state
    new_hashes = update_state_hash([file1, file2], state_path)
    
    assert len(new_hashes) == 2
    assert str(file1.relative_to(tmp_path)) in new_hashes
    assert str(file2.relative_to(tmp_path)) in new_hashes
    
    # Verify state file was updated
    state = load_state_file(state_path)
    assert len(state["artifacts"]) == 2

def test_verify_artifact_integrity(tmp_path):
    """Test artifact integrity verification."""
    # Create test files
    file1 = tmp_path / "test1.txt"
    file1.write_text("content 1")
    
    # Create state file with correct hash
    state_path = tmp_path / "state.yaml"
    initial_hash = compute_file_hash(file1)
    save_state_file(state_path, {
        "project_id": "TEST",
        "artifacts": {
            str(file1.relative_to(tmp_path)): {"hash": initial_hash, "updated_at": "2023-01-01T00:00:00"}
        }
    })
    
    # Verify should pass
    results = verify_artifact_integrity([file1], state_path)
    assert results[str(file1.relative_to(tmp_path))] is True
    
    # Modify file and verify should fail
    file1.write_text("modified content")
    results = verify_artifact_integrity([file1], state_path)
    assert results[str(file1.relative_to(tmp_path))] is False

def test_get_artifact_hash(tmp_path):
    """Test retrieving a specific artifact hash."""
    file1 = tmp_path / "test1.txt"
    file1.write_text("content 1")
    
    state_path = tmp_path / "state.yaml"
    expected_hash = compute_file_hash(file1)
    save_state_file(state_path, {
        "project_id": "TEST",
        "artifacts": {
            str(file1.relative_to(tmp_path)): {"hash": expected_hash, "updated_at": "2023-01-01T00:00:00"}
        }
    })
    
    retrieved_hash = get_artifact_hash(file1, state_path)
    assert retrieved_hash == expected_hash
    
    # Test non-existent artifact
    nonexistent = tmp_path / "nonexistent.txt"
    assert get_artifact_hash(nonexistent, state_path) is None

def test_update_state_hash_missing_file(tmp_path):
    """Test updating state with a missing file logs warning but continues."""
    missing_file = tmp_path / "missing.txt"
    existing_file = tmp_path / "existing.txt"
    existing_file.write_text("content")
    
    state_path = tmp_path / "state.yaml"
    save_state_file(state_path, {"project_id": "TEST", "artifacts": {}})
    
    # Should not raise, just log warning
    new_hashes = update_state_hash([missing_file, existing_file], state_path)
    
    assert len(new_hashes) == 1
    assert str(existing_file.relative_to(tmp_path)) in new_hashes

def test_verify_artifact_integrity_no_state(tmp_path):
    """Test verification when no state file exists."""
    file1 = tmp_path / "test1.txt"
    file1.write_text("content")
    
    results = verify_artifact_integrity([file1], tmp_path / "nonexistent.yaml")
    assert results[str(file1.relative_to(tmp_path))] is False