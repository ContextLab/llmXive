import hashlib
import json
import os
import tempfile
from pathlib import Path

import pytest

from code_05_compute_checksums import compute_sha256, load_existing_checksums, save_checksums
from config import get_data_dir, get_raw_data_dir


class TestChecksumComputation:
    """Tests for checksum computation functionality."""

    def test_compute_sha256(self, tmp_path):
        """Test SHA-256 computation on a known file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash
        assert len(actual_hash) == 64  # SHA-256 produces 64 hex characters

    def test_compute_sha256_empty_file(self, tmp_path):
        """Test SHA-256 computation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash

    def test_load_existing_checksums_nonexistent(self, tmp_path):
        """Test loading checksums from a non-existent file returns empty dict."""
        checksums_path = tmp_path / "nonexistent.json"
        checksums = load_existing_checksums(checksums_path)
        assert checksums == {}

    def test_load_existing_checksums_valid(self, tmp_path):
        """Test loading valid checksums from a JSON file."""
        checksums_path = tmp_path / "checksums.json"
        test_checksums = {"file1.csv": "abc123", "file2.csv": "def456"}
        with open(checksums_path, "w") as f:
            json.dump(test_checksums, f)

        loaded_checksums = load_existing_checksums(checksums_path)
        assert loaded_checksums == test_checksums

    def test_save_and_load_checksums(self, tmp_path):
        """Test saving and loading checksums."""
        checksums_path = tmp_path / "checksums.json"
        test_checksums = {"file1.csv": "abc123", "file2.csv": "def456"}

        save_checksums(checksums_path, test_checksums)
        loaded_checksums = load_existing_checksums(checksums_path)

        assert loaded_checksums == test_checksums

    def test_checksum_entry_for_real_ratings(self):
        """Test that real_ratings.csv checksum can be computed if file exists."""
        raw_data_dir = get_raw_data_dir()
        target_file = raw_data_dir / "real_ratings.csv"

        if target_file.exists():
            checksum = compute_sha256(target_file)
            assert len(checksum) == 64
            assert all(c in '0123456789abcdef' for c in checksum)
        else:
            pytest.skip("real_ratings.csv not found, skipping integration test")
