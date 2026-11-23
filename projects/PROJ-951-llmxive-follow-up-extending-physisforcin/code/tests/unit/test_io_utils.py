"""
Unit tests for src.utils.io_utils
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

import sys
# Ensure we can import from the code directory
code_root = Path(__file__).parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils.io_utils import (
    calculate_file_checksum,
    calculate_directory_checksums,
    save_checksums,
    load_checksums,
    verify_directory_integrity,
    update_checksums,
    get_file_size,
    get_total_size,
    cleanup_empty_dirs,
    move_files_with_checksums,
    validate_project_structure,
    get_data_stats,
    ensure_dirs
)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory with some files for testing."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()

    # Create some files
    (test_dir / "file1.txt").write_text("content1")
    (test_dir / "file2.txt").write_text("content2")
    (test_dir / "subdir").mkdir()
    (test_dir / "subdir" / "file3.txt").write_text("content3")

    return test_dir


@pytest.fixture
def populated_dir(tmp_path):
    """Create a directory with known content for checksum tests."""
    test_dir = tmp_path / "populated"
    test_dir.mkdir()
    (test_dir / "test.txt").write_text("Hello, World!")
    return test_dir


def test_ensure_dirs(tmp_path):
    """Test that ensure_dirs creates non-existent directories."""
    new_dir = tmp_path / "new" / "nested" / "dir"
    ensure_dirs([new_dir])
    assert new_dir.exists()
    assert new_dir.is_dir()

def test_ensure_dirs_existing(tmp_path):
    """Test that ensure_dirs does not fail on existing directories."""
    existing_dir = tmp_path / "existing"
    existing_dir.mkdir()
    ensure_dirs([existing_dir])
    assert existing_dir.exists()


def test_calculate_file_checksum(populated_dir):
    """Test file checksum calculation."""
    file_path = populated_dir / "test.txt"
    checksum = calculate_file_checksum(file_path)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length


def test_calculate_file_checksum_nonexistent():
    """Test that calculating checksum for non-existent file raises."""
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum("/nonexistent/path/file.txt")


def test_calculate_directory_checksums(temp_data_dir):
    """Test directory checksum calculation."""
    checksums = calculate_directory_checksums(temp_data_dir)
    assert len(checksums) == 3  # file1.txt, file2.txt, subdir/file3.txt
    assert "file1.txt" in checksums
    assert "subdir/file3.txt" in checksums


def test_save_and_load_checksums(tmp_path, populated_dir):
    """Test saving and loading checksums to/from JSON."""
    checksums = calculate_directory_checksums(populated_dir)
    output_path = tmp_path / "checksums.json"

    save_checksums(checksums, output_path)
    assert output_path.exists()

    loaded = load_checksums(output_path)
    assert loaded == checksums


def test_verify_directory_integrity(temp_data_dir):
    """Test directory integrity verification."""
    checksums = calculate_directory_checksums(temp_data_dir)
    is_valid, mismatches = verify_directory_integrity(temp_data_dir, checksums)
    assert is_valid
    assert len(mismatches) == 0

def test_verify_directory_integrity_modified(temp_data_dir):
    """Test verification fails when a file is modified."""
    checksums = calculate_directory_checksums(temp_data_dir)
    (temp_data_dir / "file1.txt").write_text("modified content")

    is_valid, mismatches = verify_directory_integrity(temp_data_dir, checksums)
    assert not is_valid
    assert len(mismatches) == 1
    assert "file1.txt" in mismatches[0]

def test_verify_directory_integrity_missing(temp_data_dir):
    """Test verification fails when a file is missing."""
    checksums = calculate_directory_checksums(temp_data_dir)
    (temp_data_dir / "file1.txt").unlink()

    is_valid, mismatches = verify_directory_integrity(temp_data_dir, checksums)
    assert not is_valid
    assert len(mismatches) == 1
    assert "Missing" in mismatches[0]


def test_update_checksums(tmp_path, temp_data_dir):
    """Test the update_checksums convenience function."""
    output_path = tmp_path / "updated_checksums.json"
    result = update_checksums(temp_data_dir, output_path)

    assert output_path.exists()
    assert len(result) == 3


def test_get_file_size(populated_dir):
    """Test getting file size."""
    file_path = populated_dir / "test.txt"
    size = get_file_size(file_path)
    assert size > 0
    assert size == len("Hello, World!")


def test_get_total_size(temp_data_dir):
    """Test getting total directory size."""
    total = get_total_size(temp_data_dir)
    assert total > 0
    # Should be sum of file sizes
    assert total == len("content1") + len("content2") + len("content3")


def test_cleanup_empty_dirs(tmp_path):
    """Test cleanup of empty directories."""
    # Create nested empty dirs
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)

    removed = cleanup_empty_dirs(tmp_path)
    assert removed == 3
    assert not deep.exists()
    assert not (tmp_path / "a").exists()

def test_cleanup_empty_dirs_non_empty(tmp_path):
    """Test that cleanup does not remove non-empty dirs."""
    (tmp_path / "non_empty").mkdir()
    (tmp_path / "non_empty" / "file.txt").write_text("data")

    removed = cleanup_empty_dirs(tmp_path)
    assert removed == 0
    assert (tmp_path / "non_empty").exists()


def test_move_files_with_checksums(tmp_path):
    """Test moving files with checksum verification."""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()

    (src / "file.txt").write_text("move me")

    success = move_files_with_checksums(src, dst, ["file.txt"])
    assert success
    assert (dst / "file.txt").exists()
    assert not (src / "file.txt").exists()
    assert (dst / "file.txt").read_text() == "move me"

def test_move_files_with_checksums_missing_source(tmp_path):
    """Test move fails gracefully if source is missing."""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()

    success = move_files_with_checksums(src, dst, ["missing.txt"])
    assert not success


def test_validate_project_structure(tmp_path):
    """Test project structure validation."""
    # Create valid structure
    (tmp_path / "src").mkdir()
    (tmp_path / "data").mkdir()

    is_valid, missing = validate_project_structure(tmp_path, ["src", "data"])
    assert is_valid
    assert len(missing) == 0

    # Test missing dir
    is_valid, missing = validate_project_structure(tmp_path, ["src", "tests"])
    assert not is_valid
    assert "tests" in missing


def test_get_data_stats(tmp_path):
    """Test data statistics gathering."""
    stats = get_data_stats(tmp_path)
    assert stats["exists"]
    assert stats["file_count"] == 0
    assert stats["total_size_bytes"] == 0

    # Add files
    (tmp_path / "f1.txt").write_text("a")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "f2.txt").write_text("bb")

    stats = get_data_stats(tmp_path)
    assert stats["file_count"] == 2
    assert stats["directory_count"] == 1
    assert stats["total_size_bytes"] == 3
