"""
Unit tests for validation_utils.py
"""
import json
import os
import tempfile
import time
from pathlib import Path
from unittest import TestCase

import pytest

from code.validation_utils import (
    compute_file_checksum,
    verify_file_integrity,
    create_manifest,
    verify_manifest,
    check_file_age,
    save_manifest,
    DEFAULT_ALGORITHM
)


class TestComputeFileChecksum(TestCase):
    def test_compute_checksum_sha256(self):
        """Test checksum computation with SHA256."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            temp_path = Path(f.name)
        
        try:
            checksum = compute_file_checksum(temp_path, algorithm='sha256')
            self.assertEqual(len(checksum), 64)  # SHA256 hex length
            self.assertTrue(all(c in '0123456789abcdef' for c in checksum.lower()))
        finally:
            os.unlink(temp_path)

    def test_compute_checksum_md5(self):
        """Test checksum computation with MD5."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            temp_path = Path(f.name)
        
        try:
            checksum = compute_file_checksum(temp_path, algorithm='md5')
            self.assertEqual(len(checksum), 32)  # MD5 hex length
        finally:
            os.unlink(temp_path)

    def test_compute_checksum_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with self.assertRaises(FileNotFoundError):
            compute_file_checksum(Path("/nonexistent/file.txt"))

    def test_compute_checksum_invalid_algorithm(self):
        """Test that ValueError is raised for invalid algorithm."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)
        try:
            with self.assertRaises(ValueError):
                compute_file_checksum(temp_path, algorithm='invalid_algo')
        finally:
            os.unlink(temp_path)


class TestVerifyFileIntegrity(TestCase):
    def test_verify_success(self):
        """Test successful verification."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            temp_path = Path(f.name)
        
        try:
            checksum = compute_file_checksum(temp_path)
            self.assertTrue(verify_file_integrity(temp_path, checksum))
        finally:
            os.unlink(temp_path)

    def test_verify_failure(self):
        """Test verification failure with wrong checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            temp_path = Path(f.name)
        
        try:
            self.assertFalse(verify_file_integrity(temp_path, "wrong_checksum"))
        finally:
            os.unlink(temp_path)

    def test_verify_file_not_found(self):
        """Test verification returns False for missing file."""
        self.assertFalse(verify_file_integrity(Path("/nonexistent/file.txt"), "checksum"))


class TestCreateManifest(TestCase):
    def test_create_manifest_single_file(self):
        """Test manifest creation for a single file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            manifest = create_manifest([temp_path])
            self.assertIn("files", manifest)
            self.assertIn("algorithm", manifest)
            self.assertIn("created_at", manifest)
            self.assertEqual(len(manifest["files"]), 1)
            self.assertIn(str(temp_path), manifest["files"])
        finally:
            os.unlink(temp_path)

    def test_create_manifest_missing_file(self):
        """Test manifest creation handles missing files gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            missing_path = Path("/nonexistent/file.txt")
            manifest = create_manifest([temp_path, missing_path])
            self.assertEqual(len(manifest["files"]), 1)  # Only the existing file
        finally:
            os.unlink(temp_path)

    def test_create_manifest_save(self):
        """Test manifest creation and saving to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest.json"
            try:
                manifest = create_manifest([temp_path], output_path=output_path)
                self.assertTrue(output_path.exists())
                with open(output_path, 'r') as f:
                    saved_manifest = json.load(f)
                self.assertEqual(manifest, saved_manifest)
            finally:
                os.unlink(temp_path)


class TestVerifyManifest(TestCase):
    def test_verify_manifest_success(self):
        """Test successful manifest verification."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            manifest = create_manifest([temp_path])
            all_valid, passed, failed = verify_manifest(manifest)
            self.assertTrue(all_valid)
            self.assertEqual(len(passed), 1)
            self.assertEqual(len(failed), 0)
        finally:
            os.unlink(temp_path)

    def test_verify_manifest_failure(self):
        """Test manifest verification with corrupted file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            manifest = create_manifest([temp_path])
            # Corrupt the file
            with open(temp_path, 'w') as f:
                f.write("corrupted content")
            
            all_valid, passed, failed = verify_manifest(manifest)
            self.assertFalse(all_valid)
            self.assertEqual(len(passed), 0)
            self.assertEqual(len(failed), 1)
        finally:
            os.unlink(temp_path)

    def test_verify_manifest_missing_file(self):
        """Test manifest verification with missing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            manifest = create_manifest([temp_path])
            os.unlink(temp_path)  # Delete the file
            
            all_valid, passed, failed = verify_manifest(manifest)
            self.assertFalse(all_valid)
            self.assertEqual(len(passed), 0)
            self.assertEqual(len(failed), 1)
        finally:
            pass  # File already deleted


class TestCheckFileAge(TestCase):
    def test_check_file_age_fresh(self):
        """Test file age check for a fresh file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            self.assertTrue(check_file_age(temp_path, max_age_seconds=60))
        finally:
            os.unlink(temp_path)

    def test_check_file_age_stale(self):
        """Test file age check for a stale file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)
        
        # Set modification time to 1 hour ago
        old_time = time.time() - 3600
        os.utime(temp_path, (old_time, old_time))
        
        try:
            self.assertFalse(check_file_age(temp_path, max_age_seconds=60))
        finally:
            os.unlink(temp_path)

    def test_check_file_age_not_found(self):
        """Test file age check raises error for missing file."""
        with self.assertRaises(FileNotFoundError):
            check_file_age(Path("/nonexistent/file.txt"), max_age_seconds=60)


class TestSaveManifest(TestCase):
    def test_save_manifest(self):
        """Test saving manifest to file."""
        manifest = {
            "algorithm": "sha256",
            "created_at": "2023-01-01T00:00:00Z",
            "files": {}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_manifest.json"
            save_manifest(manifest, output_path)
            
            self.assertTrue(output_path.exists())
            with open(output_path, 'r') as f:
                loaded_manifest = json.load(f)
            self.assertEqual(manifest, loaded_manifest)
