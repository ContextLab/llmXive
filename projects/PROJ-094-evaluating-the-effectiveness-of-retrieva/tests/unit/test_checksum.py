"""
Unit tests for src/data/checksum.py
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
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        data_raw = project_root / "data" / "raw"
        data_raw.mkdir(parents=True)
        yield project_root


def test_calculate_sha256(temp_project_dir):
    """Test SHA-256 calculation for a known file."""
    file_path = temp_project_dir / "data" / "raw" / "test.txt"
    content = b"Hello, World!"
    file_path.write_bytes(content)

    expected_hash = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
    assert calculate_sha256(file_path) == expected_hash


def test_calculate_sha256_missing_file(temp_project_dir):
    """Test that calculating hash for a missing file raises FileNotFoundError."""
    file_path = temp_project_dir / "data" / "raw" / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        calculate_sha256(file_path)


def test_calculate_sha256_directory(temp_project_dir):
    """Test that calculating hash for a directory raises IsADirectoryError."""
    dir_path = temp_project_dir / "data" / "raw"
    with pytest.raises(IsADirectoryError):
        calculate_sha256(dir_path)


def test_load_state_empty(temp_project_dir):
    """Test loading state from a non-existent file returns empty dict."""
    state_file = get_state_file_path(temp_project_dir)
    assert load_state(state_file) == {}


def test_save_and_load_state(temp_project_dir):
    """Test saving and loading state preserves data."""
    state_file = get_state_file_path(temp_project_dir)
    test_state = {"file1.txt": "abc123", "file2.txt": "def456"}

    save_state(state_file, test_state)
    loaded_state = load_state(state_file)

    assert loaded_state == test_state


def test_register_file(temp_project_dir):
    """Test registering a file updates the state."""
    file_path = temp_project_dir / "data" / "raw" / "test.txt"
    file_path.write_text("test content")

    state = {}
    register_file(file_path, state, temp_project_dir)

    assert len(state) == 1
    assert "data/raw/test.txt" in state
    assert len(state["data/raw/test.txt"]) == 64  # SHA-256 hex length


def test_verify_file_match(temp_project_dir):
    """Test verifying a file that matches the stored hash."""
    file_path = temp_project_dir / "data" / "raw" / "test.txt"
    file_path.write_text("test content")

    state = {}
    register_file(file_path, state, temp_project_dir)

    is_valid, error_msg = verify_file(file_path, state, temp_project_dir)
    assert is_valid is True
    assert error_msg is None


def test_verify_file_mismatch(temp_project_dir):
    """Test verifying a file that has been modified."""
    file_path = temp_project_dir / "data" / "raw" / "test.txt"
    file_path.write_text("original content")

    state = {}
    register_file(file_path, state, temp_project_dir)

    # Modify the file
    file_path.write_text("modified content")

    is_valid, error_msg = verify_file(file_path, state, temp_project_dir)
    assert is_valid is False
    assert "Checksum mismatch" in error_msg


def test_verify_file_missing(temp_project_dir):
    """Test verifying a file that has been deleted."""
    file_path = temp_project_dir / "data" / "raw" / "test.txt"
    file_path.write_text("test content")

    state = {}
    register_file(file_path, state, temp_project_dir)

    # Delete the file
    file_path.unlink()

    is_valid, error_msg = verify_file(file_path, state, temp_project_dir)
    assert is_valid is False
    assert "File missing" in error_msg


def test_verify_all(temp_project_dir):
    """Test verifying all registered files."""
    file1 = temp_project_dir / "data" / "raw" / "test1.txt"
    file2 = temp_project_dir / "data" / "raw" / "test2.txt"
    file1.write_text("content 1")
    file2.write_text("content 2")

    state = {}
    register_file(file1, state, temp_project_dir)
    register_file(file2, state, temp_project_dir)

    # Verify all pass
    all_valid, errors = verify_all(temp_project_dir)
    assert all_valid is True
    assert len(errors) == 0

    # Modify one file
    file1.write_text("modified content 1")

    all_valid, errors = verify_all(temp_project_dir)
    assert all_valid is False
    assert len(errors) == 1
    assert "data/raw/test1.txt" in errors[0]


def test_check_and_register_missing_files(temp_project_dir):
    """Test checking and registering missing files."""
    file1 = temp_project_dir / "data" / "raw" / "test1.txt"
    file2 = temp_project_dir / "data" / "raw" / "test2.txt"
    file1.write_text("content 1")
    file2.write_text("content 2")

    state_file = get_state_file_path(temp_project_dir)
    # Save empty state initially
    save_state(state_file, {})

    count, registered = check_and_register_missing_files(temp_project_dir / "data" / "raw", temp_project_dir)

    assert count == 2
    assert len(registered) == 2
    assert "data/raw/test1.txt" in registered
    assert "data/raw/test2.txt" in registered

    # Check state file was updated
    loaded_state = load_state(state_file)
    assert len(loaded_state) == 2