"""
Unit tests for the checksum generation module.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from checksum_generator import compute_file_checksum, generate_checksums, save_checksums


class TestComputeFileChecksum:
    def test_compute_sha256(self, tmp_path):
        """Test SHA256 checksum computation."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        checksum = compute_file_checksum(test_file)

        # Known SHA256 for "Hello, World!"
        expected = "d9014c4624844aa5bac314773d6b689ad467fa4e1d1a50a1b8a99d5a95f72ff5"
        assert checksum == expected

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent file."""
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(non_existent)

    def test_different_algorithms(self, tmp_path):
        """Test different hash algorithms."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test")

        sha256_checksum = compute_file_checksum(test_file, "sha256")
        md5_checksum = compute_file_checksum(test_file, "md5")

        # Check that different algorithms produce different results
        assert sha256_checksum != md5_checksum
        assert len(sha256_checksum) == 64  # SHA256 hex length
        assert len(md5_checksum) == 32    # MD5 hex length


class TestGenerateChecksums:
    def test_generate_multiple_files(self, tmp_path):
        """Test generating checksums for multiple files."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")

        checksums = generate_checksums(tmp_path)

        assert len(checksums) == 2
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums
        assert checksums["file1.txt"] != checksums["file2.txt"]

    def test_empty_directory(self, tmp_path):
        """Test generating checksums for an empty directory."""
        checksums = generate_checksums(tmp_path)
        assert checksums == {}

    def test_subdirectories_ignored(self, tmp_path):
        """Test that subdirectories are ignored."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file1 = tmp_path / "file1.txt"
        file1.write_bytes(b"content")

        checksums = generate_checksums(tmp_path)

        assert len(checksums) == 1
        assert "file1.txt" in checksums
        assert "subdir" not in checksums


class TestSaveChecksums:
    def test_save_and_load(self, tmp_path):
        """Test saving and loading checksums."""
        checksums = {
            "file1.txt": "abc123",
            "file2.txt": "def456"
        }

        output_path = tmp_path / "checksums.json"
        save_checksums(checksums, output_path)

        # Verify file exists and content is correct
        assert output_path.exists()
        with open(output_path, "r") as f:
            loaded = json.load(f)

        assert loaded == checksums

    def test_creates_parent_directories(self, tmp_path):
        """Test that save_checksums creates parent directories."""
        output_path = tmp_path / "nested" / "dir" / "checksums.json"
        save_checksums({}, output_path)

        assert output_path.exists()