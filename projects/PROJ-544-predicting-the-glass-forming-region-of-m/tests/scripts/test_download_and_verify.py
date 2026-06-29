"""
Tests for download_and_verify.py script.

These tests verify the core functionality without requiring
actual network access for all test cases.
"""
import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.download_and_verify import (
    compute_sha256,
    load_manifest,
    save_manifest,
    verify_checksum,
)


class TestComputeSHA256:
    """Tests for SHA-256 computation function."""

    def test_compute_sha256_empty_file(self, tmp_path):
        """Test checksum of empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        checksum = compute_sha256(str(test_file))
        # SHA-256 of empty string
        assert checksum == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_compute_sha256_simple_text(self, tmp_path):
        """Test checksum of simple text file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        checksum = compute_sha256(str(test_file))
        # SHA-256 of "hello world"
        assert checksum == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    def test_compute_sha256_binary_file(self, tmp_path):
        """Test checksum of binary file."""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b'\x00\x01\x02\x03\x04')
        checksum = compute_sha256(str(test_file))
        assert len(checksum) == 64  # SHA-256 produces 64 hex chars


class TestLoadManifest:
    """Tests for manifest loading function."""

    def test_load_manifest_nonexistent(self):
        """Test loading non-existent manifest returns empty dict."""
        manifest = load_manifest("/nonexistent/path/manifest.sha256")
        assert manifest == {}

    def test_load_manifest_empty(self, tmp_path):
        """Test loading empty manifest file."""
        manifest_file = tmp_path / "manifest.sha256"
        manifest_file.write_text("")
        manifest = load_manifest(str(manifest_file))
        assert manifest == {}

    def test_load_manifest_with_entries(self, tmp_path):
        """Test loading manifest with checksum entries."""
        manifest_file = tmp_path / "manifest.sha256"
        manifest_file.write_text(
            "abc123def456  file1.txt\n"
            "def456abc123  file2.txt\n"
        )
        manifest = load_manifest(str(manifest_file))
        assert "file1.txt" in manifest
        assert "file2.txt" in manifest
        assert manifest["file1.txt"] == "abc123def456"

    def test_load_manifest_ignores_comments(self, tmp_path):
        """Test that comment lines are ignored."""
        manifest_file = tmp_path / "manifest.sha256"
        manifest_file.write_text(
            "# This is a comment\n"
            "abc123def456  file1.txt\n"
            "# Another comment\n"
        )
        manifest = load_manifest(str(manifest_file))
        assert len(manifest) == 1
        assert "file1.txt" in manifest

    def test_load_manifest_ignores_blank_lines(self, tmp_path):
        """Test that blank lines are ignored."""
        manifest_file = tmp_path / "manifest.sha256"
        manifest_file.write_text(
            "\n"
            "abc123def456  file1.txt\n"
            "\n"
        )
        manifest = load_manifest(str(manifest_file))
        assert len(manifest) == 1


class TestSaveManifest:
    """Tests for manifest saving function."""

    def test_save_manifest_creates_directory(self, tmp_path):
        """Test that save_manifest creates parent directories."""
        manifest_path = tmp_path / "subdir" / "manifest.sha256"
        manifest = {"file.txt": "abc123"}
        save_manifest(str(manifest_path), manifest)
        assert manifest_path.exists()

    def test_save_manifest_content(self, tmp_path):
        """Test manifest file content format."""
        manifest_file = tmp_path / "manifest.sha256"
        manifest = {"file1.txt": "abc123", "file2.txt": "def456"}
        save_manifest(str(manifest_file), manifest)

        content = manifest_file.read_text()
        assert "# SHA-256 manifest" in content
        assert "abc123  file1.txt" in content
        assert "def456  file2.txt" in content


class TestVerifyChecksum:
    """Tests for checksum verification function."""

    def test_verify_checksum_matches(self, tmp_path):
        """Test successful checksum verification."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        checksum = compute_sha256(str(test_file))
        assert verify_checksum(str(test_file), checksum) is True

    def test_verify_checksum_mismatch(self, tmp_path):
        """Test checksum mismatch detection."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        wrong_checksum = "wrongchecksum123"
        assert verify_checksum(str(test_file), wrong_checksum) is False

    def test_verify_checksum_no_expected(self, tmp_path):
        """Test verification with no expected checksum (None)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        # Should return True when expected_checksum is None
        assert verify_checksum(str(test_file), None) is True

    def test_verify_checksum_case_insensitive(self, tmp_path):
        """Test that checksum comparison is case-insensitive."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        checksum = compute_sha256(str(test_file))
        # Uppercase version should also match
        assert verify_checksum(str(test_file), checksum.upper()) is True


class TestIntegration:
    """Integration tests that combine multiple functions."""

    def test_roundtrip_manifest(self, tmp_path):
        """Test saving and loading manifest preserves data."""
        manifest_file = tmp_path / "manifest.sha256"
        original_manifest = {
            "file1.txt": "abc123def456",
            "file2.txt": "def456abc123",
        }
        save_manifest(str(manifest_file), original_manifest)
        loaded_manifest = load_manifest(str(manifest_file))
        assert loaded_manifest == original_manifest

    def test_full_checksum_workflow(self, tmp_path):
        """Test complete checksum workflow: compute -> save -> verify."""
        # Create test file
        test_file = tmp_path / "data.txt"
        test_file.write_text("test data for checksum workflow")

        # Compute checksum
        checksum = compute_sha256(str(test_file))

        # Create manifest
        manifest_file = tmp_path / "manifest.sha256"
        save_manifest(str(manifest_file), {"data.txt": checksum})

        # Verify
        loaded_manifest = load_manifest(str(manifest_file))
        assert verify_checksum(str(test_file), loaded_manifest["data.txt"]) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])