"""
Unit tests for download_guild_source.py
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.download_guild_source import download_file, compute_sha256, save_metadata, main
from utils.config import get_raw_data_dir

class TestDownloadGuildSource(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_raw_dir = get_raw_data_dir()
        # Mock the get_raw_data_dir to return our temp directory
        # We cannot easily mock the function, so we will test the logic directly
        # by creating a mock file path.

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('data.download_guild_source.requests.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download."""
        mock_response = MagicMock()
        mock_response.content = b"species_id,foraging_guild\ntest_species,forager"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        test_file = Path(self.temp_dir) / "test.csv"
        result = download_file("http://example.com/test.csv", test_file)

        self.assertTrue(result)
        self.assertTrue(test_file.exists())
        self.assertEqual(test_file.read_bytes(), b"species_id,foraging_guild\ntest_species,forager")

    @patch('data.download_guild_source.requests.get')
    def test_download_file_failure(self, mock_get):
        """Test failed file download."""
        mock_get.side_effect = Exception("Network error")

        test_file = Path(self.temp_dir) / "test_fail.csv"
        result = download_file("http://example.com/fail.csv", test_file)

        self.assertFalse(result)
        self.assertFalse(test_file.exists())

    def test_compute_sha256(self):
        """Test SHA256 hash computation."""
        test_file = Path(self.temp_dir) / "hash_test.txt"
        test_content = b"hello world"
        test_file.write_bytes(test_content)

        hash_value = compute_sha256(test_file)
        # Expected hash for "hello world"
        expected_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        self.assertEqual(hash_value, expected_hash)

    def test_save_metadata(self):
        """Test metadata saving."""
        test_file = Path(self.temp_dir) / "test.csv"
        test_file.write_text("test")
        metadata_file = Path(self.temp_dir) / "metadata.yaml"

        save_metadata(test_file, "http://example.com", "abc123")

        self.assertTrue(metadata_file.exists())
        with open(metadata_file, 'r') as f:
            metadata = yaml.safe_load(f)
        
        self.assertIn("guild_source", metadata)
        self.assertEqual(metadata["guild_source"]["source"], "http://example.com")
        self.assertEqual(metadata["guild_source"]["hash"], "abc123")

    @patch('data.download_guild_source.download_file')
    @patch('data.download_guild_source.compute_sha256')
    @patch('data.download_guild_source.save_metadata')
    def test_main_success(self, mock_save_meta, mock_compute_hash, mock_download):
        """Test main function success path."""
        mock_download.return_value = True
        mock_compute_hash.return_value = "hash123"
        
        # Mock get_raw_data_dir to return a temp directory
        with patch('data.download_guild_source.get_raw_data_dir', return_value=Path(self.temp_dir)):
            main()
        
        mock_download.assert_called_once()
        mock_compute_hash.assert_called_once()
        mock_save_meta.assert_called_once()

    @patch('data.download_guild_source.download_file')
    def test_main_failure(self, mock_download):
        """Test main function failure path."""
        mock_download.return_value = False
        
        with patch('data.download_guild_source.get_raw_data_dir', return_value=Path(self.temp_dir)):
            with self.assertRaises(FileNotFoundError):
                main()

if __name__ == '__main__':
    unittest.main()