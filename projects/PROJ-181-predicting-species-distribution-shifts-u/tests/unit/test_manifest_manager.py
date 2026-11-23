"""
Unit tests for the manifest_manager module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

import sys

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from manifest_manager import (
    compute_sha256,
    load_manifest,
    save_manifest,
    update_manifest,
    verify_dataset,
    list_datasets,
    MANIFEST_PATH
)


class TestManifestManager(TestCase):
    """Test cases for Manifest Manager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.temp_manifest_path = Path(self.test_dir.name) / "test_manifest.json"

        # Mock the global MANIFEST_PATH to use our temp file
        self.original_manifest_path = MANIFEST_PATH
        # We cannot easily mock the module-level constant, so we will test the logic
        # by creating files in the temp dir and passing them to functions that accept paths,
        # or by mocking the file operations.
        # For update_manifest, we need to patch the load/save functions or the global path.
        # Since MANIFEST_PATH is imported at module level in manifest_manager, we patch the module.
        import manifest_manager
        self.patcher = patch.object(manifest_manager, 'MANIFEST_PATH', self.temp_manifest_path)
        self.mock_manifest_path = self.patcher.start()

        # Create a dummy file for checksum tests
        self.dummy_file = Path(self.test_dir.name) / "dummy.txt"
        self.dummy_file.write_text("Hello, World!")

    def tearDown(self):
        """Tear down test fixtures."""
        self.patcher.stop()
        self.test_dir.cleanup()

    def test_compute_sha256(self):
        """Test SHA-256 computation."""
        checksum = compute_sha256(self.dummy_file)
        # Known SHA-256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        self.assertEqual(checksum, expected)

    def test_compute_sha256_file_not_found(self):
        """Test SHA-256 raises error for missing file."""
        with self.assertRaises(FileNotFoundError):
            compute_sha256(Path("/nonexistent/file.txt"))

    def test_load_manifest_empty(self):
        """Test loading non-existent manifest returns empty structure."""
        # Ensure file doesn't exist
        if self.temp_manifest_path.exists():
            self.temp_manifest_path.unlink()

        manifest = load_manifest()
        self.assertIn("datasets", manifest)
        self.assertIn("metadata", manifest)
        self.assertEqual(manifest["datasets"], {})

    def test_load_manifest_existing(self):
        """Test loading existing manifest."""
        # Create a manifest file
        data = {
            "datasets": {"test": {"file_path": "test.txt"}},
            "metadata": {"version": "1.0"}
        }
        with open(self.temp_manifest_path, "w") as f:
            json.dump(data, f)

        manifest = load_manifest()
        self.assertEqual(manifest["datasets"]["test"]["file_path"], "test.txt")

    def test_save_manifest(self):
        """Test saving manifest."""
        data = {
            "datasets": {"test": {"file_path": "test.txt"}},
            "metadata": {"version": "1.0", "created_at": "2023-01-01", "updated_at": "2023-01-01"}
        }
        save_manifest(data)
        self.assertTrue(self.temp_manifest_path.exists())

        with open(self.temp_manifest_path, "r") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["datasets"]["test"]["file_path"], "test.txt")

    def test_update_manifest(self):
        """Test updating manifest with a new dataset."""
        # Create a test file in the temp directory
        test_file = Path(self.test_dir.name) / "occurrence_test.csv"
        test_file.write_text("species,lat,lon\nBirdA,1.0,2.0")

        manifest = update_manifest(
            dataset_name="occurrence_test",
            file_path=test_file,
            source_url="https://gbif.org/test",
            dataset_type="occurrence"
        )

        self.assertIn("occurrence_test", manifest["datasets"])
        entry = manifest["datasets"]["occurrence_test"]
        self.assertEqual(entry["source_url"], "https://gbif.org/test")
        self.assertEqual(entry["dataset_type"], "occurrence")
        self.assertIn("checksum_sha256", entry)
        self.assertIn("file_size_bytes", entry)
        self.assertIn("download_timestamp", entry)

    def test_update_manifest_file_not_found(self):
        """Test update_manifest raises error for missing file."""
        with self.assertRaises(FileNotFoundError):
            update_manifest(
                dataset_name="missing",
                file_path=Path("/nonexistent/file.txt"),
                source_url="http://test.com"
            )

    def test_verify_dataset_success(self):
        """Test successful dataset verification."""
        test_file = Path(self.test_dir.name) / "verify_test.txt"
        test_file.write_text("Verify content")

        # First, update the manifest
        update_manifest(
            dataset_name="verify_test",
            file_path=test_file,
            source_url="http://test.com"
        )

        # Verify should pass
        self.assertTrue(verify_dataset("verify_test"))

    def test_verify_dataset_failure(self):
        """Test failed dataset verification due to corruption."""
        test_file = Path(self.test_dir.name) / "corrupt_test.txt"
        test_file.write_text("Original content")

        # Update manifest
        update_manifest(
            dataset_name="corrupt_test",
            file_path=test_file,
            source_url="http://test.com"
        )

        # Corrupt the file
        test_file.write_text("Corrupted content")

        # Verify should fail
        self.assertFalse(verify_dataset("corrupt_test"))

    def test_verify_dataset_missing_file(self):
        """Test verification fails when file is missing."""
        test_file = Path(self.test_dir.name) / "missing_file.txt"
        # Don't create the file, just add entry to manifest
        manifest = load_manifest()
        manifest["datasets"]["missing_entry"] = {
            "file_path": "missing_file.txt",
            "checksum_sha256": "fake_checksum"
        }
        save_manifest(manifest)

        self.assertFalse(verify_dataset("missing_entry"))

    def test_list_datasets(self):
        """Test listing datasets."""
        # Add two datasets
        file1 = Path(self.test_dir.name) / "file1.txt"
        file1.write_text("Data 1")
        update_manifest("ds1", file1, "http://a.com")

        file2 = Path(self.test_dir.name) / "file2.txt"
        file2.write_text("Data 2")
        update_manifest("ds2", file2, "http://b.com")

        datasets = list_datasets()
        self.assertIn("ds1", datasets)
        self.assertIn("ds2", datasets)
        self.assertEqual(len(datasets), 2)
