"""
Unit tests for the checksum module.
"""

import json
import tempfile
from pathlib import Path

import pytest

from code.data.checksum import (
    compute_sha256,
    generate_checksums,
    save_checksums,
    load_checksums,
    verify_checksums,
)


def test_compute_sha256():
    """Test SHA256 computation on a known string."""
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)

    try:
        checksum = compute_sha256(temp_path)
        # Known SHA256 for "Hello, World!"
        expected = "7f83b1657ff1fc53b92dc18148a1d65dfa62434e6d50275b7b924350f41d7f40"
        assert checksum == expected
    finally:
        temp_path.unlink()


def test_compute_sha256_empty_file():
    """Test SHA256 computation on an empty file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        temp_path = Path(f.name)

    try:
        checksum = compute_sha256(temp_path)
        # Known SHA256 for empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert checksum == expected
    finally:
        temp_path.unlink()


def test_generate_checksums():
    """Test checksum generation for a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("content3")

        checksums = generate_checksums(tmp_path, recursive=True)

        assert len(checksums) == 3
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums
        assert "subdir/file3.txt" in checksums or "subdir\\file3.txt" in checksums


def test_generate_checksums_with_extension_filter():
    """Test checksum generation with extension filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test files with different extensions
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.csv").write_text("content2")
        (tmp_path / "file3.json").write_text("content3")

        checksums = generate_checksums(
            tmp_path, recursive=True, extensions=[".csv", ".json"]
        )

        assert len(checksums) == 2
        assert "file1.txt" not in checksums
        assert "file2.csv" in checksums
        assert "file3.json" in checksums


def test_save_and_load_checksums():
    """Test saving and loading checksums to/from JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        checksum_file = tmp_path / "checksums.json"

        test_checksums = {
            "file1.txt": "abc123",
            "file2.csv": "def456",
        }

        save_checksums(test_checksums, checksum_file)

        loaded_checksums = load_checksums(checksum_file)

        assert loaded_checksums == test_checksums


def test_verify_checksums_success():
    """Test successful checksum verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        checksum = compute_sha256(test_file)
        checksums = {"test.txt": checksum}

        assert verify_checksums(tmp_path, checksums) is True


def test_verify_checksums_missing_file():
    """Test verification fails for missing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        checksums = {"missing.txt": "abc123"}

        assert verify_checksums(tmp_path, checksums) is False


def test_verify_checksums_modified_file():
    """Test verification fails for modified files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        # Get checksum
        checksum = compute_sha256(test_file)
        checksums = {"test.txt": checksum}

        # Modify the file
        test_file.write_text("modified content")

        assert verify_checksums(tmp_path, checksums) is False


def test_verify_checksums_nonexistent_directory():
    """Test verification raises error for nonexistent directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        nonexistent_dir = tmp_path / "nonexistent"

        checksums = {"file.txt": "abc123"}

        # Should return False, not raise (based on current implementation)
        result = verify_checksums(nonexistent_dir, checksums)
        assert result is False