"""
Tests for checksum management functionality.
"""

import os
import json
import tempfile
from pathlib import Path
import pytest

from src.data.checksums import (
    compute_directory_checksums,
    save_checksums,
    load_checksums,
    verify_checksums,
    _get_checksum_file_path,
    CHECKSUM_FILE_NAME
)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory with some test files."""
    # Create subdirectories
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "subdir").mkdir()

    # Create test files
    file1 = raw_dir / "test1.csv"
    file1.write_text("col1,col2\n1,2\n3,4\n")

    file2 = raw_dir / "subdir" / "test2.csv"
    file2.write_text("col1,col2\n5,6\n7,8\n")

    file3 = raw_dir / "test3.json"
    file3.write_text('{"key": "value"}')

    return tmp_path


def test_compute_directory_checksums(temp_data_dir):
    """Test that checksums are computed correctly for all files."""
    checksums = compute_directory_checksums(temp_data_dir)

    # Should find 3 files
    assert len(checksums) == 3

    # Check that all expected files are present
    assert "test1.csv" in checksums
    assert "subdir/test2.csv" in checksums
    assert "test3.json" in checksums

    # Check structure of each entry
    for rel_path, info in checksums.items():
        assert "sha256" in info
        assert "size_bytes" in info
        assert "timestamp" in info
        assert len(info["sha256"]) == 64  # SHA-256 hex length

def test_save_and_load_checksums(temp_data_dir):
    """Test saving and loading checksums to/from JSON."""
    checksums = compute_directory_checksums(temp_data_dir)

    # Save checksums
    saved_path = save_checksums(checksums, temp_data_dir)
    assert saved_path.exists()
    assert saved_path.name == CHECKSUM_FILE_NAME

    # Load checksums
    loaded_checksums = load_checksums(temp_data_dir)
    assert loaded_checksums is not None
    assert len(loaded_checksums) == len(checksums)

    # Verify checksums match
    for rel_path, info in checksums.items():
        assert rel_path in loaded_checksums
        assert loaded_checksums[rel_path]["sha256"] == info["sha256"]

def test_save_checksums_excludes_itself(temp_data_dir):
    """Test that the checksum file is excluded from checksums."""
    checksums = compute_directory_checksums(temp_data_dir)
    save_checksums(checksums, temp_data_dir)

    # Recompute checksums - should still be 3 files, not 4
    new_checksums = compute_directory_checksums(temp_data_dir)
    assert len(new_checksums) == 3
    assert CHECKSUM_FILE_NAME not in new_checksums

def test_verify_checksums_valid(temp_data_dir):
    """Test verification when files haven't changed."""
    checksums = compute_directory_checksums(temp_data_dir)
    save_checksums(checksums, temp_data_dir)

    results = verify_checksums(temp_data_dir)

    # All files should verify successfully
    assert len(results) == 3
    assert all(results.values())

def test_verify_checksums_modified_file(temp_data_dir):
    """Test verification when a file has been modified."""
    checksums = compute_directory_checksums(temp_data_dir)
    save_checksums(checksums, temp_data_dir)

    # Modify a file
    file_path = temp_data_dir / "test1.csv"
    file_path.write_text("modified content\n")

    results = verify_checksums(temp_data_dir)

    # The modified file should fail verification
    assert results["test1.csv"] is False
    assert results["subdir/test2.csv"] is True
    assert results["test3.json"] is True

def test_verify_checksums_missing_file(temp_data_dir):
    """Test verification when a file is missing."""
    checksums = compute_directory_checksums(temp_data_dir)
    save_checksums(checksums, temp_data_dir)

    # Delete a file
    file_path = temp_data_dir / "test3.json"
    file_path.unlink()

    results = verify_checksums(temp_data_dir)

    # The missing file should fail verification
    assert results["test3.json"] is False
    assert results["test1.csv"] is True
    assert results["subdir/test2.csv"] is True

def test_verify_checksums_no_stored(temp_data_dir):
    """Test verification when no checksums are stored."""
    results = verify_checksums(temp_data_dir)
    assert results == {}

def test_get_checksum_file_path():
    """Test the checksum file path helper."""
    data_dir = Path("/some/data/dir")
    expected = data_dir / CHECKSUM_FILE_NAME
    result = _get_checksum_file_path(data_dir)
    assert result == expected
    assert result.name == CHECKSUM_FILE_NAME
