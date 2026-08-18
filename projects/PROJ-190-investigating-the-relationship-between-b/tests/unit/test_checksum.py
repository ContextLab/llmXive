import os
import json
import tempfile
from pathlib import Path
import pytest

from code.utils.checksum import (
    compute_file_sha256,
    compute_directory_checksums,
    verify_checksum,
    save_checksums,
    load_checksums,
    verify_directory_against_checksums,
)


def test_compute_file_sha256():
    """Test SHA-256 computation on a simple file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Hello, World!")
        temp_path = f.name

    try:
        checksum = compute_file_sha256(temp_path)
        # Known SHA-256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_compute_file_sha256_nonexistent():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_file_sha256("/nonexistent/path/file.txt")

def test_compute_directory_checksums():
    """Test directory checksumming."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        file1 = Path(tmpdir) / "file1.txt"
        file1.write_text("Test content 1")

        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        file2 = subdir / "file2.txt"
        file2.write_text("Test content 2")

        checksums = compute_directory_checksums(tmpdir)

        assert len(checksums) == 2
        assert "file1.txt" in checksums
        assert "subdir/file2.txt" in checksums or "subdir\\file2.txt" in checksums

def test_save_and_load_checksums():
    """Test saving and loading checksums from JSON."""
    test_checksums = {
        "file1.txt": "abc123",
        "file2.txt": "def456",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "checksums.json"
        save_checksums(test_checksums, output_path)

        loaded = load_checksums(output_path)
        assert loaded == test_checksums

def test_verify_checksum_match():
    """Test successful checksum verification."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Verify me")
        temp_path = f.name

    try:
        checksum = compute_file_sha256(temp_path)
        assert verify_checksum(temp_path, checksum) is True
    finally:
        os.unlink(temp_path)

def test_verify_checksum_mismatch():
    """Test failed checksum verification."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Verify me")
        temp_path = f.name

    try:
        assert verify_checksum(temp_path, "wrong_checksum") is False
    finally:
        os.unlink(temp_path)

def test_verify_directory_against_checksums():
    """Test full directory verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        file1 = dir_path / "data.txt"
        file1.write_text("Data for verification")

        # Create checksums
        checksums = compute_directory_checksums(dir_path)
        checksum_file = Path(tmpdir) / "checksums.json"
        save_checksums(checksums, checksum_file)

        # Verify
        assert verify_directory_against_checksums(dir_path, checksum_file) is True

        # Corrupt a file
        file1.write_text("Corrupted data")
        assert verify_directory_against_checksums(dir_path, checksum_file) is False
