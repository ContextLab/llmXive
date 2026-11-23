"""
Integration tests for the data_hygiene module.
"""
import os
import json
import tempfile
import shutil
import unittest
from pathlib import Path

# Ensure we can import from the project root
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.data_hygiene import compute_sha256, record_checksums
from utils.logger import get_logger

logger = get_logger(__name__)

class TestDataHygiene(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.raw_dir = os.path.join(self.test_dir, "data", "raw")
        self.processed_dir = os.path.join(self.test_dir, "data", "processed")
        os.makedirs(self.raw_dir)
        os.makedirs(self.processed_dir)
        
        # Create dummy CSV files for testing
        self.test_files = []
        for i, name in enumerate(["high_entropy.csv", "low_entropy.csv", "target_specific.csv", "test_set.csv"]):
            path = os.path.join(self.raw_dir, name)
            with open(path, "w") as f:
                f.write(f"id,data\n{i},test_data_{i}\n")
            self.test_files.append(path)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_compute_sha256(self):
        """Test that compute_sha256 returns a valid hex string."""
        file_path = self.test_files[0]
        checksum = compute_sha256(file_path)
        self.assertIsInstance(checksum, str)
        self.assertEqual(len(checksum), 64) # SHA256 hex is 64 chars
        # Verify consistency
        self.assertEqual(checksum, compute_sha256(file_path))

    def test_record_checksums(self):
        """Test that record_checksums creates the JSON file and logs correctly."""
        output_path = os.path.join(self.processed_dir, "test_checksums.json")
        result = record_checksums(self.test_files, output_path)
        
        # Check return value
        self.assertEqual(len(result), len(self.test_files))
        for path in self.test_files:
            self.assertIn(path, result)
            self.assertEqual(len(result[path]), 64)
        
        # Check file creation
        self.assertTrue(os.path.exists(output_path))
        
        # Check content validity
        with open(output_path, "r") as f:
            data = json.load(f)
        self.assertEqual(data, result)

    def test_record_checksums_missing_file(self):
        """Test that record_checksums raises FileNotFoundError for missing files."""
        missing_file = os.path.join(self.raw_dir, "non_existent.csv")
        with self.assertRaises(FileNotFoundError):
            record_checksums([self.test_files[0], missing_file])

if __name__ == "__main__":
    unittest.main()