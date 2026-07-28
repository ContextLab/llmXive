"""
Unit tests for src/data/checksum.py
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

from src.data.checksum import (
    calculate_sha256,
    get_state_file_path,
    load_state,
    save_state,
    verify_file,
    register_file,
    verify_all,
    check_and_register_missing_files
)


@pytest.fixture
def temp_project_dir():
    """Creates a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        # Create data directory
        (project_root / "data").mkdir()
        # Create a test file
        test_file = project_root / "data" / "test.txt"
        test_file.write_text("Hello, World!")
        yield project_root, test_file


def test_calculate_sha256(temp_project_dir):
    """Test SHA-256 calculation on a known file."""
    _, test_file = temp_project_dir
    hash_val = calculate_sha256(test_file)
    assert len(hash_val) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in hash_val)


def test_calculate_sha256_missing_file():
    """Test that calculate_sha256 raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256(Path("/nonexistent/file.txt"))


def test_calculate_sha256_directory():
    """Test that calculate_sha256 raises IsADirectoryError for directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(IsADirectoryError):
            calculate_sha256(Path(tmpdir))


def test_load_state_empty(temp_project_dir):
    """Test loading state when no state file exists."""
    project_root, _ = temp_project_dir
    state = load_state(project_root)
    assert "files" in state
    assert "metadata" in state
    assert state["files"] == {}


def test_save_and_load_state(temp_project_dir):
    """Test saving and loading state."""
    project_root, test_file = temp_project_dir
    
    # Create a state
    state = {
        "files": {"test.txt": {"hash": "abc123"}},
        "metadata": {"created": "now", "last_updated": "later"}
    }
    save_state(state, project_root)
    
    # Load it back
    loaded = load_state(project_root)
    assert loaded["files"]["test.txt"]["hash"] == "abc123"
    assert loaded["metadata"]["last_updated"] is not None


def test_register_file(temp_project_dir):
    """Test registering a file."""
    project_root, test_file = temp_project_dir
    
    hash_val = register_file(test_file, project_root)
    
    state = load_state(project_root)
    relative_path = str(test_file.relative_to(project_root))
    
    assert relative_path in state["files"]
    assert state["files"][relative_path]["hash"] == hash_val
    assert "size_bytes" in state["files"][relative_path]


def test_verify_file_match(temp_project_dir):
    """Test verifying a file with matching hash."""
    project_root, test_file = temp_project_dir
    expected_hash = calculate_sha256(test_file)
    
    is_valid, msg = verify_file(test_file, expected_hash, project_root)
    assert is_valid
    assert "successfully" in msg.lower()


def test_verify_file_mismatch(temp_project_dir):
    """Test verifying a file with mismatched hash."""
    project_root, test_file = temp_project_dir
    wrong_hash = "0" * 64
    
    is_valid, msg = verify_file(test_file, wrong_hash, project_root)
    assert not is_valid
    assert "mismatch" in msg.lower()


def test_verify_file_missing(temp_project_dir):
    """Test verifying a missing file."""
    project_root, _ = temp_project_dir
    missing_file = project_root / "data" / "missing.txt"
    
    is_valid, msg = verify_file(missing_file, "fakehash", project_root)
    assert not is_valid
    assert "missing" in msg.lower()


def test_verify_all(temp_project_dir):
    """Test verifying all registered files."""
    project_root, test_file = temp_project_dir
    
    # Register the file
    register_file(test_file, project_root)
    
    # Verify all
    results = verify_all(project_root)
    relative_path = str(test_file.relative_to(project_root))
    
    assert relative_path in results
    assert results[relative_path] is True


def test_check_and_register_missing_files(temp_project_dir):
    """Test checking and registering missing files."""
    project_root, test_file = temp_project_dir
    
    # Initially state is empty
    state = load_state(project_root)
    assert len(state["files"]) == 0
    
    # Check and register
    newly_registered = check_and_register_missing_files([test_file], project_root)
    
    assert len(newly_registered) == 1
    assert test_file in newly_registered
    
    # Verify state now has the file
    state = load_state(project_root)
    relative_path = str(test_file.relative_to(project_root))
    assert relative_path in state["files"]