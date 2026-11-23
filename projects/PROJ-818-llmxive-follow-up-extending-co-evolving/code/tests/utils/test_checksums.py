"""
Unit tests for the checksum utility.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code to path if running standalone
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.checksums import (
    ChecksumError,
    compute_file_sha256,
    load_checksums,
    save_checksums,
    update_checksum_for_file,
    verify_file_integrity
)


class TestChecksums:
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary directory for test artifacts."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return str(data_dir)

    @pytest.fixture
    def test_file(self, temp_data_dir):
        """Create a temporary test file."""
        file_path = Path(temp_data_dir) / "test_file.txt"
        file_path.write_text("Hello, World!")
        return str(file_path)

    @pytest.fixture
    def checksum_file(self, temp_data_dir):
        """Path to a temporary checksum file."""
        return str(Path(temp_data_dir) / "checksums.json")

    def test_compute_file_sha256(self, test_file):
        """Test that compute_file_sha256 returns a valid hash."""
        hash_val = compute_file_sha256(test_file)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_compute_file_sha256_not_found(self, temp_data_dir):
        """Test that compute_file_sha256 raises error for missing file."""
        with pytest.raises(ChecksumError, match="File not found"):
            compute_file_sha256(str(Path(temp_data_dir) / "nonexistent.txt"))

    def test_load_checksums_empty(self, temp_data_dir):
        """Test loading checksums from a non-existent file."""
        checksum_path = str(Path(temp_data_dir) / "nonexistent.json")
        data = load_checksums(checksum_path)
        assert "files" in data
        assert "metadata" in data
        assert data["files"] == {}

    def test_load_checksums_with_data(self, temp_data_dir, checksum_file):
        """Test loading checksums from an existing file."""
        initial_data = {
            "files": {"test.txt": {"hash": "abc123", "updated_at": "2023-01-01"}},
            "metadata": {"last_updated": "2023-01-01"}
        }
        with open(checksum_file, "w") as f:
            json.dump(initial_data, f)

        loaded = load_checksums(checksum_file)
        assert loaded["files"]["test.txt"]["hash"] == "abc123"

    def test_save_checksums(self, temp_data_dir, checksum_file):
        """Test saving checksums to a file."""
        data = {
            "files": {"test.txt": {"hash": "def456", "updated_at": "2023-01-02"}},
            "metadata": {"last_updated": None}
        }
        save_checksums(data, checksum_file)

        assert os.path.exists(checksum_file)
        with open(checksum_file, "r") as f:
            loaded = json.load(f)
        assert loaded["files"]["test.txt"]["hash"] == "def456"
        assert loaded["metadata"]["last_updated"] is not None

    def test_update_checksum_for_file(self, test_file, checksum_file):
        """Test updating a file's checksum in the database."""
        hash_val = update_checksum_for_file(test_file, checksum_file)

        # Verify the returned hash matches the computed one
        assert hash_val == compute_file_sha256(test_file)

        # Verify it was saved
        checksums = load_checksums(checksum_file)
        # The key might be relative or absolute depending on implementation,
        # but the file should be in the dict.
        keys = list(checksums["files"].keys())
        assert any("test_file.txt" in k for k in keys)

    def test_verify_file_integrity_success(self, test_file, checksum_file):
        """Test successful integrity verification."""
        update_checksum_for_file(test_file, checksum_file)
        assert verify_file_integrity(test_file, checksum_file) is True

    def test_verify_file_integrity_failure(self, test_file, checksum_file):
        """Test integrity verification failure after file modification."""
        update_checksum_for_file(test_file, checksum_file)

        # Modify the file
        Path(test_file).write_text("Modified content")

        assert verify_file_integrity(test_file, checksum_file) is False

    def test_verify_file_integrity_not_registered(self, test_file, checksum_file):
        """Test verification fails if file is not registered."""
        # Don't update checksum first
        with pytest.raises(ChecksumError, match="not registered"):
            verify_file_integrity(test_file, checksum_file)