"""
Unit tests for the Checksum Manager functionality.
"""
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import os
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.checksum_manager import (
    compute_file_checksum,
    load_checksum_manifest,
    save_checksum_manifest,
    verify_checksum,
    verify_all_files,
    update_checksum_for_file,
    get_project_root
)

class TestComputeFileChecksum:
    def test_compute_checksum_valid_file(self, tmp_path):
        """Test checksum computation on a valid file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_file_checksum(test_file)

        assert actual_hash == expected_hash

    def test_compute_checksum_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        missing_file = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            compute_file_checksum(missing_file)

    def test_compute_checksum_large_file(self, tmp_path):
        """Test checksum computation on a larger file (chunked reading)."""
        test_file = tmp_path / "large.bin"
        # Create a 1MB file
        content = b"x" * (1024 * 1024)
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_file_checksum(test_file)

        assert actual_hash == expected_hash

class TestChecksumManifest:
    def test_save_and_load_manifest(self, tmp_path):
        """Test saving and loading a checksum manifest."""
        manifest_path = tmp_path / "manifest.json"
        test_manifest = {
            "data/raw/file1.txt": "abc123...",
            "data/raw/file2.bin": "def456..."
        }

        save_checksum_manifest(test_manifest, manifest_path)

        loaded_manifest = load_checksum_manifest(manifest_path)

        assert loaded_manifest == test_manifest

    def test_load_manifest_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing manifest."""
        missing_manifest = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load_checksum_manifest(missing_manifest)

    def test_load_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        manifest_path = tmp_path / "invalid.json"
        manifest_path.write_text("not valid json")

        with pytest.raises(json.JSONDecodeError):
            load_checksum_manifest(manifest_path)

class TestVerifyChecksum:
    def test_verify_valid_checksum(self, tmp_path):
        """Test verification with matching checksum."""
        test_file = tmp_path / "test.txt"
        content = b"Test content"
        test_file.write_bytes(content)

        checksum = compute_file_checksum(test_file)
        assert verify_checksum(test_file, checksum) is True

    def test_verify_invalid_checksum(self, tmp_path):
        """Test verification with mismatched checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")

        assert verify_checksum(test_file, "wrong_checksum") is False

    def test_verify_missing_file(self, tmp_path):
        """Test verification on missing file."""
        missing_file = tmp_path / "nonexistent.txt"

        assert verify_checksum(missing_file, "any_checksum") is False

class TestVerifyAllFiles:
    def test_verify_all_valid(self, tmp_path):
        """Test verifying multiple valid files."""
        manifest_path = tmp_path / "manifest.json"
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        # Create test files
        file1 = raw_dir / "file1.txt"
        file1.write_bytes(b"Content 1")
        file2 = raw_dir / "file2.txt"
        file2.write_bytes(b"Content 2")

        manifest = {
            "raw/file1.txt": compute_file_checksum(file1),
            "raw/file2.txt": compute_file_checksum(file2)
        }
        save_checksum_manifest(manifest, manifest_path)

        all_ok, failures = verify_all_files(manifest_path, tmp_path)

        assert all_ok is True
        assert len(failures) == 0

    def test_verify_all_with_missing_file(self, tmp_path):
        """Test verification when one file is missing."""
        manifest_path = tmp_path / "manifest.json"
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        file1 = raw_dir / "file1.txt"
        file1.write_bytes(b"Content 1")

        # Create manifest with a missing file
        manifest = {
            "raw/file1.txt": compute_file_checksum(file1),
            "raw/file2.txt": "some_checksum"  # This file doesn't exist
        }
        save_checksum_manifest(manifest, manifest_path)

        all_ok, failures = verify_all_files(manifest_path, tmp_path)

        assert all_ok is False
        assert "raw/file2.txt" in failures

class TestUpdateChecksumForFile:
    def test_update_existing_manifest(self, tmp_path):
        """Test updating checksum in an existing manifest."""
        manifest_path = tmp_path / "manifest.json"
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Original content")

        # Create initial manifest
        initial_manifest = {"test.txt": "old_checksum"}
        save_checksum_manifest(initial_manifest, manifest_path)

        # Update content
        test_file.write_bytes(b"New content")

        # Update checksum
        update_checksum_for_file(test_file, manifest_path)

        # Verify update
        manifest = load_checksum_manifest(manifest_path)
        new_checksum = compute_file_checksum(test_file)
        assert manifest["test.txt"] == new_checksum

    def test_update_new_file(self, tmp_path):
        """Test updating checksum for a file not in manifest."""
        manifest_path = tmp_path / "manifest.json"
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"New content")

        # Create empty manifest
        save_checksum_manifest({}, manifest_path)

        update_checksum_for_file(test_file, manifest_path)

        manifest = load_checksum_manifest(manifest_path)
        assert "test.txt" in manifest
        assert manifest["test.txt"] == compute_file_checksum(test_file)

class TestGetProjectRoot:
    def test_get_project_root_returns_path(self):
        """Test that get_project_root returns a valid Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()
        # Check that 'src' directory exists under root
        assert (root / 'src').exists()