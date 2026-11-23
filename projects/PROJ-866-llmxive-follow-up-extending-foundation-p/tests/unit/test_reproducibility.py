"""
Unit tests for reproducibility checking functionality.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from utils.reproducibility_checker import (
    compute_file_hash,
    compute_directory_hashes,
    compare_hashes,
    run_pipeline_run
)


class TestComputeFileHash:
    """Tests for compute_file_hash function."""

    def test_compute_hash_existing_file(self, tmp_path):
        """Test hashing an existing file."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        hash_result = compute_file_hash(test_file)
        
        assert hash_result is not None
        assert len(hash_result) == 64  # SHA-256 hex length
        assert isinstance(hash_result, str)

    def test_compute_hash_nonexistent_file(self, tmp_path):
        """Test hashing a non-existent file."""
        nonexistent = tmp_path / "does_not_exist.txt"
        
        hash_result = compute_file_hash(nonexistent)
        
        assert hash_result is None

    def test_compute_hash_empty_file(self, tmp_path):
        """Test hashing an empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        
        hash_result = compute_file_hash(empty_file)
        
        assert hash_result is not None
        # SHA-256 of empty string
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_result == expected_hash


class TestComputeDirectoryHashes:
    """Tests for compute_directory_hashes function."""

    def test_compute_dir_hashes_single_file(self, tmp_path):
        """Test hashing a directory with a single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        hashes = compute_directory_hashes(tmp_path)
        
        assert len(hashes) == 1
        assert "test.txt" in hashes
        assert hashes["test.txt"] is not None

    def test_compute_dir_hashes_nested_files(self, tmp_path):
        """Test hashing a directory with nested files."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        file1 = tmp_path / "file1.txt"
        file2 = subdir / "file2.txt"
        
        file1.write_text("content1")
        file2.write_text("content2")
        
        hashes = compute_directory_hashes(tmp_path)
        
        assert len(hashes) == 2
        assert "file1.txt" in hashes
        assert "subdir/file2.txt" in hashes

    def test_compute_dir_hashes_empty_directory(self, tmp_path):
        """Test hashing an empty directory."""
        hashes = compute_directory_hashes(tmp_path)
        
        assert len(hashes) == 0

    def test_compute_dir_hashes_nonexistent_directory(self):
        """Test hashing a non-existent directory."""
        hashes = compute_directory_hashes(Path("/nonexistent/path"))
        
        assert len(hashes) == 0


class TestCompareHashes:
    """Tests for compare_hashes function."""

    def test_identical_hashes(self):
        """Test comparing identical hashes."""
        hashes1 = {
            "file1.txt": "abc123",
            "file2.txt": "def456"
        }
        hashes2 = {
            "file1.txt": "abc123",
            "file2.txt": "def456"
        }
        
        is_identical, missing, different = compare_hashes(hashes1, hashes2)
        
        assert is_identical is True
        assert len(missing) == 0
        assert len(different) == 0

    def test_different_hashes(self):
        """Test comparing different hashes."""
        hashes1 = {
            "file1.txt": "abc123",
            "file2.txt": "def456"
        }
        hashes2 = {
            "file1.txt": "xyz789",  # Different
            "file2.txt": "def456"
        }
        
        is_identical, missing, different = compare_hashes(hashes1, hashes2)
        
        assert is_identical is False
        assert len(missing) == 0
        assert len(different) == 1
        assert "file1.txt" in different[0]

    def test_missing_in_run2(self):
        """Test comparing when files are missing in run 2."""
        hashes1 = {
            "file1.txt": "abc123",
            "file2.txt": "def456"
        }
        hashes2 = {
            "file1.txt": "abc123"
            # file2.txt missing
        }
        
        is_identical, missing, different = compare_hashes(hashes1, hashes2)
        
        assert is_identical is False
        assert len(missing) == 1
        assert "file2.txt" in missing[0]
        assert len(different) == 0

    def test_missing_in_run1(self):
        """Test comparing when files are missing in run 1."""
        hashes1 = {
            "file1.txt": "abc123"
        }
        hashes2 = {
            "file1.txt": "abc123",
            "file2.txt": "def456"
        }
        
        is_identical, missing, different = compare_hashes(hashes1, hashes2)
        
        assert is_identical is False
        assert len(missing) == 1
        assert "file2.txt" in missing[0]
        assert len(different) == 0

    def test_both_missing(self):
        """Test comparing when files are missing in both runs."""
        hashes1 = {
            "file1.txt": "abc123"
        }
        hashes2 = {
            "file1.txt": "abc123"
        }
        
        is_identical, missing, different = compare_hashes(hashes1, hashes2)
        
        assert is_identical is True
        assert len(missing) == 0
        assert len(different) == 0