"""
Tests for checksum generation and verification functionality.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from checksum_generator import compute_file_checksum, generate_checksums, save_checksums
from data_loader import verify_checksum


class TestChecksumGeneration:
    """Test cases for checksum generation functions."""

    def test_compute_file_checksum(self, tmp_path: Path):
        """Test that checksum computation is deterministic and correct."""
        test_content = b"Hello, World! This is a test file."
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(test_content)

        checksum1 = compute_file_checksum(test_file)
        checksum2 = compute_file_checksum(test_file)

        # Checksums should be identical for the same file
        assert checksum1 == checksum2
        # Checksum should be a valid hex string of correct length
        assert len(checksum1) == 64
        assert all(c in '0123456789abcdef' for c in checksum1)

    def test_compute_file_checksum_empty(self, tmp_path: Path):
        """Test checksum computation for empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        checksum = compute_file_checksum(test_file)
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert checksum == expected

    def test_generate_checksums(self, tmp_path: Path):
        """Test checksum generation for multiple files."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")

        file2 = tmp_path / "file2.txt"
        file2.write_text("Content 2")

        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()
        file3 = sub_dir / "file3.txt"
        file3.write_text("Content 3")

        checksums = generate_checksums(tmp_path)

        assert checksums["total_files"] == 3
        assert "file1.txt" in checksums["file_checksums"]
        assert "file2.txt" in checksums["file_checksums"]
        assert "subdir/file3.txt" in checksums["file_checksums"]
        assert checksums["algorithm"] == "sha256"
        assert checksums["version"] == "1.0"

    def test_save_checksums(self, tmp_path: Path):
        """Test that checksums are saved correctly to JSON."""
        checksums_data = {
            "version": "1.0",
            "algorithm": "sha256",
            "total_files": 1,
            "file_checksums": {
                "test.txt": "abc123"
            },
            "generated_files": [
                {
                    "path": "test.txt",
                    "checksum": "abc123",
                    "size_bytes": 100
                }
            ]
        }

        output_path = tmp_path / "checksums.json"
        save_checksums(checksums_data, output_path)

        assert output_path.exists()
        with open(output_path, "r") as f:
            loaded = json.load(f)

        assert loaded == checksums_data

    def test_generate_checksums_nonexistent_directory(self):
        """Test that generating checksums for non-existent directory raises error."""
        with pytest.raises(FileNotFoundError):
            generate_checksums(Path("/nonexistent/directory"))

    def test_verify_checksum_integration(self, tmp_path: Path):
        """Integration test: generate checksums and verify them."""
        # Create a test file
        test_file = tmp_path / "verify_test.txt"
        test_content = b"This is test content for verification."
        test_file.write_bytes(test_content)

        # Generate checksum
        checksum = compute_file_checksum(test_file)

        # Create checksums file
        checksums_data = {
            "file_checksums": {
                "verify_test.txt": checksum
            }
        }
        checksums_file = tmp_path / "checksums.json"
        save_checksums(checksums_data, checksums_file)

        # Verify using the data_loader function
        is_valid = verify_checksum(str(test_file), str(checksums_file))
        assert is_valid is True

    def test_verify_checksum_invalid(self, tmp_path: Path):
        """Test verification with invalid checksum."""
        test_file = tmp_path / "invalid_test.txt"
        test_file.write_text("Content")

        # Create checksums file with wrong checksum
        checksums_data = {
            "file_checksums": {
                "invalid_test.txt": "wrongchecksum12345678901234567890123456789012345678901234567890"
            }
        }
        checksums_file = tmp_path / "checksums.json"
        save_checksums(checksums_data, checksums_file)

        is_valid = verify_checksum(str(test_file), str(checksums_file))
        assert is_valid is False