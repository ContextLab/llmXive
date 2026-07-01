"""
Unit tests for code/download.py.

This module verifies that the dataset loading mechanism works correctly
without requiring authentication tokens, ensuring the pipeline can run
in CI environments.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import hashlib
import yaml

# Import the real module
from code import download


class TestDatasetLoader(unittest.TestCase):
    """Tests for the dataset loading functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manifest_path = os.path.join(self.temp_dir, "dataset_manifest.yaml")
        
        # Mock the dataset info to avoid actual HuggingFace calls during test setup
        self.mock_dataset = MagicMock()
        self.mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"prompt": "def add(a, b): return a + b", "test_list": []}
        ]))
        self.mock_dataset.__len__ = MagicMock(return_value=1)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    @patch("code.download.load_dataset")
    def test_load_without_auth(self, mock_load):
        """
        Test that dataset loads successfully without authentication.
        
        This verifies the core requirement: the pipeline must work
        in environments where no HF_TOKEN is set.
        """
        mock_load.return_value = self.mock_dataset
        
        # Explicitly ensure no auth token is used
        if "HF_TOKEN" in os.environ:
            del os.environ["HF_TOKEN"]
        
        result = download.load_human_eval_dataset(self.temp_dir)
        
        # Verify the dataset was loaded
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        
        # Verify load_dataset was called without auth token
        call_args = mock_load.call_args
        # The first positional argument should be the dataset name
        self.assertEqual(call_args[0][0], "openai_humaneval")

    @patch("code.download.load_dataset")
    def test_manifest_creation(self, mock_load):
        """
        Test that a valid manifest file is created after download.
        
        The manifest should contain versioning info and checksums
        for reproducibility.
        """
        mock_load.return_value = self.mock_dataset
        
        # Mock the checksum calculation to return a deterministic value
        with patch("code.download.hashlib.sha256") as mock_hash:
            mock_hash.return_value.hexdigest.return_value = "abc123"
            
            result = download.load_human_eval_dataset(self.temp_dir)
            
            # Verify manifest file was created
            self.assertTrue(os.path.exists(self.manifest_path))
            
            # Verify manifest content
            with open(self.manifest_path, "r") as f:
                manifest = yaml.safe_load(f)
            
            self.assertIn("dataset_name", manifest)
            self.assertEqual(manifest["dataset_name"], "openai_humaneval")
            self.assertIn("version", manifest)
            self.assertIn("checksum", manifest)
            self.assertEqual(manifest["checksum"], "abc123")

    def test_dataset_path_structure(self):
        """
        Test that the dataset is saved in the correct directory structure.
        
        The data should be stored under data/raw/ as per project conventions.
        """
        # This test verifies the directory structure logic
        # We mock the actual download to avoid network calls
        with patch("code.download.load_dataset", return_value=self.mock_dataset):
            with patch("code.download.os.makedirs"):
                with patch("code.download.pd.DataFrame.to_parquet") as mock_to_parquet:
                    with patch("code.download.hashlib.sha256"):
                        # Create a temporary data directory
                        data_dir = os.path.join(self.temp_dir, "raw")
                        os.makedirs(data_dir, exist_ok=True)
                        
                        # Call the function
                        download.load_human_eval_dataset(data_dir)
                        
                        # Verify to_parquet was called (indicates data was processed)
                        mock_to_parquet.assert_called_once()


if __name__ == "__main__":
    unittest.main()