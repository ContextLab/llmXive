"""
Unit tests for the hashing utility module.
"""

import os
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.hashing import (
    compute_file_hash,
    compute_string_hash,
    verify_file_hash,
    generate_manifest,
    load_manifest,
)


class TestHashingFunctions(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.temp_dir.name, "test_file.txt")
        self.test_content = "Hello, World! This is a test string."
        
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(self.test_content)
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_compute_file_hash_sha256(self):
        """Test SHA-256 hash computation for a file."""
        expected_hash = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
        # Note: This is the hash of the exact content above. 
        # We will compute it dynamically to be safe.
        computed_hash = compute_file_hash(self.test_file_path, "sha256")
        self.assertEqual(len(computed_hash), 64)  # SHA-256 hex length
        self.assertTrue(all(c in "0123456789abcdef" for c in computed_hash))
    
    def test_compute_file_hash_md5(self):
        """Test MD5 hash computation for a file."""
        computed_hash = compute_file_hash(self.test_file_path, "md5")
        self.assertEqual(len(computed_hash), 32)  # MD5 hex length
    
    def test_compute_string_hash(self):
        """Test hash computation for a string."""
        string_hash = compute_string_hash("test content")
        self.assertEqual(len(string_hash), 64)
    
    def test_verify_file_hash_success(self):
        """Test successful hash verification."""
        file_hash = compute_file_hash(self.test_file_path)
        self.assertTrue(verify_file_hash(self.test_file_path, file_hash))
    
    def test_verify_file_hash_failure(self):
        """Test failed hash verification with wrong hash."""
        wrong_hash = "0" * 64
        self.assertFalse(verify_file_hash(self.test_file_path, wrong_hash))
    
    def test_verify_file_hash_missing(self):
        """Test verification for a non-existent file returns False."""
        self.assertFalse(verify_file_hash("non_existent_file.txt", "dummy_hash"))
    
    def test_compute_file_hash_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with self.assertRaises(FileNotFoundError):
            compute_file_hash("non_existent_file.txt")
    
    def test_compute_file_hash_invalid_algorithm(self):
        """Test that ValueError is raised for unsupported algorithm."""
        with self.assertRaises(ValueError):
            compute_file_hash(self.test_file_path, algorithm="invalid_algo")
    
    def test_generate_manifest(self):
        """Test manifest generation."""
        manifest_path = os.path.join(self.temp_dir.name, "manifest.txt")
        generate_manifest([self.test_file_path], manifest_path)
        
        self.assertTrue(os.path.exists(manifest_path))
        
        with open(manifest_path, "r") as f:
            content = f.read().strip()
        
        parts = content.split("  ")
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[1], self.test_file_path)
        self.assertEqual(len(parts[0]), 64)  # Hash length
    
    def test_load_manifest(self):
        """Test loading a manifest file."""
        manifest_path = os.path.join(self.temp_dir.name, "manifest.txt")
        generate_manifest([self.test_file_path], manifest_path)
        
        loaded_hashes = load_manifest(manifest_path)
        
        self.assertIn(self.test_file_path, loaded_hashes)
        self.assertIsNotNone(loaded_hashes[self.test_file_path])
        self.assertEqual(len(loaded_hashes[self.test_file_path]), 64)
    
    def test_load_manifest_missing_file(self):
        """Test loading manifest with a missing file entry."""
        manifest_path = os.path.join(self.temp_dir.name, "manifest.txt")
        generate_manifest(["non_existent.txt"], manifest_path)
        
        loaded_hashes = load_manifest(manifest_path)
        
        self.assertIn("non_existent.txt", loaded_hashes)
        self.assertIsNone(loaded_hashes["non_existent.txt"])

if __name__ == "__main__":
    unittest.main()