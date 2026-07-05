"""
Unit tests for the manifest generation utility (T014).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from code.src.utils.manifest import (
    compute_sha256,
    generate_manifest,
    load_manifest,
    verify_manifest
)


class TestManifestGeneration(TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        
        # Create some dummy files
        self.file1 = self.base_dir / "file1.txt"
        self.file2 = self.base_dir / "subdir" / "file2.json"
        
        self.file1.parent.mkdir(parents=True, exist_ok=True)
        self.file2.parent.mkdir(parents=True, exist_ok=True)
        
        self.file1.write_text("Hello World")
        self.file2.write_text('{"key": "value"}')
        
        self.manifest_path = self.base_dir / "manifest.json"
    
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compute_sha256(self):
        """Test SHA256 computation matches known values."""
        content = b"Hello World"
        # "Hello World" SHA256
        expected_hash = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
        
        # Create a temp file to test
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            computed_hash = compute_sha256(temp_path)
            self.assertEqual(computed_hash, expected_hash)
        finally:
            temp_path.unlink()

    def test_compute_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with self.assertRaises(FileNotFoundError):
            compute_sha256(Path("/nonexistent/file.txt"))

    def test_generate_manifest_creates_file(self):
        """Test that generate_manifest creates the output file."""
        manifest = generate_manifest(
            artifact_paths=[self.file1, self.file2],
            output_path=self.manifest_path,
            base_dir=self.base_dir
        )
        
        self.assertTrue(self.manifest_path.exists())
        self.assertIn("artifacts", manifest)
        self.assertEqual(len(manifest["artifacts"]), 2)

    def test_generate_manifest_content(self):
        """Test that manifest contains correct hashes and relative paths."""
        manifest = generate_manifest(
            artifact_paths=[self.file1, self.file2],
            output_path=self.manifest_path,
            base_dir=self.base_dir
        )
        
        # Check relative paths
        self.assertIn("file1.txt", manifest["artifacts"])
        self.assertIn("subdir/file2.json", manifest["artifacts"])
        
        # Check hashes exist
        self.assertIn("sha256", manifest["artifacts"]["file1.txt"])
        self.assertIn("sha256", manifest["artifacts"]["subdir/file2.json"])
        
        # Check sizes exist
        self.assertIn("size_bytes", manifest["artifacts"]["file1.txt"])
        self.assertIn("size_bytes", manifest["artifacts"]["subdir/file2.json"])

    def test_load_manifest(self):
        """Test loading a generated manifest."""
        generate_manifest(
            artifact_paths=[self.file1],
            output_path=self.manifest_path,
            base_dir=self.base_dir
        )
        
        loaded = load_manifest(self.manifest_path)
        self.assertIn("artifacts", loaded)
        self.assertIn("file1.txt", loaded["artifacts"])

    def test_verify_manifest_success(self):
        """Test verification passes when files match."""
        generate_manifest(
            artifact_paths=[self.file1, self.file2],
            output_path=self.manifest_path,
            base_dir=self.base_dir
        )
        
        self.assertTrue(verify_manifest(self.manifest_path, self.base_dir))

    def test_verify_manifest_failure_modified_file(self):
        """Test verification fails when a file is modified."""
        generate_manifest(
            artifact_paths=[self.file1],
            output_path=self.manifest_path,
            base_dir=self.base_dir
        )
        
        # Modify the file
        self.file1.write_text("Modified Content")
        
        self.assertFalse(verify_manifest(self.manifest_path, self.base_dir))

    def test_verify_manifest_failure_missing_file(self):
        """Test verification fails when a file is missing."""
        generate_manifest(
            artifact_paths=[self.file1, self.file2],
            output_path=self.manifest_path,
            base_dir=self.base_dir
        )
        
        # Delete a file
        self.file2.unlink()
        
        self.assertFalse(verify_manifest(self.manifest_path, self.base_dir))

    def test_generate_manifest_missing_file_raises(self):
        """Test that generate_manifest raises FileNotFoundError if a file is missing."""
        missing_file = self.base_dir / "nonexistent.txt"
        
        with self.assertRaises(FileNotFoundError):
            generate_manifest(
                artifact_paths=[self.file1, missing_file],
                output_path=self.manifest_path,
                base_dir=self.base_dir
            )
