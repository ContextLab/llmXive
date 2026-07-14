import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.download import (
    calculate_sha256,
    download_dataset,
    validate_checksum,
    load_checksums,
    save_checksums,
    log_info,
    log_error
)

class TestDownloadFunctions(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_calculate_sha256(self):
        """Test SHA256 calculation on a known string."""
        test_file = self.temp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        calculated_sha = calculate_sha256(test_file)
        expected_sha = hashlib.sha256(test_content).hexdigest()

        self.assertEqual(calculated_sha, expected_sha)

    def test_validate_checksum_true(self):
        """Test checksum validation when it matches."""
        test_file = self.temp_path / "test.txt"
        test_content = b"Test content"
        test_file.write_bytes(test_content)

        actual_sha = hashlib.sha256(test_content).hexdigest()
        self.assertTrue(validate_checksum(test_file, actual_sha))

    def test_validate_checksum_false(self):
        """Test checksum validation when it doesn't match."""
        test_file = self.temp_path / "test.txt"
        test_file.write_bytes(b"Test content")

        self.assertFalse(validate_checksum(test_file, "wrong_checksum"))

    def test_validate_checksum_missing_file(self):
        """Test checksum validation on missing file."""
        missing_file = self.temp_path / "nonexistent.txt"
        self.assertFalse(validate_checksum(missing_file, "any_checksum"))

    def test_load_checksums_empty(self):
        """Test loading checksums from non-existent file."""
        # Use a temporary directory that doesn't have the checksums file
        temp_checksums_file = self.temp_path / "checksums.json"
        # Temporarily override the global path
        import data.download as download_module
        original_path = download_module.CHECKSUMS_FILE
        download_module.CHECKSUMS_FILE = temp_checksums_file

        try:
            checksums = load_checksums()
            self.assertEqual(checksums, {})
        finally:
            download_module.CHECKSUMS_FILE = original_path

    def test_save_and_load_checksums(self):
        """Test saving and loading checksums."""
        temp_checksums_file = self.temp_path / "checksums.json"
        import data.download as download_module
        original_path = download_module.CHECKSUMS_FILE
        download_module.CHECKSUMS_FILE = temp_checksums_file

        try:
            test_checksums = {"dataset1": "abc123", "dataset2": "def456"}
            save_checksums(test_checksums)

            loaded_checksums = load_checksums()
            self.assertEqual(loaded_checksums, test_checksums)
        finally:
            download_module.CHECKSUMS_FILE = original_path

if __name__ == "__main__":
    unittest.main()