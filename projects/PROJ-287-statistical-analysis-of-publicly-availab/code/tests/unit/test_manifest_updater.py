import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import hashlib

# Add the code directory to the path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.data.manifest_updater import (
    compute_file_checksum,
    check_fetch_status,
    gather_processed_checksums,
    update_manifest
)

class TestManifestUpdater(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.raw_data_dir = Path(self.temp_dir.name) / "raw"
        self.processed_data_dir = Path(self.temp_dir.name) / "processed"
        self.results_dir = Path(self.temp_dir.name) / "results"
        
        self.raw_data_dir.mkdir()
        self.processed_data_dir.mkdir()
        self.results_dir.mkdir()
        
        # Create test files
        self.test_arxiv_file = self.raw_data_dir / "arxiv_2024.jsonl"
        self.test_pubmed_file = self.raw_data_dir / "pubmed_2024.jsonl"
        self.test_processed_file = self.processed_data_dir / "window_2000_2004.csv"
        
        with open(self.test_arxiv_file, 'w') as f:
            f.write('{"title": "Test", "abstract": "Test abstract"}\n')
        
        with open(self.test_pubmed_file, 'w') as f:
            f.write('{"title": "Test", "abstract": "Test abstract"}\n')
        
        with open(self.test_processed_file, 'w') as f:
            f.write('title,abstract\nTest,Test abstract\n')

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_compute_file_checksum(self):
        """Test SHA256 checksum computation."""
        expected_hash = hashlib.sha256(b'{"title": "Test", "abstract": "Test abstract"}\n').hexdigest()
        computed_hash = compute_file_checksum(str(self.test_arxiv_file))
        self.assertEqual(computed_hash, expected_hash)

    def test_compute_file_checksum_missing_file(self):
        """Test checksum computation for non-existent file."""
        result = compute_file_checksum("/non/existent/file.txt")
        self.assertIsNone(result)

    def test_check_fetch_status_both_exist(self):
        """Test fetch status when both files exist."""
        status = check_fetch_status(str(self.raw_data_dir))
        self.assertTrue(status["arxiv_fetch_status"])
        self.assertTrue(status["pubmed_fetch_status"])

    def test_check_fetch_status_no_files(self):
        """Test fetch status when no files exist."""
        empty_dir = Path(self.temp_dir.name) / "empty_raw"
        empty_dir.mkdir()
        status = check_fetch_status(str(empty_dir))
        self.assertFalse(status["arxiv_fetch_status"])
        self.assertFalse(status["pubmed_fetch_status"])

    def test_check_fetch_status_missing_directory(self):
        """Test fetch status when directory doesn't exist."""
        status = check_fetch_status("/non/existent/directory")
        self.assertFalse(status["arxiv_fetch_status"])
        self.assertFalse(status["pubmed_fetch_status"])

    def test_gather_processed_checksums(self):
        """Test gathering checksums for processed files."""
        checksums = gather_processed_checksums(str(self.processed_data_dir))
        self.assertIn("window_2000_2004.csv", checksums)
        self.assertEqual(len(checksums), 1)

    def test_update_manifest_creates_new(self):
        """Test updating a non-existent manifest creates a new one."""
        manifest_path = str(self.results_dir / "manifest.json")
        manifest = update_manifest(
            manifest_path,
            arxiv_status=True,
            pubmed_status=False,
            processed_checksums={"test.csv": "abc123"}
        )
        
        self.assertTrue(Path(manifest_path).exists())
        self.assertTrue(manifest["arxiv_fetch_status"])
        self.assertFalse(manifest["pubmed_fetch_status"])
        self.assertIn("processed_data_checksums", manifest)
        self.assertIn("created_at", manifest)
        self.assertIn("updated_at", manifest)

    def test_update_manifest_updates_existing(self):
        """Test updating an existing manifest preserves and updates data."""
        manifest_path = str(self.results_dir / "manifest.json")
        
        # Create initial manifest
        initial_data = {"version": "1.0", "other_field": "value"}
        with open(manifest_path, 'w') as f:
            json.dump(initial_data, f)
        
        # Update manifest
        manifest = update_manifest(
            manifest_path,
            arxiv_status=True,
            pubmed_status=True,
            processed_checksums={"test.csv": "abc123"}
        )
        
        self.assertTrue(manifest["arxiv_fetch_status"])
        self.assertTrue(manifest["pubmed_fetch_status"])
        self.assertEqual(manifest["version"], "1.0")
        self.assertEqual(manifest["other_field"], "value")

if __name__ == "__main__":
    unittest.main()