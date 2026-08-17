"""
Unit tests for checksum_raw.py functionality.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.checksum_raw import compute_file_sha256, find_raw_matrices, checksum_raw_matrices


class TestComputeFileSha256:
    """Tests for compute_file_sha256 function."""

    def test_compute_sha256_simple(self, tmp_path):
        """Test SHA-256 computation on a simple file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        checksum = compute_file_sha256(test_file)

        # Known SHA-256 hash for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

    def test_compute_sha256_numpy_file(self, tmp_path):
        """Test SHA-256 computation on a NumPy .npy file."""
        test_file = tmp_path / "test.npy"
        test_array = np.array([1, 2, 3, 4, 5])
        np.save(test_file, test_array)

        checksum = compute_file_sha256(test_file)

        # Should be a valid 64-character hex string
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_compute_sha256_large_file(self, tmp_path):
        """Test SHA-256 computation on a larger file."""
        test_file = tmp_path / "large.npy"
        test_array = np.random.rand(1000, 1000)
        np.save(test_file, test_array)

        checksum = compute_file_sha256(test_file)

        # Should be a valid 64-character hex string
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)


class TestFindRawMatrices:
    """Tests for find_raw_matrices function."""

    def test_find_no_files(self, tmp_path):
        """Test finding files in empty directory."""
        matrices = find_raw_matrices(tmp_path)
        assert matrices == []

    def test_find_correct_files(self, tmp_path):
        """Test finding only matrix files."""
        # Create some test files
        (tmp_path / "matrix_N100_seed1.npy").touch()
        (tmp_path / "matrix_N200_seed2.npy").touch()
        (tmp_path / "not_a_matrix.txt").touch()
        (tmp_path / "matrix_N300_seed3.npy").touch()

        matrices = find_raw_matrices(tmp_path)
        filenames = [f.name for f in matrices]

        assert len(matrices) == 3
        assert "matrix_N100_seed1.npy" in filenames
        assert "matrix_N200_seed2.npy" in filenames
        assert "matrix_N300_seed3.npy" in filenames
        assert "not_a_matrix.txt" not in filenames

    def test_find_nonexistent_directory(self, tmp_path):
        """Test finding files in non-existent directory."""
        nonexistent = tmp_path / "does_not_exist"
        matrices = find_raw_matrices(nonexistent)
        assert matrices == []


class TestChecksumRawMatrices:
    """Tests for checksum_raw_matrices function."""

    def test_checksum_creates_output(self, tmp_path):
        """Test that checksumming creates the output file."""
        raw_dir = tmp_path / "raw"
        state_dir = tmp_path / "state"
        raw_dir.mkdir()

        # Create a test matrix file
        test_file = raw_dir / "matrix_N100_seed1.npy"
        np.save(test_file, np.random.rand(10, 10))

        result = checksum_raw_matrices(raw_dir, state_dir)

        output_file = state_dir / "checksums_raw.json"
        assert output_file.exists()
        assert result["total_files"] == 1
        assert result["status"] == "success"

    def test_checksum_output_structure(self, tmp_path):
        """Test the structure of the checksum output."""
        raw_dir = tmp_path / "raw"
        state_dir = tmp_path / "state"
        raw_dir.mkdir()

        # Create test matrix files
        test_file1 = raw_dir / "matrix_N100_seed1.npy"
        np.save(test_file1, np.random.rand(10, 10))

        test_file2 = raw_dir / "matrix_N200_seed2.npy"
        np.save(test_file2, np.random.rand(20, 20))

        result = checksum_raw_matrices(raw_dir, state_dir)

        # Verify output file exists and can be loaded
        output_file = state_dir / "checksums_raw.json"
        with open(output_file) as f:
            loaded = json.load(f)

        assert "files" in loaded
        assert "total_files" in loaded
        assert "status" in loaded
        assert "checksum_algorithm" in loaded
        assert loaded["total_files"] == 2
        assert loaded["status"] == "success"
        assert loaded["checksum_algorithm"] == "SHA-256"

    def test_checksum_no_files(self, tmp_path):
        """Test checksumming when no files exist."""
        raw_dir = tmp_path / "raw"
        state_dir = tmp_path / "state"
        raw_dir.mkdir()

        result = checksum_raw_matrices(raw_dir, state_dir)

        assert result["total_files"] == 0
        assert result["status"] == "no_files"
