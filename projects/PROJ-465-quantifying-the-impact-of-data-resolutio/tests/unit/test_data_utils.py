"""
Unit tests for code/data/utils.py checksum utilities.
"""
import os
import tempfile
from pathlib import Path

import pytest

from code.data.utils import verify_checksum, generate_checksum_file


class TestVerifyChecksum:
    def test_verify_success(self, tmp_path):
        """Test successful verification of a known file."""
        test_file = tmp_path / "test_data.txt"
        test_content = b"Hello, GWOSC!"
        test_file.write_bytes(test_content)

        # Compute hash manually to simulate expected hash
        import hashlib
        expected_hash = hashlib.sha256(test_content).hexdigest()

        assert verify_checksum(test_file, expected_hash) is True

    def test_verify_mismatch(self, tmp_path):
        """Test verification failure when hash does not match."""
        test_file = tmp_path / "test_data.txt"
        test_file.write_bytes(b"Some data")

        wrong_hash = "a" * 64
        assert verify_checksum(test_file, wrong_hash) is False

    def test_verify_file_not_found(self, tmp_path):
        """Test verification returns False if file is missing."""
        non_existent = tmp_path / "missing.txt"
        assert verify_checksum(non_existent, "dummy_hash") is False

    def test_verify_case_insensitive(self, tmp_path):
        """Test that hash comparison is case-insensitive."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Data")

        import hashlib
        expected_hash = hashlib.sha256(b"Data").hexdigest()
        upper_hash = expected_hash.upper()

        assert verify_checksum(test_file, upper_hash) is True


class TestGenerateChecksumFile:
    def test_generate_creates_file(self, tmp_path):
        """Test that checksum file is created correctly."""
        test_file = tmp_path / "source.bin"
        test_file.write_bytes(b"Binary content")

        output_dir = tmp_path / "checksums"
        result_path = generate_checksum_file(test_file, output_dir)

        assert result_path.exists()
        assert result_path.name == "source.bin.sha256"

        content = result_path.read_text()
        assert f"{test_file.name}" in content

    def test_generate_creates_directory(self, tmp_path):
        """Test that output directory is created if missing."""
        test_file = tmp_path / "source.txt"
        test_file.write_bytes(b"Content")

        new_dir = tmp_path / "nested" / "dir"
        result_path = generate_checksum_file(test_file, new_dir)

        assert new_dir.exists()
        assert result_path.exists()

    def test_generate_missing_source(self, tmp_path):
        """Test that FileNotFoundError is raised if source is missing."""
        missing_file = tmp_path / "nonexistent.bin"
        with pytest.raises(FileNotFoundError):
            generate_checksum_file(missing_file, tmp_path)