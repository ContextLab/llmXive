"""
Unit tests for checksum utility (T011).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from src.utils.checksum import (
    compute_file_sha256,
    compute_directory_checksums,
    save_checksum_manifest,
    load_checksum_manifest,
    verify_checksums,
    generate_and_save_manifest,
)


def test_compute_file_sha256():
    """Test SHA-256 computation on a known file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, World!")
        temp_path = f.name

    try:
        # Known SHA-256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        result = compute_file_sha256(temp_path)
        assert result == expected
    finally:
        os.unlink(temp_path)


def test_compute_file_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_file_sha256("/nonexistent/path/file.txt")


def test_compute_directory_checksums():
    """Test checksum computation for a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        Path(tmpdir, "file1.txt").write_text("test1")
        Path(tmpdir, "file2.txt").write_text("test2")
        Path(tmpdir, "subdir").mkdir()
        Path(tmpdir, "subdir", "file3.txt").write_text("test3")

        checksums = compute_directory_checksums(tmpdir)

        assert len(checksums) == 3
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums
        assert "subdir/file3.txt" in checksums or "subdir\\file3.txt" in checksums


def test_compute_directory_checksums_with_extension_filter():
    """Test checksum computation with extension filter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file1.txt").write_text("test1")
        Path(tmpdir, "file2.csv").write_text("test2")

        checksums = compute_directory_checksums(tmpdir, extensions=[".csv"])

        assert len(checksums) == 1
        assert "file2.csv" in checksums


def test_save_and_load_checksum_manifest():
    """Test saving and loading a checksum manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir, "manifest.json")
        test_checksums = {"file1.txt": "abc123", "file2.txt": "def456"}

        save_checksum_manifest(test_checksums, str(manifest_path))

        assert manifest_path.exists()

        loaded = load_checksum_manifest(str(manifest_path))

        assert loaded == test_checksums


def test_verify_checksums_success():
    """Test successful checksum verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file
        test_file = Path(tmpdir, "test.txt")
        test_file.write_text("verification test")

        # Generate manifest
        generate_and_save_manifest(tmpdir, str(Path(tmpdir, "manifest.json")))

        # Verify
        results = verify_checksums(tmpdir, str(Path(tmpdir, "manifest.json")))

        assert "test.txt" in results
        assert results["test.txt"] is True


def test_verify_checksums_failure():
    """Test checksum verification with corrupted file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file
        test_file = Path(tmpdir, "test.txt")
        test_file.write_text("original content")

        # Generate manifest
        generate_and_save_manifest(tmpdir, str(Path(tmpdir, "manifest.json")))

        # Corrupt the file
        test_file.write_text("corrupted content")

        # Verify
        results = verify_checksums(tmpdir, str(Path(tmpdir, "manifest.json")))

        assert "test.txt" in results
        assert results["test.txt"] is False


def test_verify_checksums_missing_file():
    """Test checksum verification when file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create manifest with a file that doesn't exist
        manifest_path = Path(tmpdir, "manifest.json")
        save_checksum_manifest({"missing.txt": "fakehash"}, str(manifest_path))

        results = verify_checksums(tmpdir, str(manifest_path))

        assert "missing.txt" in results
        assert results["missing.txt"] is False


def test_generate_and_save_manifest():
    """Test the combined generate and save function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "data.txt").write_text("data content")
        output_path = Path(tmpdir, "output_manifest.json")

        checksums = generate_and_save_manifest(tmpdir, str(output_path))

        assert "data.txt" in checksums
        assert output_path.exists()

        # Verify the saved manifest
        loaded = load_checksum_manifest(str(output_path))
        assert loaded == {"version": "1.0", "algorithm": "sha256", "checksums": checksums}
