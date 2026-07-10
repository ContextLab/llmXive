"""
Unit tests for the checksum utility module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from code.utils.checksum import (
    compute_file_checksum,
    compute_directory_checksums,
    validate_file_checksum,
    save_checksums,
    load_checksums,
    generate_checksum_manifest,
    verify_checksum_manifest,
)


class TestChecksumUtility(TestCase):
    """Test cases for checksum utility functions."""

    def setUp(self):
        """Set up temporary directory for test files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_compute_file_checksum_basic(self):
        """Test basic checksum computation for a simple file."""
        test_file = self.test_dir / "test.txt"
        test_file.write_text("Hello, World!")

        checksum = compute_file_checksum(test_file)
        
        # SHA-256 of "Hello, World!" is well-known
        expected = "c0535ee41bea2e675e2780330b98488844321688d88e82013f0958757b278072"
        self.assertEqual(checksum, expected)

    def test_compute_file_checksum_binary(self):
        """Test checksum computation for binary data."""
        test_file = self.test_dir / "binary.bin"
        binary_data = bytes(range(256))
        test_file.write_bytes(binary_data)

        checksum = compute_file_checksum(test_file)
        
        # Verify it's a valid 64-character hex string
        self.assertEqual(len(checksum), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in checksum))

    def test_compute_file_checksum_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        non_existent = self.test_dir / "non_existent.txt"
        
        with self.assertRaises(FileNotFoundError):
            compute_file_checksum(non_existent)

    def test_compute_file_checksum_is_directory(self):
        """Test that IsADirectoryError is raised for directories."""
        with self.assertRaises(IsADirectoryError):
            compute_file_checksum(self.test_dir)

    def test_compute_directory_checksums(self):
        """Test checksum computation for multiple files in a directory."""
        file1 = self.test_dir / "file1.txt"
        file2 = self.test_dir / "file2.txt"
        
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        checksums = compute_directory_checksums(self.test_dir)
        
        self.assertIn("file1.txt", checksums)
        self.assertIn("file2.txt", checksums)
        self.assertEqual(len(checksums), 2)

    def test_compute_directory_checksums_empty(self):
        """Test checksum computation for an empty directory."""
        checksums = compute_directory_checksums(self.test_dir)
        self.assertEqual(checksums, {})

    def test_validate_file_checksum_valid(self):
        """Test validation with correct checksum."""
        test_file = self.test_dir / "test.txt"
        test_file.write_text("Valid content")
        
        checksum = compute_file_checksum(test_file)
        is_valid, message = validate_file_checksum(test_file, checksum)
        
        self.assertTrue(is_valid)
        self.assertIn("Checksum valid", message)

    def test_validate_file_checksum_invalid(self):
        """Test validation with incorrect checksum."""
        test_file = self.test_dir / "test.txt"
        test_file.write_text("Test content")
        
        is_valid, message = validate_file_checksum(test_file, "wrong_checksum")
        
        self.assertFalse(is_valid)
        self.assertIn("Checksum mismatch", message)

    def test_validate_file_checksum_not_found(self):
        """Test validation for non-existent file."""
        is_valid, message = validate_file_checksum(
            self.test_dir / "nonexistent.txt", 
            "some_checksum"
        )
        
        self.assertFalse(is_valid)
        self.assertIn("File not found", message)

    def test_save_and_load_checksums(self):
        """Test saving and loading checksums to/from JSON."""
        test_file = self.test_dir / "test.txt"
        test_file.write_text("Test data")
        
        checksum = compute_file_checksum(test_file)
        checksums = {"test.txt": checksum}
        
        output_path = self.test_dir / "checksums.json"
        save_checksums(checksums, output_path)
        
        loaded_checksums = load_checksums(output_path)
        
        self.assertEqual(loaded_checksums, checksums)

    def test_generate_checksum_manifest(self):
        """Test manifest generation for a directory."""
        file1 = self.test_dir / "file1.txt"
        file2 = self.test_dir / "file2.txt"
        
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        manifest_path = self.test_dir / "manifest.json"
        result_path = generate_checksum_manifest(self.test_dir, manifest_path)
        
        self.assertTrue(result_path.exists())
        
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        self.assertIn("checksums", data)
        self.assertIn("algorithm", data)
        self.assertEqual(data["algorithm"], "sha256")

    def test_verify_checksum_manifest_valid(self):
        """Test manifest verification with valid files."""
        file1 = self.test_dir / "file1.txt"
        file1.write_text("Content 1")
        
        checksum = compute_file_checksum(file1)
        checksums = {"file1.txt": checksum}
        
        manifest_path = self.test_dir / "manifest.json"
        save_checksums(checksums, manifest_path)

        results = verify_checksum_manifest(manifest_path, self.test_dir)
        
        self.assertIn("file1.txt", results)
        self.assertTrue(results["file1.txt"][0])

    def test_verify_checksum_manifest_invalid(self):
        """Test manifest verification with modified files."""
        file1 = self.test_dir / "file1.txt"
        file1.write_text("Original content")
        
        checksum = compute_file_checksum(file1)
        checksums = {"file1.txt": checksum}
        
        manifest_path = self.test_dir / "manifest.json"
        save_checksums(checksums, manifest_path)
        
        # Modify the file
        file1.write_text("Modified content")

        results = verify_checksum_manifest(manifest_path, self.test_dir)
        
        self.assertIn("file1.txt", results)
        self.assertFalse(results["file1.txt"][0])

    def test_checksum_case_insensitive(self):
        """Test that checksum validation is case-insensitive."""
        test_file = self.test_dir / "test.txt"
        test_file.write_text("Test content")
        
        checksum = compute_file_checksum(test_file)
        upper_checksum = checksum.upper()
        
        is_valid, _ = validate_file_checksum(test_file, upper_checksum)
        
        self.assertTrue(is_valid)

    def test_large_file_checksum(self):
        """Test checksum computation for a larger file."""
        test_file = self.test_dir / "large.txt"
        large_content = "A" * (1024 * 1024)  # 1MB of data
        test_file.write_text(large_content)

        checksum = compute_file_checksum(test_file)
        
        # Verify it's a valid checksum
        self.assertEqual(len(checksum), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in checksum))