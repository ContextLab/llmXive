"""
Unit tests for checksum verification and state file management.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
from src.data.checksum import (
    get_state_file_path,
    calculate_sha256,
    load_state,
    save_state,
    verify_file,
    register_file,
    verify_all,
    check_and_register_missing_files,
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        # Create a src/data directory structure
        (tmpdir_path / "src" / "data").mkdir(parents=True)
        yield tmpdir_path


def test_calculate_sha256(temp_project_dir):
    """Test calculating SHA256 hash of a file."""
    # Create a test file
    test_file = temp_project_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    # Calculate hash
    file_hash = calculate_sha256(test_file)
    
    # Verify hash (known value for "Hello, World!")
    expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert file_hash == expected_hash


def test_calculate_sha256_missing_file(temp_project_dir):
    """Test that calculate_sha256 raises FileNotFoundError for missing file."""
    missing_file = temp_project_dir / "nonexistent.txt"
    
    with pytest.raises(FileNotFoundError):
        calculate_sha256(missing_file)


def test_calculate_sha256_directory(temp_project_dir):
    """Test that calculate_sha256 raises IsADirectoryError for directories."""
    with pytest.raises(IsADirectoryError):
        calculate_sha256(temp_project_dir)


def test_load_state_empty(temp_project_dir):
    """Test loading state from non-existent file returns empty dict."""
    state_file = temp_project_dir / "state.json"
    
    state = load_state(state_file)
    assert state == {}


def test_save_and_load_state(temp_project_dir):
    """Test saving and loading state."""
    state_file = temp_project_dir / "state.json"
    test_state = {
        "/path/to/file1.txt": "hash1",
        "/path/to/file2.txt": "hash2"
    }
    
    save_state(test_state, state_file)
    loaded_state = load_state(state_file)
    
    assert loaded_state == test_state


def test_register_file(temp_project_dir):
    """Test registering a file."""
    # Create a test file
    test_file = temp_project_dir / "test.txt"
    test_content = b"Test content"
    test_file.write_bytes(test_content)
    
    state_file = temp_project_dir / "state.json"
    
    # Register the file
    file_hash = register_file(test_file, state_file)
    
    # Verify the hash is correct
    expected_hash = calculate_sha256(test_file)
    assert file_hash == expected_hash
    
    # Verify the state file was updated
    state = load_state(state_file)
    assert str(test_file) in state
    assert state[str(test_file)] == expected_hash


def test_verify_file_match(temp_project_dir):
    """Test verifying a file with matching hash."""
    # Create a test file
    test_file = temp_project_dir / "test.txt"
    test_content = b"Test content"
    test_file.write_bytes(test_content)
    
    state_file = temp_project_dir / "state.json"
    
    # Register the file
    register_file(test_file, state_file)
    
    # Verify the file
    is_valid, message = verify_file(test_file, state_file)
    
    assert is_valid is True
    assert "Hash verified" in message


def test_verify_file_mismatch(temp_project_dir):
    """Test verifying a file with mismatched hash."""
    # Create a test file
    test_file = temp_project_dir / "test.txt"
    test_content = b"Test content"
    test_file.write_bytes(test_content)
    
    state_file = temp_project_dir / "state.json"
    
    # Register the file
    register_file(test_file, state_file)
    
    # Modify the file
    test_file.write_bytes(b"Modified content")
    
    # Verify the file - should fail
    is_valid, message = verify_file(test_file, state_file)
    
    assert is_valid is False
    assert "Hash mismatch" in message


def test_verify_file_missing(temp_project_dir):
    """Test verifying a file that doesn't exist."""
    state_file = temp_project_dir / "state.json"
    missing_file = temp_project_dir / "nonexistent.txt"
    
    # Register the non-existent file in state (simulate stale state)
    save_state({str(missing_file): "somehash"}, state_file)
    
    is_valid, message = verify_file(missing_file, state_file)
    
    assert is_valid is False
    assert "not found" in message


def test_verify_all(temp_project_dir):
    """Test verifying all registered files."""
    # Create test files
    file1 = temp_project_dir / "file1.txt"
    file2 = temp_project_dir / "file2.txt"
    file1.write_bytes(b"Content 1")
    file2.write_bytes(b"Content 2")
    
    state_file = temp_project_dir / "state.json"
    
    # Register both files
    register_file(file1, state_file)
    register_file(file2, state_file)
    
    # Verify all
    results = verify_all(state_file)
    
    assert len(results) == 2
    for file_path, is_valid, message in results:
        assert is_valid is True
        assert "Hash verified" in message


def test_check_and_register_missing_files(temp_project_dir):
    """Test checking and registering missing files."""
    # Create test files
    file1 = temp_project_dir / "file1.txt"
    file2 = temp_project_dir / "file2.txt"
    file1.write_bytes(b"Content 1")
    file2.write_bytes(b"Content 2")
    
    state_file = temp_project_dir / "state.json"
    
    # Initially register only file1
    register_file(file1, state_file)
    
    # Check and register missing files
    newly_registered = check_and_register_missing_files([temp_project_dir], state_file)
    
    # Should have registered file2
    assert len(newly_registered) == 1
    assert newly_registered[0][0] == file2
    
    # Verify state now contains both files
    state = load_state(state_file)
    assert len(state) == 2
    assert str(file1) in state
    assert str(file2) in state