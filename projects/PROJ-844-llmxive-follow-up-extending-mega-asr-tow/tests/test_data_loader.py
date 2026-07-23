import unittest
from code.data_loader import compute_file_hash, verify_checksum
import os

class TestDataLoader(unittest.TestCase):

    def test_compute_file_hash(self):
        # Create a dummy file for testing
        with open("test_file.txt", "w") as f:
            f.write("This is a test file.")
        
        # Compute the hash of the file
        hash_value = compute_file_hash("test_file.txt")

        # Verify that the hash is not empty
        self.assertIsNotNone(hash_value)

        # Clean up the dummy file
        os.remove("test_file.txt")
    
    def test_verify_checksum(self):
        # Create a dummy file for testing
        with open("test_file.txt", "w") as f:
            f.write("This is a test file.")

        # Compute the hash of the file
        expected_hash = compute_file_hash("test_file.txt")

        # Verify that the checksum matches
        self.assertTrue(verify_checksum("test_file.txt", expected_hash))

        # Clean up the dummy file
        os.remove("test_file.txt")

if __name__ == '__main__':
    unittest.main()