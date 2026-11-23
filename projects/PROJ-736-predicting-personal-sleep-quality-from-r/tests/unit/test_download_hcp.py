"""Unit tests for the HCP data download module."""
import os
import json
import tempfile
import pytest
from pathlib import Path

# Mock the config to avoid path issues in tests
import sys
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.download_hcp import compute_sha256, verify_checksum, save_manifest, load_manifest


class TestChecksumFunctions:
    """Tests for checksum utility functions."""

    def test_compute_sha256(self, tmp_path):
        """Test SHA256 computation on a known file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        checksum = compute_sha256(str(test_file))
        
        # Expected SHA256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

    def test_verify_checksum_valid(self, tmp_path):
        """Test checksum verification with valid hash."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        checksum = compute_sha256(str(test_file))
        assert verify_checksum(str(test_file), checksum) is True

    def test_verify_checksum_invalid(self, tmp_path):
        """Test checksum verification with invalid hash."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        invalid_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        assert verify_checksum(str(test_file), invalid_hash) is False

    def test_verify_checksum_missing_file(self, tmp_path):
        """Test checksum verification with missing file."""
        assert verify_checksum(str(tmp_path / "nonexistent.txt"), "somehash") is False


class TestManifestFunctions:
    """Tests for manifest management functions."""

    def test_save_and_load_manifest(self, tmp_path):
        """Test saving and loading a manifest."""
        manifest_path = tmp_path / "manifest.json"
        test_manifest = {
            "project": "test-project",
            "data_sources": {
                "behavioral": {
                    "url": "http://example.com/data.csv",
                    "sha256": "abc123"
                }
            }
        }

        save_manifest(test_manifest, str(manifest_path))
        
        # Verify file exists
        assert manifest_path.exists()
        
        # Load and verify content
        loaded = load_manifest(str(manifest_path))
        assert loaded["project"] == "test-project"
        assert loaded["data_sources"]["behavioral"]["url"] == "http://example.com/data.csv"

    def test_load_nonexistent_manifest(self, tmp_path):
        """Test loading a manifest that doesn't exist."""
        manifest_path = tmp_path / "nonexistent.json"
        result = load_manifest(str(manifest_path))
        assert result is None

    def test_manifest_with_large_values(self, tmp_path):
        """Test manifest with complex data types."""
        manifest_path = tmp_path / "complex_manifest.json"
        test_manifest = {
            "timestamp": "2023-01-01 12:00:00",
            "nested": {
                "list": [1, 2, 3],
                "dict": {"a": "b"}
            }
        }

        save_manifest(test_manifest, str(manifest_path))
        loaded = load_manifest(str(manifest_path))
        
        assert loaded["nested"]["list"] == [1, 2, 3]
        assert loaded["nested"]["dict"]["a"] == "b"
