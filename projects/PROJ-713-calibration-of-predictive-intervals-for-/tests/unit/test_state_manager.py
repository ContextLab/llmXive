"""
Unit tests for the state_manager module.

Tests verify:
1. Hash computation and verification logic.
2. Timestamp validation logic.
3. Manifest loading and saving.
4. Integrity check failures (missing files, bad hashes).
"""
import os
import json
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime
from unittest import TestCase

import pytest

# Import the module under test
# Note: We assume the test is run from the project root or PYTHONPATH is set
from state_manager import (
    compute_file_checksum,
    load_state_manifest,
    save_state_manifest,
    verify_file_hash,
    verify_timestamps,
    verify_state_integrity,
    update_state_manifest,
    MANIFEST_FILENAME,
    STATE_DIR_NAME
)
from utils.exceptions import DataValidationError


class TestChecksums(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = Path(self.temp_dir) / "test.txt"
        self.test_content = b"Hello, World! This is a test file for checksums."
        self.test_file_path.write_bytes(self.test_content)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_compute_file_checksum(self):
        """Test that compute_file_checksum returns a valid SHA-256 hex string."""
        checksum = compute_file_checksum(self.test_file_path)
        self.assertEqual(len(checksum), 64)  # SHA-256 hex length
        self.assertTrue(all(c in '0123456789abcdef' for c in checksum))

    def test_compute_file_checksum_nonexistent(self):
        """Test that compute_file_checksum raises FileNotFoundError for missing files."""
        with self.assertRaises(FileNotFoundError):
            compute_file_checksum(Path(self.temp_dir) / "nonexistent.txt")


class TestManifestIO(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir) / "state"
        self.state_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_save_and_load_manifest(self):
        """Test saving and loading a manifest."""
        data = {
            "version": "1.0",
            "files": {"test.txt": {"hash": "abc123"}}
        }
        save_state_manifest(self.state_dir, data)
        
        loaded = load_state_manifest(self.state_dir)
        self.assertEqual(loaded, data)

    def test_load_manifest_missing(self):
        """Test loading manifest when it doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            load_state_manifest(self.state_dir)

    def test_load_manifest_invalid_json(self):
        """Test loading manifest with invalid JSON."""
        manifest_path = self.state_dir / MANIFEST_FILENAME
        manifest_path.write_text("{ invalid json }")
        with self.assertRaises(json.JSONDecodeError):
            load_state_manifest(self.state_dir)


class TestFileHashVerification(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir) / "state"
        self.state_dir.mkdir()
        self.test_file = self.state_dir / "data.txt"
        self.test_file.write_bytes(b"test content")
        self.correct_hash = compute_file_checksum(self.test_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_verify_file_hash_success(self):
        """Test successful hash verification."""
        result = verify_file_hash(self.state_dir, "data.txt", self.correct_hash)
        self.assertTrue(result)

    def test_verify_file_hash_mismatch(self):
        """Test verification fails on hash mismatch."""
        with self.assertRaises(DataValidationError):
            verify_file_hash(self.state_dir, "data.txt", "wrong_hash")

    def test_verify_file_hash_missing(self):
        """Test verification fails on missing file."""
        with self.assertRaises(DataValidationError):
            verify_file_hash(self.state_dir, "missing.txt", "any_hash")


class TestTimestampVerification(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir) / "state"
        self.state_dir.mkdir()
        self.test_file = self.state_dir / "data.txt"
        self.test_file.write_bytes(b"test")
        self.mtime = self.test_file.stat().st_mtime

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_verify_timestamps_valid(self):
        """Test timestamp verification with valid data."""
        manifest = {
            "updated_at": datetime.now().isoformat(),
            "files": {
                "data.txt": {"updated_at": self.mtime}
            }
        }
        warnings = verify_timestamps(self.state_dir, manifest)
        self.assertEqual(len(warnings), 0)

    def test_verify_timestamps_future(self):
        """Test timestamp verification detects future dates."""
        future_time = (datetime.now().timestamp() + 1000000)
        manifest = {
            "updated_at": future_time,
            "files": {}
        }
        warnings = verify_timestamps(self.state_dir, manifest)
        self.assertTrue(any("future" in w for w in warnings))

    def test_verify_timestamps_missing_file(self):
        """Test timestamp verification detects missing files."""
        manifest = {
            "updated_at": datetime.now().isoformat(),
            "files": {
                "missing.txt": {"updated_at": self.mtime}
            }
        }
        warnings = verify_timestamps(self.state_dir, manifest)
        self.assertTrue(any("missing" in w for w in warnings))


class TestIntegrityCheck(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir) / "state"
        self.state_dir.mkdir()
        self.test_file = self.state_dir / "good.txt"
        self.test_file.write_bytes(b"good content")
        
        # Create a valid manifest
        manifest = {
            "updated_at": datetime.now().isoformat(),
            "files": {
                "good.txt": {
                    "hash": compute_file_checksum(self.test_file),
                    "updated_at": self.test_file.stat().st_mtime
                }
            }
        }
        save_state_manifest(self.state_dir, manifest)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_verify_state_integrity_pass(self):
        """Test full integrity check passes on valid state."""
        is_valid, errors = verify_state_integrity(self.state_dir)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_verify_state_integrity_missing_file(self):
        """Test integrity check fails if file is missing."""
        self.test_file.unlink()
        is_valid, errors = verify_state_integrity(self.state_dir)
        self.assertFalse(is_valid)
        self.assertTrue(any("missing" in str(e).lower() for e in errors))

    def test_verify_state_integrity_missing_manifest(self):
        """Test integrity check fails if manifest is missing."""
        manifest_path = self.state_dir / MANIFEST_FILENAME
        manifest_path.unlink()
        is_valid, errors = verify_state_integrity(self.state_dir)
        self.assertFalse(is_valid)
        self.assertTrue(any("manifest" in str(e).lower() for e in errors))


class TestUpdateManifest(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir) / "state"
        self.state_dir.mkdir()
        self.test_file = self.state_dir / "new.txt"
        self.test_file.write_bytes(b"new content")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_update_state_manifest(self):
        """Test updating manifest creates correct entries."""
        update_state_manifest(self.state_dir, [self.test_file])
        
        manifest = load_state_manifest(self.state_dir)
        
        self.assertIn("new.txt", manifest["files"])
        self.assertIn("hash", manifest["files"]["new.txt"])
        self.assertIn("updated_at", manifest["files"]["new.txt"])
        self.assertEqual(manifest["files"]["new.txt"]["hash"], compute_file_checksum(self.test_file))
        self.assertIn("updated_at", manifest)
        self.assertIn("created_at", manifest)
