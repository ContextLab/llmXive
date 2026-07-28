"""
Unit tests for checksum utilities.
"""
import hashlib
import tempfile
from pathlib import Path

import pytest

from utils.checksum import (
    compute_file_sha256,
    compute_directory_checksums,
    verify_checksum,
    save_checksums,
    load_checksums,
    verify_directory_against_checksums,
)


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file with known content."""
    file_path = tmp_path / "test_file.txt"
    content = b"Hello, World! This is a test."
    file_path.write_bytes(content)
    return file_path, content


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory with multiple files."""
    # Create subdirectory
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    # Create files
    file1 = tmp_path / "file1.txt"
    file1.write_bytes(b"Content of file 1")

    file2 = tmp_path / "file2.csv"
    file2.write_bytes(b"a,b,c\n1,2,3")

    file3 = subdir / "file3.txt"
    file3.write_bytes(b"Content of file 3")

    return tmp_path


def test_compute_file_sha256(temp_file):
    """Test SHA-256 computation for a single file."""
    file_path, content = temp_file
    expected_hash = hashlib.sha256(content).hexdigest()

    actual_hash = compute_file_sha256(file_path)

    assert actual_hash == expected_hash
    assert len(actual_hash) == 64  # SHA-256 hex length


def test_compute_file_sha256_nonexistent():
    """Test that FileNotFoundError is raised for non-existent files."""
    with pytest.raises(FileNotFoundError):
        compute_file_sha256("/nonexistent/path/file.txt")


def test_verify_checksum_match(temp_file):
    """Test checksum verification when values match."""
    file_path, content = temp_file
    expected_hash = hashlib.sha256(content).hexdigest()

    assert verify_checksum(file_path, expected_hash) is True


def test_verify_checksum_mismatch(temp_file):
    """Test checksum verification when values don't match."""
    file_path, _ = temp_file
    wrong_hash = "a" * 64

    assert verify_checksum(file_path, wrong_hash) is False


def test_compute_directory_checksums(temp_dir):
    """Test checksum computation for a directory."""
    checksums = compute_directory_checksums(temp_dir, recursive=True)

    assert len(checksums) == 3
    assert "file1.txt" in checksums
    assert "file2.csv" in checksums
    assert "subdir/file3.txt" in checksums


def test_compute_directory_checksums_non_recursive(temp_dir):
    """Test checksum computation without recursion."""
    checksums = compute_directory_checksums(temp_dir, recursive=False)

    assert len(checksums) == 2
    assert "file1.txt" in checksums
    assert "file2.csv" in checksums
    assert "subdir" not in str(checksums.keys())


def test_compute_directory_checksums_with_extension_filter(temp_dir):
    """Test checksum computation with extension filter."""
    checksums = compute_directory_checksums(temp_dir, recursive=True, extensions=[".csv"])

    assert len(checksums) == 1
    assert "file2.csv" in checksums


def test_save_and_load_checksums(temp_dir):
    """Test saving and loading checksums to/from file."""
    checksums = compute_directory_checksums(temp_dir, recursive=True)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        checksum_path = f.name

    try:
        save_checksums(checksums, checksum_path)
        loaded_checksums = load_checksums(checksum_path)

        assert loaded_checksums == checksums
    finally:
        Path(checksum_path).unlink()


def test_verify_directory_against_checksums(temp_dir):
    """Test directory verification against stored checksums."""
    checksums = compute_directory_checksums(temp_dir, recursive=True)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        checksum_path = f.name

    try:
        save_checksums(checksums, checksum_path)
        result = verify_directory_against_checksums(temp_dir, checksum_path)
        assert result is True
    finally:
        Path(checksum_path).unlink()


def test_verify_directory_with_missing_file(temp_dir):
    """Test directory verification when a file is missing."""
    checksums = compute_directory_checksums(temp_dir, recursive=True)

    # Remove a file
    file_to_remove = temp_dir / "file1.txt"
    file_to_remove.unlink()

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        checksum_path = f.name

    try:
        save_checksums(checksums, checksum_path)
        result = verify_directory_against_checksums(temp_dir, checksum_path)
        assert result is False
    finally:
        Path(checksum_path).unlink()


def test_verify_directory_with_corrupted_file(temp_dir):
    """Test directory verification when a file is corrupted."""
    checksums = compute_directory_checksums(temp_dir, recursive=True)

    # Corrupt a file
    file_to_corrupt = temp_dir / "file1.txt"
    file_to_corrupt.write_bytes(b"Corrupted content")

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        checksum_path = f.name

    try:
        save_checksums(checksums, checksum_path)
        result = verify_directory_against_checksums(temp_dir, checksum_path)
        assert result is False
    finally:
        Path(checksum_path).unlink()
