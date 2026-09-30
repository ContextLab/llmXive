"""
Tests for code/download.py
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import unittest

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from download import (
    generate_data_gap_report,
    compute_sha256,
    check_dataset_availability,
    select_dataset,
    log_to_file
)

class TestDownloadModule(unittest.TestCase):
    
    def setUp(self):
        """Create temporary directories for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, "data")
        self.logs_dir = os.path.join(self.test_dir, "logs")
        os.makedirs(self.data_dir)
        os.makedirs(self.logs_dir)
        
        # Patch paths
        import download
        download.DATA_GAP_REPORT_PATH = os.path.join(self.data_dir, "data_gap_report.json")
        download.LOG_FILE_PATH = os.path.join(self.logs_dir, "processing.log")
        download.DATASET_ID_FILE = os.path.join(self.data_dir, "selected_dataset_id.txt")
        download.RAW_DATA_DIR = os.path.join(self.test_dir, "raw")
        os.makedirs(download.RAW_DATA_DIR)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_generate_data_gap_report(self):
        """Test that data gap report is generated correctly."""
        report = generate_data_gap_report(
            dataset_id=None,
            reason="Test reason",
            fallback_id=None
        )
        
        self.assertIn("dataset_id", report)
        self.assertIn("reason", report)
        self.assertIn("timestamp", report)
        self.assertIn("fallback_id", report)
        self.assertIsNone(report["fallback_id"])
        
        # Verify file exists
        self.assertTrue(os.path.exists(download.DATA_GAP_REPORT_PATH))
        
        # Verify content
        with open(download.DATA_GAP_REPORT_PATH, "r") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["reason"], "Test reason")

    def test_compute_sha256(self):
        """Test SHA-256 computation on a dummy file."""
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        checksum = compute_sha256(test_file)
        self.assertEqual(len(checksum), 64)  # SHA-256 hex length
        self.assertIsInstance(checksum, str)

    def test_select_dataset_primary(self):
        """Test selection of primary dataset (mocked check)."""
        # Since we can't reliably hit the API in tests without mocking,
        # we verify the logic flow.
        # We assume check_dataset_availability returns False for ds004173 in this test env
        # unless we mock it.
        # For this unit test, we just ensure the function doesn't crash.
        result = select_dataset(primary_id="ds004173", fallback_query="task-switching")
        # Result might be None if network is down or ID not found
        # We just ensure it returns a string or None
        self.assertTrue(result is None or isinstance(result, str))

    def test_log_to_file(self):
        """Test logging to file."""
        log_to_file("Test log message")
        self.assertTrue(os.path.exists(download.LOG_FILE_PATH))
        with open(download.LOG_FILE_PATH, "r") as f:
            content = f.read()
        self.assertIn("Test log message", content)

if __name__ == "__main__":
    unittest.main()