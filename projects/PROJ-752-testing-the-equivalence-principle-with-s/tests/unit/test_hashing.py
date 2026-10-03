"""
Unit tests for hashing and versioning utilities.
Tests edge cases: missing data, empty results, invalid paths.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add code directory to path
code_dir = os.path.join(os.path.dirname(__file__), "..", "..", "code")
sys.path.insert(0, os.path.abspath(code_dir))

from utils.hashing import (
    compute_sha256,
    hash_artifact,
    update_state_file,
    verify_artifact_integrity,
    compute_file_metadata,
)
from utils.logging import DataUnavailableError


class TestComputeSha256:
    """Tests for compute_sha256 function."""

    def test_compute_sha256_valid_file(self, tmp_path):
        """Test hashing a valid file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        hash1 = compute_sha256(str(test_file))
        hash2 = compute_sha256(str(test_file))

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_compute_sha256_empty_file(self, tmp_path):
        """Test hashing an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        hash_val = compute_sha256(str(test_file))
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_val == expected

    def test_compute_sha256_nonexistent_file(self):
        """Test hashing a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/file.txt")

    def test_compute_sha256_binary_file(self, tmp_path):
        """Test hashing a binary file."""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b"\x00\x01\x02\x03\xff")

        hash_val = compute_sha256(str(test_file))
        assert len(hash_val) == 64


class TestHashArtifact:
    """Tests for hash_artifact function."""

    def test_hash_artifact_success(self, tmp_path):
        """Test successful artifact hashing."""
        test_file = tmp_path / "artifact.csv"
        test_file.write_text("col1,col2\n1,2\n3,4")

        result = hash_artifact(str(test_file))

        assert "sha256" in result
        assert "version" in result
        assert "size_bytes" in result
        assert "path" in result
        assert result["size_bytes"] > 0

    def test_hash_artifact_with_custom_version(self, tmp_path):
        """Test artifact hashing with custom version."""
        test_file = tmp_path / "artifact.json"
        test_file.write_text('{"key": "value"}')

        result = hash_artifact(str(test_file), version="v1.0.0")

        assert result["version"] == "v1.0.0"


class TestUpdateStateFile:
    """Tests for update_state_file function."""

    def test_update_state_file_creates_new(self, tmp_path):
        """Test updating a non-existent state file."""
        state_file = tmp_path / "state.json"
        artifact_path = "data/test.csv"
        artifact_hash = "abc123"

        update_state_file(str(state_file), artifact_path, artifact_hash)

        assert state_file.exists()
        with open(state_file, "r") as f:
            state = json.load(f)

        assert state["artifact_hashes"][artifact_path] == artifact_hash

    def test_update_state_file_updates_existing(self, tmp_path):
        """Test updating an existing state file."""
        state_file = tmp_path / "state.json"

        # Create initial state
        initial_state = {"artifact_hashes": {"old.csv": "oldhash"}, "versions": {}}
        with open(state_file, "w") as f:
            json.dump(initial_state, f)

        update_state_file(str(state_file), "new.csv", "newhash")

        with open(state_file, "r") as f:
            state = json.load(f)

        assert state["artifact_hashes"]["old.csv"] == "oldhash"
        assert state["artifact_hashes"]["new.csv"] == "newhash"

    def test_update_state_file_creates_directories(self, tmp_path):
        """Test that update_state_file creates necessary directories."""
        state_file = tmp_path / "deep" / "nested" / "state.json"

        update_state_file(str(state_file), "test.csv", "hash")

        assert state_file.exists()


class TestVerifyArtifactIntegrity:
    """Tests for verify_artifact_integrity function."""

    def test_verify_success(self, tmp_path):
        """Test successful verification."""
        test_file = tmp_path / "verify.txt"
        content = "Test content"
        test_file.write_text(content)

        expected_hash = compute_sha256(str(test_file))

        assert verify_artifact_integrity(str(test_file), expected_hash)

    def test_verify_hash_mismatch(self, tmp_path):
        """Test verification with mismatched hash."""
        test_file = tmp_path / "verify.txt"
        test_file.write_text("Test content")

        wrong_hash = "0" * 64

        assert not verify_artifact_integrity(str(test_file), wrong_hash)

    def test_verify_missing_file(self):
        """Test verification of non-existent file."""
        assert not verify_artifact_integrity("/nonexistent/file.txt", "abc123")


class TestComputeFileMetadata:
    """Tests for compute_file_metadata function."""

    def test_metadata_structure(self, tmp_path):
        """Test metadata structure."""
        test_file = tmp_path / "meta.txt"
        test_file.write_text("content")

        metadata = compute_file_metadata(str(test_file))

        assert "path" in metadata
        assert "size_bytes" in metadata
        assert "sha256" in metadata
        assert "modified_timestamp" in metadata
        assert "created_timestamp" in metadata
        assert metadata["size_bytes"] > 0
        assert len(metadata["sha256"]) == 64


class TestEdgeCases:
    """Tests for edge cases: missing data, empty results."""

    def test_empty_directory_scan(self, tmp_path):
        """Test handling of empty directory."""
        # Create empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Should not raise, just return empty
        from utils.hashing import scan_and_hash_artifacts

        state_file = tmp_path / "state.json"
        result = scan_and_hash_artifacts(str(empty_dir), ["*.csv"], str(state_file))

        assert result == {}

    def test_large_file_handling(self, tmp_path):
        """Test handling of large files (simulate with moderate size)."""
        test_file = tmp_path / "large.bin"
        # Write 1MB of data
        test_file.write_bytes(b"0" * (1024 * 1024))

        hash_val = compute_sha256(str(test_file))
        assert len(hash_val) == 64

    def test_unicode_filename(self, tmp_path):
        """Test handling of unicode filenames."""
        test_file = tmp_path / "文件_测试.txt"
        test_file.write_text("Unicode content")

        hash_val = compute_sha256(str(test_file))
        assert len(hash_val) == 64

    def test_special_characters_in_path(self, tmp_path):
        """Test handling of special characters in path."""
        test_file = tmp_path / "test-file_v1.0 (beta).txt"
        test_file.write_text("Content")

        hash_val = compute_sha256(str(test_file))
        assert len(hash_val) == 64