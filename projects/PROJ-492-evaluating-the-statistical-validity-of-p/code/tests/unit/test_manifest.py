"""
Unit tests for manifest generation functionality (T014).
Verifies that manifest.json is generated with correct SHA256 hashes.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from code.src.utils.manifest import (
    compute_file_hash,
    collect_files_to_hash,
    generate_manifest,
    verify_manifest,
)


class TestManifestGeneration(TestCase):
    """Tests for manifest generation and verification."""

    def setUp(self):
        """Create a temporary directory with test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)

        # Create test files with known content
        self.file1 = self.test_dir / "file1.txt"
        self.file1.write_text("Hello, World!")

        self.file2 = self.test_dir / "subdir" / "file2.json"
        self.file2.parent.mkdir(parents=True, exist_ok=True)
        self.file2.write_text('{"key": "value"}')

        self.file3 = self.test_dir / "data.csv"
        self.file3.write_text("a,b,c\n1,2,3")

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_compute_file_hash(self):
        """Test SHA256 hash computation for a file."""
        # "Hello, World!" SHA256
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        actual_hash = compute_file_hash(self.file1)
        self.assertEqual(actual_hash, expected_hash)
        self.assertEqual(len(actual_hash), 64)  # SHA256 hex length

    def test_compute_file_hash_nonexistent(self):
        """Test that FileNotFoundError is raised for missing files."""
        with self.assertRaises(FileNotFoundError):
            compute_file_hash(self.test_dir / "nonexistent.txt")

    def test_collect_files_to_hash(self):
        """Test file collection with patterns."""
        files = collect_files_to_hash(self.test_dir)
        file_names = [f.name for f in files]
        self.assertIn("file1.txt", file_names)
        self.assertIn("file2.json", file_names)
        self.assertIn("data.csv", file_names)

    def test_collect_files_to_hash_with_exclusions(self):
        """Test file collection with exclusion patterns."""
        # Create a file to exclude
        excluded_file = self.test_dir / "__pycache__" / "test.pyc"
        excluded_file.parent.mkdir(parents=True, exist_ok=True)
        excluded_file.write_text("bytecode")

        files = collect_files_to_hash(
            self.test_dir,
            exclude_patterns=["**/__pycache__/**", "**/*.pyc"],
        )
        file_names = [f.name for f in files]
        self.assertNotIn("test.pyc", file_names)
        self.assertIn("file1.txt", file_names)

    def test_generate_manifest(self):
        """Test full manifest generation."""
        manifest_path = self.test_dir / "manifest.json"
        manifest = generate_manifest(self.test_dir, manifest_path)

        # Verify manifest structure
        self.assertIn("version", manifest)
        self.assertEqual(manifest["version"], "1.0.0")
        self.assertIn("files", manifest)
        self.assertIn("total_files", manifest)
        self.assertEqual(manifest["total_files"], 3)

        # Verify file entries have SHA256 hashes
        for rel_path, file_info in manifest["files"].items():
            self.assertIn("sha256", file_info)
            self.assertIn("size_bytes", file_info)
            self.assertEqual(len(file_info["sha256"]), 64)

        # Verify manifest file was written
        self.assertTrue(manifest_path.exists())

        # Verify JSON is valid
        with open(manifest_path, "r") as f:
            loaded_manifest = json.load(f)
        self.assertEqual(loaded_manifest, manifest)

    def test_verify_manifest_success(self):
        """Test manifest verification when hashes match."""
        manifest_path = self.test_dir / "manifest.json"
        generate_manifest(self.test_dir, manifest_path)

        is_valid = verify_manifest(manifest_path, self.test_dir)
        self.assertTrue(is_valid)

    def test_verify_manifest_failure(self):
        """Test manifest verification when a file is modified."""
        manifest_path = self.test_dir / "manifest.json"
        generate_manifest(self.test_dir, manifest_path)

        # Modify a file after manifest generation
        self.file1.write_text("Modified content")

        is_valid = verify_manifest(manifest_path, self.test_dir)
        self.assertFalse(is_valid)

    def test_verify_manifest_missing_file(self):
        """Test manifest verification when a file is missing."""
        manifest_path = self.test_dir / "manifest.json"
        generate_manifest(self.test_dir, manifest_path)

        # Remove a file after manifest generation
        self.file1.unlink()

        is_valid = verify_manifest(manifest_path, self.test_dir)
        self.assertFalse(is_valid)

    def test_manifest_contains_sha256(self):
        """
        Explicit test for FR-024: Verify manifest.json contains SHA256 hashes.
        """
        manifest_path = self.test_dir / "manifest.json"
        generate_manifest(self.test_dir, manifest_path)

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        # Verify each file entry has a valid SHA256 hash
        for rel_path, file_info in manifest["files"].items():
            sha256_hash = file_info.get("sha256")
            self.assertIsNotNone(sha256_hash, f"Missing sha256 for {rel_path}")
            self.assertEqual(len(sha256_hash), 64, f"Invalid SHA256 length for {rel_path}")
            # Verify it's a valid hex string
            try:
                int(sha256_hash, 16)
            except ValueError:
                self.fail(f"sha256 for {rel_path} is not a valid hex string")