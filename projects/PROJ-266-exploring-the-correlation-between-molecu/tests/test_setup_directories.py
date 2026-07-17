"""
Unit tests for the setup_directories module (T008).

Tests directory creation, checksum computation, and manifest generation.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# Note: We assume the module is installed or in PYTHONPATH
from code.data.setup_directories import (
    create_directories,
    compute_file_checksum,
    generate_checksum_manifest,
    verify_checksums,
)
from code.utils.config import get_project_root


class TestCreateDirectories:
    """Tests for directory creation functionality."""

    def test_creates_required_directories(self, tmp_path):
        """Test that all required directories are created."""
        with patch('code.data.setup_directories.get_project_root', return_value=tmp_path):
            result = create_directories()
            
            # Check that all expected directories exist
            assert "raw" in result
            assert "processed" in result
            assert "interim" in result
            assert "figures" in result
            
            # Check that the directories actually exist on disk
            for name, path in result.items():
                assert path.exists(), f"Directory {path} was not created"
                assert path.is_dir(), f"{path} is not a directory"

    def test_does_not_recreate_existing_directories(self, tmp_path):
        """Test that existing directories are not recreated."""
        # Pre-create some directories
        (tmp_path / "data" / "raw").mkdir(parents=True)
        
        with patch('code.data.setup_directories.get_project_root', return_value=tmp_path):
            result = create_directories()
            
            # Should still return the paths
            assert "raw" in result
            # The directory should still exist
            assert result["raw"].exists()


class TestComputeFileChecksum:
    """Tests for file checksum computation."""

    def test_compute_sha256_checksum(self, tmp_path):
        """Test computing SHA-256 checksum of a file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        checksum = compute_file_checksum(test_file)
        
        # SHA-256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

    def test_compute_different_algorithms(self, tmp_path):
        """Test computing checksums with different algorithms."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Test SHA-256
        sha256_checksum = compute_file_checksum(test_file, "sha256")
        assert len(sha256_checksum) == 64  # 64 hex chars for SHA-256
        
        # Test MD5
        md5_checksum = compute_file_checksum(test_file, "md5")
        assert len(md5_checksum) == 32  # 32 hex chars for MD5

    def test_file_not_found_error(self, tmp_path):
        """Test that FileNotFoundError is raised for missing files."""
        missing_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(missing_file)

    def test_invalid_algorithm(self, tmp_path):
        """Test that ValueError is raised for invalid algorithms."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        with pytest.raises(ValueError):
            compute_file_checksum(test_file, "invalid_algorithm")


class TestGenerateChecksumManifest:
    """Tests for checksum manifest generation."""

    def test_generates_manifest_for_directory(self, tmp_path):
        """Test manifest generation for a directory with files."""
        # Create some test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("content3")
        
        manifest = generate_checksum_manifest(tmp_path)
        
        # Check that all files are in the manifest
        assert "file1.txt" in manifest
        assert "file2.txt" in manifest
        assert "subdir/file3.txt" in manifest
        
        # Check that checksums are valid hex strings
        for checksum in manifest.values():
            assert len(checksum) == 64  # SHA-256
            assert all(c in "0123456789abcdef" for c in checksum)

    def test_excludes_hidden_and_temp_files(self, tmp_path):
        """Test that hidden and temp files are excluded from manifest."""
        (tmp_path / "visible.txt").write_text("visible")
        (tmp_path / ".hidden.txt").write_text("hidden")
        (tmp_path / "temp.tmp").write_text("temp")
        
        manifest = generate_checksum_manifest(tmp_path)
        
        assert "visible.txt" in manifest
        assert ".hidden.txt" not in manifest
        assert "temp.tmp" not in manifest

    def test_writes_manifest_to_file(self, tmp_path):
        """Test that manifest can be written to a file."""
        (tmp_path / "test.txt").write_text("test")
        output_path = tmp_path / "manifest.json"
        
        manifest = generate_checksum_manifest(tmp_path, output_path)
        
        # Check that the file was created
        assert output_path.exists()
        
        # Check that the file contains valid JSON
        with open(output_path, "r") as f:
            loaded_manifest = json.load(f)
        
        assert loaded_manifest == manifest


class TestVerifyChecksums:
    """Tests for checksum verification."""

    def test_verifies_valid_checksums(self, tmp_path):
        """Test verification when all checksums are valid."""
        # Create files and manifest
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        
        manifest = generate_checksum_manifest(tmp_path)
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)
        
        # Verify should return True
        assert verify_checksums(manifest_path, tmp_path) is True

    def test_fails_on_missing_file(self, tmp_path):
        """Test verification fails when a file is missing."""
        (tmp_path / "file1.txt").write_text("content1")
        
        manifest = {"file1.txt": "valid_checksum", "missing.txt": "checksum"}
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)
        
        # Verify should return False
        assert verify_checksums(manifest_path, tmp_path) is False

    def test_fails_on_checksum_mismatch(self, tmp_path):
        """Test verification fails when checksum doesn't match."""
        (tmp_path / "file1.txt").write_text("content1")
        
        # Create a manifest with an incorrect checksum
        manifest = {"file1.txt": "0000000000000000000000000000000000000000000000000000000000000000"}
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)
        
        # Verify should return False
        assert verify_checksums(manifest_path, tmp_path) is False

    def test_fails_on_missing_manifest(self, tmp_path):
        """Test verification fails when manifest file is missing."""
        missing_manifest = tmp_path / "nonexistent_manifest.json"
        assert verify_checksums(missing_manifest, tmp_path) is False
