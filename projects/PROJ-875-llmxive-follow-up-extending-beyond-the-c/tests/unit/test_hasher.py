"""
Unit tests for the hasher utility.
"""
import os
import json
import yaml
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.hasher import generate_version_hash, generate_batch_hash, create_version_manifest


class TestGenerateVersionHash:
    """Tests for the generate_version_hash function."""

    def test_generate_version_hash_basic(self, tmp_path):
        """Test basic version hash generation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        hash_value = generate_version_hash(str(test_file))

        # Should be a short hex string
        assert len(hash_value) == 8
        assert all(c in '0123456789abcdef' for c in hash_value)

    def test_generate_version_hash_consistency(self, tmp_path):
        """Test that the same file produces the same hash."""
        test_file = tmp_path / "consistent.txt"
        test_file.write_text("Consistent content")

        hash1 = generate_version_hash(str(test_file))
        hash2 = generate_version_hash(str(test_file))

        assert hash1 == hash2

    def test_generate_version_hash_different_content(self, tmp_path):
        """Test that different content produces different hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        file1.write_text("Content 1")
        file2.write_text("Content 2")

        hash1 = generate_version_hash(str(file1))
        hash2 = generate_version_hash(str(file2))

        assert hash1 != hash2


class TestGenerateBatchHash:
    """Tests for the generate_batch_hash function."""

    def test_generate_batch_hash_basic(self, tmp_path):
        """Test basic batch hash generation."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        batch_hash = generate_batch_hash([str(file1), str(file2)])

        # Should be a longer hex string
        assert len(batch_hash) == 16
        assert all(c in '0123456789abcdef' for c in batch_hash)

    def test_generate_batch_hash_order_independence(self, tmp_path):
        """Test that batch hash is independent of file order."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        hash1 = generate_batch_hash([str(file1), str(file2)])
        hash2 = generate_batch_hash([str(file2), str(file1)])

        assert hash1 == hash2

    def test_generate_batch_hash_single_file(self, tmp_path):
        """Test batch hash with a single file."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")

        batch_hash = generate_batch_hash([str(file1)])

        assert len(batch_hash) == 16


class TestCreateVersionManifest:
    """Tests for the create_version_manifest function."""

    def test_create_version_manifest_basic(self, tmp_path):
        """Test basic manifest creation."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")

        artifacts = {
            "test_file": str(file1)
        }
        output_file = tmp_path / "manifest.yaml"

        manifest = create_version_manifest(artifacts, str(output_file))

        assert output_file.exists()
        assert "artifacts" in manifest
        assert "test_file" in manifest["artifacts"]
        assert manifest["artifacts"]["test_file"]["hash"] is not None

    def test_create_version_manifest_with_metadata(self, tmp_path):
        """Test manifest creation with metadata."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")

        artifacts = {
            "test_file": str(file1)
        }
        output_file = tmp_path / "manifest.yaml"
        metadata = {
            "project": "test_project",
            "version": "1.0"
        }

        manifest = create_version_manifest(artifacts, str(output_file), metadata)

        assert manifest["metadata"]["project"] == "test_project"
        assert manifest["metadata"]["version"] == "1.0"

    def test_create_version_manifest_missing_file(self, tmp_path):
        """Test manifest creation with a missing file."""
        artifacts = {
            "missing_file": str(tmp_path / "nonexistent.txt")
        }
        output_file = tmp_path / "manifest.yaml"

        manifest = create_version_manifest(artifacts, str(output_file))

        assert manifest["artifacts"]["missing_file"]["hash"] is None
        assert manifest["artifacts"]["missing_file"]["status"] == "missing"
