"""
Tests for T032: Artifact Hash Generation.
Verifies that the hash generation logic works correctly for files and directories.
"""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.hash_artifacts import hash_file, hash_directory, verify_file_hash

class TestGenerateArtifactHashes(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
        
        # Create test files
        (self.test_dir / "file1.txt").write_text("Hello World")
        (self.test_dir / "file2.txt").write_text("Hello World") # Same content
        (self.test_dir / "file3.txt").write_text("Different Content")
        
        # Create subdirectory
        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("Nested content")

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_hash_file_identical_content(self):
        """Test that files with identical content produce identical hashes."""
        hash1 = hash_file(self.test_dir / "file1.txt")
        hash2 = hash_file(self.test_dir / "file2.txt")
        self.assertEqual(hash1, hash2)

    def test_hash_file_different_content(self):
        """Test that files with different content produce different hashes."""
        hash1 = hash_file(self.test_dir / "file1.txt")
        hash3 = hash_file(self.test_dir / "file3.txt")
        self.assertNotEqual(hash1, hash3)

    def test_hash_file_nonexistent(self):
        """Test that hashing a nonexistent file raises an error or handles gracefully."""
        # The function should raise FileNotFoundError if the file doesn't exist
        with self.assertRaises(FileNotFoundError):
            hash_file(self.test_dir / "nonexistent.txt")

    def test_hash_directory_deterministic(self):
        """Test that hashing a directory produces the same result on repeated calls."""
        hash1 = hash_directory(self.test_dir)
        hash2 = hash_directory(self.test_dir)
        self.assertEqual(hash1, hash2)

    def test_hash_directory_content_sensitivity(self):
        """Test that changing a file in the directory changes the directory hash."""
        hash1 = hash_directory(self.test_dir)
        
        # Modify a file
        (self.test_dir / "file1.txt").write_text("Modified content")
        
        hash2 = hash_directory(self.test_dir)
        self.assertNotEqual(hash1, hash2)

    def test_hash_directory_structure_sensitivity(self):
        """Test that adding a new file changes the directory hash."""
        hash1 = hash_directory(self.test_dir)
        
        # Add a new file
        (self.test_dir / "new_file.txt").write_text("New file")
        
        hash2 = hash_directory(self.test_dir)
        self.assertNotEqual(hash1, hash2)

    def test_verify_file_hash(self):
        """Test the verify_file_hash function."""
        file_path = self.test_dir / "file1.txt"
        correct_hash = hash_file(file_path)
        incorrect_hash = "0" * 64
        
        self.assertTrue(verify_file_hash(file_path, correct_hash))
        self.assertFalse(verify_file_hash(file_path, incorrect_hash))
        self.assertFalse(verify_file_hash(self.test_dir / "nonexistent.txt", correct_hash))

if __name__ == '__main__':
    unittest.main()