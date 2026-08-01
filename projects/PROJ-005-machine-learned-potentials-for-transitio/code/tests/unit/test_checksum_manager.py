"""
Unit tests for checksum_manager.py
"""
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import os
import sys

# Add code directory to path to allow imports
code_root = Path(__file__).resolve().parents[2]
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.checksum_manager import (
    compute_file_checksum,
    load_checksum_manifest,
    save_checksum_manifest,
    verify_checksum,
    verify_all_files,
    update_checksum_for_file,
    DEFAULT_ALGORITHM,
    CHECKSUM_MANIFEST_NAME
)


class TestComputeFileChecksum:
    def test_compute_sha256(self, tmp_path):
        """Test computing SHA-256 checksum of a file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        computed_hash = compute_file_checksum(test_file)

        assert computed_hash == expected_hash

    def test_compute_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        missing_file = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(missing_file)

    def test_compute_large_file(self, tmp_path):
        """Test computing checksum of a larger file (chunked reading)."""
        test_file = tmp_path / "large.txt"
        # Create a 1MB file
        content = b"A" * (1024 * 1024)
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        computed_hash = compute_file_checksum(test_file)

        assert computed_hash == expected_hash


class TestChecksumManifest:
    def test_save_and_load_manifest(self, tmp_path):
        """Test saving and loading a checksum manifest."""
        manifest_path = tmp_path / CHECKSUM_MANIFEST_NAME
        test_manifest = {
            "data/file1.txt": "abc123",
            "data/file2.txt": "def456"
        }

        save_checksum_manifest(test_manifest, manifest_path)
        loaded_manifest = load_checksum_manifest(manifest_path)

        assert loaded_manifest == test_manifest

    def test_load_missing_manifest(self, tmp_path):
        """Test loading a non-existent manifest returns empty dict."""
        missing_path = tmp_path / "nonexistent.json"
        manifest = load_checksum_manifest(missing_path)
        assert manifest == {}

    def test_invalid_json_manifest(self, tmp_path):
        """Test handling of invalid JSON in manifest."""
        manifest_path = tmp_path / CHECKSUM_MANIFEST_NAME
        manifest_path.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_checksum_manifest(manifest_path)


class TestVerifyChecksum:
    def test_verify_success(self, tmp_path):
        """Test successful checksum verification."""
        test_file = tmp_path / "test.txt"
        content = b"Test content"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        assert verify_checksum(test_file, expected_hash)

    def test_verify_failure(self, tmp_path):
        """Test failed checksum verification."""
        test_file = tmp_path / "test.txt"
        content = b"Test content"
        test_file.write_bytes(content)

        wrong_hash = "wronghash123"
        assert not verify_checksum(test_file, wrong_hash)

    def test_verify_file_not_found(self, tmp_path):
        """Test verification fails for missing file."""
        missing_file = tmp_path / "nonexistent.txt"
        assert not verify_checksum(missing_file, "anyhash")


class TestVerifyAllFiles:
    def test_verify_all_success(self, tmp_path):
        """Test verifying multiple files with correct checksums."""
        data_raw = tmp_path / "data" / "raw"
        data_raw.mkdir(parents=True)

        # Create test files
        file1 = data_raw / "file1.txt"
        file1.write_bytes(b"Content 1")
        file2 = data_raw / "file2.txt"
        file2.write_bytes(b"Content 2")

        # Create manifest
        manifest = {
            "file1.txt": hashlib.sha256(b"Content 1").hexdigest(),
            "file2.txt": hashlib.sha256(b"Content 2").hexdigest()
        }
        manifest_path = data_raw / CHECKSUM_MANIFEST_NAME
        save_checksum_manifest(manifest, manifest_path)

        # Verify
        all_passed, failed = verify_all_files(manifest_path, data_raw)
        assert all_passed
        assert len(failed) == 0

    def test_verify_some_failed(self, tmp_path):
        """Test verification with some files having wrong checksums."""
        data_raw = tmp_path / "data" / "raw"
        data_raw.mkdir(parents=True)

        # Create test files
        file1 = data_raw / "file1.txt"
        file1.write_bytes(b"Content 1")
        file2 = data_raw / "file2.txt"
        file2.write_bytes(b"Content 2")

        # Create manifest with one wrong checksum
        manifest = {
            "file1.txt": hashlib.sha256(b"Content 1").hexdigest(),
            "file2.txt": "wronghash"
        }
        manifest_path = data_raw / CHECKSUM_MANIFEST_NAME
        save_checksum_manifest(manifest, manifest_path)

        # Verify
        all_passed, failed = verify_all_files(manifest_path, data_raw)
        assert not all_passed
        assert len(failed) == 1
        assert "file2.txt" in failed

    def test_verify_missing_file_in_manifest(self, tmp_path):
        """Test verification when a file in manifest is missing."""
        data_raw = tmp_path / "data" / "raw"
        data_raw.mkdir(parents=True)

        # Create only one file
        file1 = data_raw / "file1.txt"
        file1.write_bytes(b"Content 1")

        # Create manifest with missing file
        manifest = {
            "file1.txt": hashlib.sha256(b"Content 1").hexdigest(),
            "missing.txt": "somehash"
        }
        manifest_path = data_raw / CHECKSUM_MANIFEST_NAME
        save_checksum_manifest(manifest, manifest_path)

        # Verify
        all_passed, failed = verify_all_files(manifest_path, data_raw)
        assert not all_passed
        assert len(failed) == 1
        assert "missing.txt" in failed


class TestUpdateChecksum:
    def test_update_checksum(self, tmp_path):
        """Test updating checksum for a file."""
        data_raw = tmp_path / "data" / "raw"
        data_raw.mkdir(parents=True)

        test_file = data_raw / "test.txt"
        test_file.write_bytes(b"New content")

        manifest_path = data_raw / CHECKSUM_MANIFEST_NAME
        # Initialize empty manifest
        save_checksum_manifest({}, manifest_path)

        # Update checksum
        checksum = update_checksum_for_file(test_file, manifest_path)

        # Verify
        expected_hash = hashlib.sha256(b"New content").hexdigest()
        assert checksum == expected_hash

        manifest = load_checksum_manifest(manifest_path)
        assert "data/raw/test.txt" in manifest
        assert manifest["data/raw/test.txt"] == expected_hash
