"""
Unit tests for code/utils/update_state.py
"""
import os
import sys
import tempfile
import shutil
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import code.utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.utils.update_state import calculate_sha256, scan_directory, PROJECT_ROOT, DATA_DIR

class TestUpdateStateUtils(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir) / "data"
        self.test_data_dir.mkdir()

        # Create some dummy files
        (self.test_data_dir / "file1.txt").write_text("hello world")
        (self.test_data_dir / "subdir").mkdir()
        (self.test_data_dir / "subdir" / "file2.txt").write_text("test content")

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_calculate_sha256(self):
        """Test SHA-256 calculation."""
        file_path = Path(self.temp_dir) / "data" / "file1.txt"
        expected_hash = hashlib.sha256(b"hello world").hexdigest()
        self.assertEqual(calculate_sha256(file_path), expected_hash)

    def test_scan_directory_existing(self):
        """Test scanning an existing directory with files."""
        scan_result = scan_directory(self.test_data_dir)
        self.assertEqual(scan_result["status"], "ok")
        self.assertEqual(scan_result["total_files"], 2)
        self.assertEqual(len(scan_result["files"]), 2)

        # Check if files are listed
        paths = [f["path"] for f in scan_result["files"]]
        self.assertIn("file1.txt", paths)
        self.assertIn("subdir/file2.txt", paths)

    def test_scan_directory_empty(self):
        """Test scanning an empty directory."""
        empty_dir = Path(self.temp_dir) / "empty"
        empty_dir.mkdir()
        scan_result = scan_directory(empty_dir)
        self.assertEqual(scan_result["status"], "empty")
        self.assertEqual(scan_result["total_files"], 0)

    def test_scan_directory_missing(self):
        """Test scanning a non-existent directory."""
        missing_path = Path(self.temp_dir) / "non_existent"
        scan_result = scan_directory(missing_path)
        self.assertEqual(scan_result["status"], "missing")
        self.assertEqual(scan_result["total_files"], 0)

if __name__ == "__main__":
    unittest.main()