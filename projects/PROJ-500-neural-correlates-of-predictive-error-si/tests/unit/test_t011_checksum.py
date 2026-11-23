"""
Unit tests for T011: Checksum utility.
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
    generate_and_save_manifest
)


def test_compute_file_sha256():
    """Test SHA-256 computation for a known file content."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)

    try:
        # Known hash for "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        result = compute_file_sha256(temp_path)
        assert result == expected_hash
    finally:
        os.unlink(temp_path)


def test_compute_file_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_file_sha256(Path("/nonexistent/path/file.txt"))


def test_compute_directory_checksums():
    """Test directory checksum computation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        checksums = compute_directory_checksums(tmp_path)

        assert len(checksums) == 3
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums
        assert "subdir/file3.txt" in checksums


def test_compute_directory_checksums_with_extension_filter():
    """Test directory checksum computation with extension filter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.csv").write_text("col1,col2\n1,2")
        (tmp_path / "file3.md").write_text("# Header")

        checksums = compute_directory_checksums(tmp_path, extension_filter=[".csv"])

        assert len(checksums) == 1
        assert "file2.csv" in checksums
        assert "file1.txt" not in checksums
        assert "file3.md" not in checksums


def test_save_and_load_checksum_manifest():
    """Test saving and loading a checksum manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        checksums = {"file1.txt": "abc123", "file2.txt": "def456"}
        manifest_path = tmp_path / "manifest.json"

        save_checksum_manifest(checksums, manifest_path)
        assert manifest_path.exists()

        loaded = load_checksum_manifest(manifest_path)
        assert loaded == checksums


def test_verify_checksums_success():
    """Test successful checksum verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "file1.txt").write_text("content1")

        # Generate manifest
        manifest_path = tmp_path / "manifest.json"
        generate_and_save_manifest(tmp_path, manifest_path)

        # Verify
        assert verify_checksums(tmp_path, manifest_path) is True


def test_verify_checksums_failure():
    """Test checksum verification failure when file changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        file_path = tmp_path / "file1.txt"
        file_path.write_text("original content")

        # Generate manifest
        manifest_path = tmp_path / "manifest.json"
        generate_and_save_manifest(tmp_path, manifest_path)

        # Modify file
        file_path.write_text("modified content")

        # Verify should fail
        assert verify_checksums(tmp_path, manifest_path) is False


def test_verify_checksums_missing_file():
    """Test checksum verification failure when file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        file_path = tmp_path / "file1.txt"
        file_path.write_text("content1")

        # Generate manifest
        manifest_path = tmp_path / "manifest.json"
        generate_and_save_manifest(tmp_path, manifest_path)

        # Delete file
        file_path.unlink()

        # Verify should fail
        assert verify_checksums(tmp_path, manifest_path) is False


def test_generate_and_save_manifest():
    """Test manifest generation and saving."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "file1.txt").write_text("content1")

        manifest_path = tmp_path / "manifest.json"
        result = generate_and_save_manifest(tmp_path, manifest_path)

        assert manifest_path.exists()
        assert len(result) == 1
        assert "file1.txt" in result
