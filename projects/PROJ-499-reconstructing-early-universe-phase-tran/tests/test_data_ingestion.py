import unittest
import os
import json
from code.data_ingestion import ensure_raw_directory, compute_sha256

class TestDataIngestion(unittest.TestCase):

    def test_ensure_raw_directory(self):
        test_dir = "test_raw"
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)  # Remove if exists for a clean test
        ensure_raw_directory(test_dir)
        self.assertTrue(os.path.exists(test_dir))

    def test_compute_sha256(self):
        # Create a dummy file for testing
        with open("test_file.txt", "w") as f:
            f.write("This is a test file.")
        hash_value = compute_sha256("test_file.txt")
        self.assertEqual(len(hash_value), 64)  # SHA-256 hash should be 64 characters long
        os.remove("test_file.txt") # Clean up the dummy file

if __name__ == '__main__':
    unittest.main()