"""
Unit tests for T024c: Data Hygiene Checksum
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
import hashlib

# Import the functions to test
# We need to adjust the import path if running from tests/
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from t024c_checksum import compute_sha256_file, load_existing_checksums, save_checksums


class TestT024cChecksum(unittest.TestCase):

    def setUp(self):
        """Set up temporary files and directories for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = Path(self.temp_dir.name) / "test_file.bin"
        self.test_checksum_path = Path(self.temp_dir.name) / "checksums.json"
        
        # Create a test file with known content
        self.test_content = b"Hello, this is a test file for checksum verification."
        with open(self.test_file_path, "wb") as f:
            f.write(self.test_content)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_compute_sha256_file(self):
        """Test that compute_sha256_file returns the correct hash."""
        expected_hash = hashlib.sha256(self.test_content).hexdigest()
        computed_hash = compute_sha256_file(self.test_file_path)
        self.assertEqual(computed_hash, expected_hash)

    def test_compute_sha256_file_not_found(self):
        """Test that compute_sha256_file raises FileNotFoundError for missing file."""
        non_existent_path = Path(self.temp_dir.name) / "non_existent.bin"
        with self.assertRaises(FileNotFoundError):
            compute_sha256_file(non_existent_path)

    def test_load_existing_checksums_file_exists(self):
        """Test loading existing checksums from a file."""
        # Create a valid checksum file
        initial_data = {"files": {"test.bin": {"sha256": "abc123"}}}
        with open(self.test_checksum_path, "w") as f:
            json.dump(initial_data, f)
        
        loaded_data = load_existing_checksums(self.test_checksum_path)
        self.assertEqual(loaded_data, initial_data)

    def test_load_existing_checksums_file_missing(self):
        """Test loading checksums when file does not exist."""
        non_existent_path = Path(self.temp_dir.name) / "missing.json"
        loaded_data = load_existing_checksums(non_existent_path)
        self.assertEqual(loaded_data, {"files": {}})

    def test_load_existing_checksums_invalid_json(self):
        """Test loading checksums from an invalid JSON file."""
        with open(self.test_checksum_path, "w") as f:
            f.write("This is not valid JSON")
        
        # Should return empty dict and log warning (handled in function)
        loaded_data = load_existing_checksums(self.test_checksum_path)
        self.assertEqual(loaded_data, {"files": {}})

    def test_save_checksums(self):
        """Test saving checksums to a file."""
        test_checksums = {
            "files": {
                "embeddings.npy": {
                    "sha256": "d41d8cd98f00b204e9800998ecf8427e",
                    "path": "data/processed/embeddings.npy"
                }
            },
            "metadata": {"generated_by": "test"}
        }
        
        save_checksums(test_checksums, self.test_checksum_path)
        
        # Verify file exists and content matches
        self.assertTrue(self.test_checksum_path.exists())
        with open(self.test_checksum_path, "r") as f:
            loaded = json.load(f)
        self.assertEqual(loaded, test_checksums)


if __name__ == "__main__":
    unittest.main()