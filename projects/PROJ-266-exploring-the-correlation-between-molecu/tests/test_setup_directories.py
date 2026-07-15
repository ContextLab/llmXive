"""
Unit tests for the directory setup and checksum utility.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the functions to test
from code.data.setup_directories import (
    create_directories,
    compute_file_checksum,
    generate_checksum_manifest,
)


class TestCreateDirectories:
    def test_creates_required_structure(self, tmp_path):
        """Test that the required directories are created."""
        # Mock get_project_root to return our temp directory
        with patch("code.data.setup_directories.get_project_root", return_value=tmp_path):
            dirs = create_directories()

        assert "raw" in dirs
        assert "processed" in dirs
        assert "figures" in dirs

        assert dirs["raw"].exists()
        assert dirs["processed"].exists()
        assert dirs["figures"].exists()

        assert dirs["raw"].is_dir()
        assert dirs["processed"].is_dir()
        assert dirs["figures"].is_dir()

    def test_does_not_fail_if_exists(self, tmp_path):
        """Test that the function does not fail if directories already exist."""
        # Pre-create the directories
        (tmp_path / "data" / "raw").mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)
        (tmp_path / "data" / "figures").mkdir(parents=True)

        with patch("code.data.setup_directories.get_project_root", return_value=tmp_path):
            # Should not raise
            dirs = create_directories()

        assert dirs["raw"].exists()


class TestComputeFileChecksum:
    def test_sha256_checksum(self, tmp_path):
        """Test SHA-256 checksum computation."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        checksum = compute_file_checksum(test_file)

        # Expected SHA-256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

    def test_nonexistent_file_raises(self, tmp_path):
        """Test that FileNotFoundError is raised for missing files."""
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(non_existent)

    def test_large_file_chunked_reading(self, tmp_path):
        """Test that large files are read in chunks without memory issues."""
        # Create a 1MB file
        large_content = b"x" * (1024 * 1024)
        test_file = tmp_path / "large.bin"
        test_file.write_bytes(large_content)

        # Should not raise
        checksum = compute_file_checksum(test_file)
        assert len(checksum) == 64  # SHA-256 hex length


class TestGenerateChecksumManifest:
    def test_generates_manifest(self, tmp_path):
        """Test manifest generation for a directory with files."""
        # Create some test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        manifest = generate_checksum_manifest(tmp_path)

        assert len(manifest) == 3
        assert "file1.txt" in manifest
        assert "file2.txt" in manifest
        assert "subdir/file3.txt" in manifest

    def test_writes_json_manifest(self, tmp_path):
        """Test that the manifest is written to a JSON file."""
        (tmp_path / "test.txt").write_text("data")
        output_path = tmp_path / "manifest.json"

        generate_checksum_manifest(tmp_path, output_path=output_path)

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)

        assert "test.txt" in data

    def test_empty_directory(self, tmp_path):
        """Test manifest generation for an empty directory."""
        manifest = generate_checksum_manifest(tmp_path)
        assert manifest == {}

    def test_nonexistent_directory_raises(self, tmp_path):
        """Test that FileNotFoundError is raised for missing directories."""
        with pytest.raises(FileNotFoundError):
            generate_checksum_manifest(tmp_path / "nonexistent")
