"""
Unit tests for src/data/checksum.py functionality.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.checksum import (
    calculate_sha256,
    load_state,
    save_state,
    verify_file,
    register_file,
    verify_all,
    check_and_register_missing_files,
    get_state_file_path,
    STATE_FILE_NAME
)


@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_file(temp_project_root):
    """Create a temporary file with known content."""
    file_path = Path(temp_project_root) / "test_file.txt"
    content = "Hello, World!"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def large_temp_file(temp_project_root):
    """Create a larger temporary file to test chunked reading."""
    file_path = Path(temp_project_root) / "large_file.bin"
    # Create a file larger than the chunk size (8KB)
    content = b"A" * (100 * 1024)  # 100KB
    file_path.write_bytes(content)
    return file_path


def test_calculate_sha256_basic(temp_file):
    """Test basic SHA-256 calculation."""
    # Known hash for "Hello, World!"
    expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    calculated_hash = calculate_sha256(temp_file)
    assert calculated_hash == expected_hash


def test_calculate_sha256_large_file(large_temp_file):
    """Test SHA-256 calculation on a file larger than chunk size."""
    # We can't easily verify the exact hash, but we can verify it runs
    # and produces a valid hex string of the correct length.
    calculated_hash = calculate_sha256(large_temp_file)
    assert len(calculated_hash) == 64
    assert all(c in "0123456789abcdef" for c in calculated_hash)


def test_calculate_sha256_nonexistent_file():
    """Test that FileNotFoundError is raised for non-existent files."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256("/nonexistent/path/file.txt")


def test_calculate_sha256_directory(temp_project_root):
    """Test that IsADirectoryError is raised for directories."""
    with pytest.raises(IsADirectoryError):
        calculate_sha256(temp_project_root)


def test_load_state_empty(temp_project_root):
    """Test loading state when no state file exists."""
    state = load_state(temp_project_root)
    assert state == {}


def test_save_and_load_state(temp_project_root):
    """Test saving and loading state."""
    test_state = {
        "file1.txt": "hash1",
        "file2.txt": "hash2"
    }
    save_state(temp_project_root, test_state)

    loaded_state = load_state(temp_project_root)
    assert loaded_state == test_state


def test_verify_file_match(temp_file):
    """Test verifying a file with the correct hash."""
    correct_hash = calculate_sha256(temp_file)
    assert verify_file(temp_file, correct_hash) is True


def test_verify_file_mismatch(temp_file):
    """Test verifying a file with an incorrect hash."""
    wrong_hash = "0" * 64
    assert verify_file(temp_file, wrong_hash) is False


def test_verify_file_nonexistent(temp_project_root):
    """Test verifying a non-existent file."""
    assert verify_file(Path(temp_project_root) / "missing.txt", "hash") is False


def test_register_file(temp_file, temp_project_root):
    """Test registering a new file."""
    success, message = register_file(temp_file, temp_project_root)
    assert success is True
    assert "Registered" in message

    # Verify it's in the state
    state = load_state(temp_project_root)
    assert str(temp_file) in state
    assert state[str(temp_file)] == calculate_sha256(temp_file)


def test_register_missing_file(temp_project_root):
    """Test registering a non-existent file."""
    missing_path = Path(temp_project_root) / "missing.txt"
    success, message = register_file(missing_path, temp_project_root)
    assert success is False
    assert "not found" in message


def test_verify_all_empty(temp_project_root):
    """Test verifying all when no files are registered."""
    results = verify_all(temp_project_root)
    assert results == {}


def test_verify_all(temp_file, temp_project_root):
    """Test verifying multiple files."""
    # Register the file
    register_file(temp_file, temp_project_root)

    # Verify
    results = verify_all(temp_project_root)
    assert len(results) == 1
    assert results[str(temp_file)] is True


def test_verify_all_missing_file(temp_file, temp_project_root):
    """Test verifying when a file is deleted."""
    # Register the file
    register_file(temp_file, temp_project_root)

    # Delete the file
    temp_file.unlink()

    # Verify - should return False for missing file
    results = verify_all(temp_project_root)
    assert results[str(temp_file)] is False


def test_check_and_register_missing_files_new_files(temp_project_root):
    """Test checking and registering new files."""
    file1 = Path(temp_project_root) / "new1.txt"
    file2 = Path(temp_project_root) / "new2.txt"
    file1.write_text("content1")
    file2.write_text("content2")

    status = check_and_register_missing_files([file1, file2], temp_project_root)

    assert status[str(file1)] == "registered"
    assert status[str(file2)] == "registered"

    # Verify in state
    state = load_state(temp_project_root)
    assert str(file1) in state
    assert str(file2) in state


def test_check_and_register_missing_files_existing_files(temp_file, temp_project_root):
    """Test checking files that are already registered."""
    # Register the file first
    register_file(temp_file, temp_project_root)

    status = check_and_register_missing_files([temp_file], temp_project_root)

    assert status[str(temp_file)] == "verified"


def test_check_and_register_missing_files_mismatch(temp_file, temp_project_root):
    """Test checking files with changed content."""
    # Register the file
    register_file(temp_file, temp_project_root)

    # Modify the file
    temp_file.write_text("modified content")

    status = check_and_register_missing_files([temp_file], temp_project_root)

    assert status[str(temp_file)] == "mismatch"

    # Verify state was updated
    state = load_state(temp_project_root)
    assert state[str(temp_file)] == calculate_sha256(temp_file)


def test_get_state_file_path(temp_project_root):
    """Test getting the state file path."""
    expected_path = Path(temp_project_root) / STATE_FILE_NAME
    actual_path = get_state_file_path(temp_project_root)
    assert actual_path == expected_path
