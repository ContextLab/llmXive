import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.manifest_updater import (
    compute_file_checksum,
    check_fetch_status,
    gather_processed_checksums,
    update_manifest
)

class TestManifestUpdater(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.raw_dir = Path(self.temp_dir.name) / "raw"
        self.processed_dir = Path(self.temp_dir.name) / "processed"
        self.results_dir = Path(self.temp_dir.name) / "results"
        self.raw_dir.mkdir()
        self.processed_dir.mkdir()
        self.results_dir.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compute_file_checksum(self):
        """Test SHA256 checksum computation."""
        test_file = self.raw_dir / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = compute_file_checksum(test_file)
        # Known SHA256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        self.assertEqual(checksum, expected)

    def test_check_fetch_status_no_files(self):
        """Test fetch status when no files exist."""
        status = check_fetch_status("arxiv", self.raw_dir)
        self.assertEqual(status["status"], "failed")
        self.assertEqual(status["count"], 0)
        self.assertEqual(status["files"], [])

    def test_check_fetch_status_with_files(self):
        """Test fetch status with existing JSONL files."""
        # Create a mock arxiv file
        arxiv_file = self.raw_dir / "arxiv_2024.jsonl"
        content = '{"id": "1"}\n{"id": "2"}\n'
        arxiv_file.write_text(content)
        
        status = check_fetch_status("arxiv", self.raw_dir)
        self.assertEqual(status["status"], "success")
        self.assertEqual(status["count"], 2)
        self.assertEqual(len(status["files"]), 1)

    def test_gather_processed_checksums(self):
        """Test gathering checksums from processed directory."""
        csv_file = self.processed_dir / "data_2000_2004.csv"
        csv_file.write_text("col1,col2\n1,2\n3,4\n")
        
        checksums = gather_processed_checksums(self.processed_dir)
        self.assertIn("data_2000_2004.csv", checksums)
        self.assertTrue(len(checksums["data_2000_2004.csv"]) > 0)

    def test_update_manifest_creates_file(self):
        """Test that update_manifest creates the manifest file if it doesn't exist."""
        manifest_path = self.results_dir / "manifest.json"
        
        arxiv_status = {"status": "success", "count": 10}
        pubmed_status = {"status": "failed", "count": 0}
        processed_checksums = {"test.csv": "abc123"}
        
        update_manifest(manifest_path, arxiv_status, pubmed_status, processed_checksums, self.raw_dir, self.processed_dir)
        
        self.assertTrue(manifest_path.exists())
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        self.assertEqual(manifest["data"]["arxiv_fetch_status"]["count"], 10)
        self.assertEqual(manifest["data"]["pubmed_fetch_status"]["count"], 0)
        self.assertIn("test.csv", manifest["data"]["processed_file_checksums"])

    def test_update_manifest_updates_existing(self):
        """Test that update_manifest updates an existing manifest."""
        manifest_path = self.results_dir / "manifest.json"
        
        # Create initial manifest
        initial_manifest = {"pipeline_version": "0.1.0", "data": {"old_key": "old_value"}}
        with open(manifest_path, 'w') as f:
            json.dump(initial_manifest, f)
        
        arxiv_status = {"status": "success", "count": 5}
        pubmed_status = {"status": "success", "count": 5}
        processed_checksums = {}
        
        update_manifest(manifest_path, arxiv_status, pubmed_status, processed_checksums, self.raw_dir, self.processed_dir)
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        self.assertEqual(manifest["pipeline_version"], "0.1.0") # Should preserve old data
        self.assertEqual(manifest["data"]["arxiv_fetch_status"]["count"], 5)
        self.assertEqual(manifest["data"]["old_key"], "old_value") # Should preserve old data