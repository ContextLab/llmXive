"""
Unit tests for the Checksum Manager module.
"""

import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import os
import sys

# Add code directory to path to allow imports
code_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(code_dir))

from src.data.checksum_manager import (
    compute_file_checksum,
    load_checksum_manifest,
    save_checksum_manifest,
    verify_checksum,
    verify_all_files,
    update_checksum_for_file,
    get_project_root,
    MANIFEST_FILENAME
)

class TestComputeFileChecksum:
    def test_compute_valid_file(self, tmp_path):
        """Test computing checksum for a valid file."""
        file_path = tmp_path / "test.txt"
        content = b"Hello, World!"
        file_path.write_bytes(content)

        # Compute expected hash manually
        expected_hash = hashlib.sha256(content).hexdigest()

        computed_hash = compute_file_checksum(file_path)
        assert computed_hash == expected_hash

    def test_compute_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        file_path = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(file_path)

    def test_compute_directory(self, tmp_path):
        """Test that ValueError is raised for a directory."""
        with pytest.raises(ValueError):
            compute_file_checksum(tmp_path)

    def test_compute_large_file(self, tmp_path):
        """Test computing checksum for a larger file (chunking)."""
        file_path = tmp_path / "large.bin"
        # Create a 1MB file
        content = b"0" * (1024 * 1024)
        file_path.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        computed_hash = compute_file_checksum(file_path)
        assert computed_hash == expected_hash


class TestChecksumManifest:
    def test_save_and_load_manifest(self, tmp_path):
        """Test saving and loading a checksum manifest."""
        manifest_path = tmp_path / MANIFEST_FILENAME
        test_checksums = {
            "file1.txt": "abc123...",
            "file2.txt": "def456..."
        }

        save_checksum_manifest(test_checksums, manifest_path)
        assert manifest_path.exists()

        loaded = load_checksum_manifest(manifest_path)
        assert loaded == test_checksums

    def test_load_missing_manifest(self, tmp_path):
        """Test loading a non-existent manifest returns empty dict."""
        manifest_path = tmp_path / MANIFEST_FILENAME
        loaded = load_checksum_manifest(manifest_path)
        assert loaded == {}

    def test_load_invalid_json(self, tmp_path):
        """Test loading a manifest with invalid JSON raises error."""
        manifest_path = tmp_path / MANIFEST_FILENAME
        manifest_path.write_text("not valid json {")
        
        with pytest.raises(json.JSONDecodeError):
            load_checksum_manifest(manifest_path)


class TestVerifyChecksum:
    def test_verify_valid(self, tmp_path):
        """Test verifying a file with correct checksum."""
        file_path = tmp_path / "test.txt"
        content = b"Test Content"
        file_path.write_bytes(content)
        expected_hash = hashlib.sha256(content).hexdigest()

        assert verify_checksum(file_path, expected_hash) is True

    def test_verify_invalid(self, tmp_path):
        """Test verifying a file with incorrect checksum."""
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(b"Test Content")
        wrong_hash = "a" * 64

        assert verify_checksum(file_path, wrong_hash) is False

    def test_verify_missing_file(self, tmp_path):
        """Test verifying a missing file returns False."""
        file_path = tmp_path / "missing.txt"
        assert verify_checksum(file_path, "somehash") is False


class TestVerifyAllFiles:
    def test_verify_all_success(self, tmp_path):
        """Test verifying multiple files that all pass."""
        manifest_path = tmp_path / MANIFEST_FILENAME
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        files = {}
        checksums = {}
        for i in range(3):
            fname = f"file{i}.txt"
            content = f"Content {i}".encode()
            fpath = raw_dir / fname
            fpath.write_bytes(content)
            files[fname] = fpath
            checksums[fname] = hashlib.sha256(content).hexdigest()

        save_checksum_manifest(checksums, manifest_path)

        success, failed = verify_all_files(manifest_path)
        assert success is True
        assert len(failed) == 0

    def test_verify_all_failure(self, tmp_path):
        """Test verifying files where one fails."""
        manifest_path = tmp_path / MANIFEST_FILENAME
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        fname = "bad_file.txt"
        fpath = raw_dir / fname
        fpath.write_bytes(b"Good content")
        
        # Put a wrong hash in manifest
        checksums = {fname: "wrong_hash_123456789012345678901234567890123456789012345678"}
        save_checksum_manifest(checksums, manifest_path)

        success, failed = verify_all_files(manifest_path)
        assert success is False
        assert fname in failed

    def test_verify_missing_file_in_manifest(self, tmp_path):
        """Test verifying when a file listed in manifest is missing."""
        manifest_path = tmp_path / MANIFEST_FILENAME
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        checksums = {"missing.txt": "somehash"}
        save_checksum_manifest(checksums, manifest_path)

        success, failed = verify_all_files(manifest_path)
        assert success is False
        assert "missing.txt" in failed


class TestUpdateChecksumForFile:
    def test_update_existing(self, tmp_path):
        """Test updating checksum for an existing file."""
        manifest_path = tmp_path / MANIFEST_FILENAME
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        # Create initial manifest
        save_checksum_manifest({"old.txt": "oldhash"}, manifest_path)

        file_path = raw_dir / "new.txt"
        file_path.write_bytes(b"New content")

        update_checksum_for_file(file_path, manifest_path)

        manifest = load_checksum_manifest(manifest_path)
        # Should contain both old and new
        assert "old.txt" in manifest
        assert "new.txt" in manifest
        assert manifest["new.txt"] == hashlib.sha256(b"New content").hexdigest()

    def test_update_missing_file(self, tmp_path):
        """Test updating checksum for a missing file raises error."""
        manifest_path = tmp_path / MANIFEST_FILENAME
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        file_path = raw_dir / "missing.txt"
        
        with pytest.raises(FileNotFoundError):
            update_checksum_for_file(file_path, manifest_path)

class TestGetProjectRoot:
    def test_get_project_root_type(self):
        """Test that get_project_root returns a Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        # Basic sanity check that it's an absolute path
        assert root.is_absolute()