"""
Unit tests for the checksum_data module.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code import checksum_data


class TestChecksumData(unittest.TestCase):

    def setUp(self):
        """Set up temporary directory for testing."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.test_dir.name)
        
        # Patch the global DATA_DIR and manifest path
        self.original_data_dir = checksum_data.DATA_DIR
        self.original_manifest_path = checksum_data.CHECKSUM_MANIFEST_PATH
        
        checksum_data.DATA_DIR = self.data_dir
        checksum_data.CHECKSUM_MANIFEST_PATH = self.data_dir / "checksums_manifest.json"

    def tearDown(self):
        """Clean up temporary directory."""
        self.test_dir.cleanup()
        checksum_data.DATA_DIR = self.original_data_dir
        checksum_data.CHECKSUM_MANIFEST_PATH = self.original_manifest_path

    def test_calculate_sha256(self):
        """Test SHA-256 calculation on a known string."""
        test_file = self.data_dir / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        # Known SHA-256 for "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        
        actual_hash = checksum_data.calculate_sha256(test_file)
        self.assertEqual(actual_hash, expected_hash)

    def test_calculate_sha256_missing_file(self):
        """Test error handling for missing file."""
        non_existent = self.data_dir / "missing.txt"
        with self.assertRaises(FileNotFoundError):
            checksum_data.calculate_sha256(non_existent)

    def test_load_empty_manifest(self):
        """Test loading when manifest does not exist."""
        manifest = checksum_data.load_manifest()
        self.assertEqual(manifest, {})

    def test_save_and_load_manifest(self):
        """Test saving and loading a manifest."""
        test_manifest = {
            "file1.txt": "hash1",
            "dir/file2.txt": "hash2"
        }
        
        checksum_data.save_manifest(test_manifest)
        
        loaded = checksum_data.load_manifest()
        self.assertEqual(loaded, test_manifest)

    def test_register_file(self):
        """Test registering a file to the manifest."""
        test_file = self.data_dir / "register_test.txt"
        test_file.write_bytes(b"test content")
        
        # Known hash for "test content"
        expected_hash = "9473fdd0d880a43c21b7778d348721579c0c0579343877735105186116426693"
        
        result_hash = checksum_data.register_file(test_file)
        self.assertEqual(result_hash, expected_hash)
        
        manifest = checksum_data.load_manifest()
        self.assertIn("register_test.txt", manifest)
        self.assertEqual(manifest["register_test.txt"], expected_hash)

    def test_verify_file_match(self):
        """Test verifying a file with matching hash."""
        test_file = self.data_dir / "verify_match.txt"
        test_file.write_bytes(b"match content")
        
        # Calculate real hash
        real_hash = checksum_data.calculate_sha256(test_file)
        
        # Add to manifest
        checksum_data.save_manifest({"verify_match.txt": real_hash})
        
        result = checksum_data.verify_file(test_file, real_hash, "verify_match.txt")
        self.assertTrue(result)

    def test_verify_file_mismatch(self):
        """Test verifying a file with mismatched hash."""
        test_file = self.data_dir / "verify_mismatch.txt"
        test_file.write_bytes(b"mismatch content")
        
        wrong_hash = "0" * 64
        
        result = checksum_data.verify_file(test_file, wrong_hash, "verify_mismatch.txt")
        self.assertFalse(result)

    def test_verify_file_missing(self):
        """Test verifying a missing file."""
        missing_file = self.data_dir / "does_not_exist.txt"
        result = checksum_data.verify_file(missing_file, "somehash")
        self.assertFalse(result)

    def test_verify_all(self):
        """Test verifying all files in manifest."""
        # Create two test files
        file1 = self.data_dir / "file1.txt"
        file1.write_bytes(b"data1")
        file2 = self.data_dir / "file2.txt"
        file2.write_bytes(b"data2")
        
        hash1 = checksum_data.calculate_sha256(file1)
        hash2 = checksum_data.calculate_sha256(file2)
        
        # Create manifest with one correct and one wrong hash
        checksum_data.save_manifest({
            "file1.txt": hash1,
            "file2.txt": "wrong_hash"
        })
        
        passed, failed = checksum_data.verify_all()
        self.assertEqual(passed, 1)
        self.assertEqual(failed, 1)

    def test_generate_checksums_for_directory(self):
        """Test generating checksums for a directory structure."""
        # Create nested structure
        subdir = self.data_dir / "subdir"
        subdir.mkdir()
        file1 = self.data_dir / "root.txt"
        file1.write_bytes(b"root data")
        file2 = subdir / "nested.txt"
        file2.write_bytes(b"nested data")
        
        checksums = checksum_data.generate_checksums_for_directory(self.data_dir)
        
        self.assertEqual(len(checksums), 2)
        self.assertIn("root.txt", checksums)
        self.assertIn("subdir/nested.txt", checksums)
        
        # Verify hashes are correct
        self.assertEqual(checksums["root.txt"], checksum_data.calculate_sha256(file1))
        self.assertEqual(checksums["subdir/nested.txt"], checksum_data.calculate_sha256(file2))


if __name__ == "__main__":
    unittest.main()