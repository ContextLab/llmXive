"""
Unit tests for code/hasher.py
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

from code.hasher import (
    compute_directory_hashes,
    compute_file_hash,
    load_hash_manifest,
    save_hash_manifest,
    verify_file_hash,
)


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    # Create nested structure
    dir1 = tmp_path / "subdir1"
    dir1.mkdir()
    dir2 = tmp_path / "subdir2"
    dir2.mkdir()

    # Create test files
    file1 = tmp_path / "file1.txt"
    file1.write_text("hello world")

    file2 = dir1 / "file2.json"
    file2.write_text('{"key": "value"}')

    file3 = dir2 / "file3.csv"
    file3.write_text("a,b\n1,2")

    return tmp_path


def test_compute_file_hash(tmp_path):
    """Test computing hash of a single file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    # Compute hash
    hash_val = compute_file_hash(test_file)

    # Verify it's a valid hex string of correct length for sha256
    assert len(hash_val) == 64
    assert all(c in "0123456789abcdef" for c in hash_val)

    # Verify determinism
    hash_val2 = compute_file_hash(test_file)
    assert hash_val == hash_val2


def test_compute_file_hash_nonexistent():
    """Test that computing hash of non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash("/nonexistent/path/file.txt")


def test_compute_file_hash_md5(tmp_path):
    """Test computing hash with different algorithm."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")

    hash_md5 = compute_file_hash(test_file, algorithm="md5")
    assert len(hash_md5) == 32  # MD5 is 32 hex chars


def test_verify_file_hash_success(tmp_path):
    """Test successful hash verification."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("verify me")

    actual_hash = compute_file_hash(test_file)
    assert verify_file_hash(test_file, actual_hash) is True


def test_verify_file_hash_failure(tmp_path):
    """Test failed hash verification."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("wrong hash")

    wrong_hash = "a" * 64
    assert verify_file_hash(test_file, wrong_hash) is False


def test_compute_directory_hashes(temp_dir):
    """Test computing hashes for all files in a directory."""
    hashes = compute_directory_hashes(temp_dir)

    assert len(hashes) == 3
    assert "file1.txt" in hashes
    assert "subdir1/file2.json" in hashes
    assert "subdir2/file3.csv" in hashes

    # Verify hashes are non-empty
    for h in hashes.values():
        assert len(h) == 64


def test_compute_directory_hashes_with_extension_filter(temp_dir):
    """Test filtering files by extension."""
    hashes = compute_directory_hashes(temp_dir, extensions=[".json"])

    assert len(hashes) == 1
    assert "subdir1/file2.json" in hashes


def test_compute_directory_hashes_nonexistent():
    """Test that computing hashes for non-existent directory raises error."""
    with pytest.raises(NotADirectoryError):
        compute_directory_hashes("/nonexistent/dir")


def test_save_and_load_hash_manifest(tmp_path):
    """Test saving and loading hash manifest."""
    test_hashes = {
        "file1.txt": "abc123",
        "file2.txt": "def456",
    }
    metadata = {"version": "1.0", "author": "test"}

    manifest_path = tmp_path / "manifest.json"
    save_hash_manifest(manifest_path, test_hashes, metadata)

    # Verify file exists
    assert manifest_path.exists()

    # Load and verify content
    loaded = load_hash_manifest(manifest_path)

    assert loaded["algorithm"] == "sha256"
    assert loaded["hashes"] == test_hashes
    assert loaded["metadata"] == metadata


def test_load_hash_manifest_nonexistent():
    """Test that loading non-existent manifest raises error."""
    with pytest.raises(FileNotFoundError):
        load_hash_manifest("/nonexistent/manifest.json")


def test_save_hash_manifest_creates_directories(tmp_path):
    """Test that save_hash_manifest creates parent directories if needed."""
    deep_path = tmp_path / "deep" / "nested" / "manifest.json"
    test_hashes = {"file.txt": "hash123"}

    save_hash_manifest(deep_path, test_hashes)

    assert deep_path.exists()
    assert json.load(open(deep_path))["hashes"] == test_hashes