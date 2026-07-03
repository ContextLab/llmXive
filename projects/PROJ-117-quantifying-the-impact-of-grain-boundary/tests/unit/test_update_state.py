"""
tests/unit/test_update_state.py

Unit tests for code/update_state.py
"""

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.update_state import compute_sha256, scan_directory, verify_hashes


class TestComputeSha256(unittest.TestCase):
    def test_compute_sha256_on_known_content(self):
        """Test SHA-256 computation on a file with known content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello, World!")
            temp_path = Path(f.name)

        try:
            computed_hash = compute_sha256(temp_path)
            # SHA-256 of "Hello, World!"
            expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            self.assertEqual(computed_hash, expected_hash)
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_on_empty_file(self):
        """Test SHA-256 computation on an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = Path(f.name)

        try:
            computed_hash = compute_sha256(temp_path)
            # SHA-256 of empty string
            expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            self.assertEqual(computed_hash, expected_hash)
        finally:
            os.unlink(temp_path)


class TestScanDirectory(unittest.TestCase):
    def test_scan_directory_with_files(self):
        """Test scanning a directory with files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some test files
            file1 = temp_path / "file1.txt"
            file1.write_text("content1")

            file2 = temp_path / "subdir" / "file2.txt"
            file2.parent.mkdir(parents=True, exist_ok=True)
            file2.write_text("content2")

            # Mock PROJECT_ROOT to be the temp directory
            with patch('code.update_state.PROJECT_ROOT', temp_path):
                with patch('code.update_state.EXCLUDE_PATTERNS', []):
                    result = scan_directory(temp_path)

            self.assertEqual(len(result), 2)
            paths = {item['path'] for item in result}
            self.assertIn("file1.txt", paths)
            self.assertIn("subdir/file2.txt", paths)

    def test_scan_directory_with_exclusions(self):
        """Test that excluded patterns are skipped."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files including excluded ones
            (temp_path / "file.txt").write_text("content")
            (temp_path / ".gitkeep").write_text("keep")
            (temp_path / "__pycache__").mkdir(exist_ok=True)
            (temp_path / "__pycache__" / "cache.txt").write_text("cache")

            with patch('code.update_state.PROJECT_ROOT', temp_path):
                with patch('code.update_state.EXCLUDE_PATTERNS', [".gitkeep", "__pycache__"]):
                    result = scan_directory(temp_path)

            # Should only include file.txt
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['path'], "file.txt")


class TestVerifyHashes(unittest.TestCase):
    def test_verify_hashes_no_changes(self):
        """Test verification when no files have changed."""
        old_state = {
            "files": [
                {"path": "file1.txt", "hash": "abc123"},
                {"path": "file2.txt", "hash": "def456"}
            ]
        }
        new_state = {
            "files": [
                {"path": "file1.txt", "hash": "abc123"},
                {"path": "file2.txt", "hash": "def456"}
            ]
        }

        result = verify_hashes(old_state, new_state)
        self.assertTrue(result)

    def test_verify_hashes_with_changes(self):
        """Test verification when some files have changed."""
        old_state = {
            "files": [
                {"path": "file1.txt", "hash": "abc123"},
                {"path": "file2.txt", "hash": "def456"}
            ]
        }
        new_state = {
            "files": [
                {"path": "file1.txt", "hash": "changed123"},
                {"path": "file2.txt", "hash": "def456"}
            ]
        }

        result = verify_hashes(old_state, new_state)
        self.assertTrue(result)  # Function should return True even with changes

    def test_verify_hashes_new_files(self):
        """Test verification when new files are added."""
        old_state = {
            "files": [
                {"path": "file1.txt", "hash": "abc123"}
            ]
        }
        new_state = {
            "files": [
                {"path": "file1.txt", "hash": "abc123"},
                {"path": "file2.txt", "hash": "new456"}
            ]
        }

        result = verify_hashes(old_state, new_state)
        self.assertTrue(result)

    def test_verify_hashes_removed_files(self):
        """Test verification when files are removed."""
        old_state = {
            "files": [
                {"path": "file1.txt", "hash": "abc123"},
                {"path": "file2.txt", "hash": "def456"}
            ]
        }
        new_state = {
            "files": [
                {"path": "file1.txt", "hash": "abc123"}
            ]
        }

        result = verify_hashes(old_state, new_state)
        self.assertTrue(result)