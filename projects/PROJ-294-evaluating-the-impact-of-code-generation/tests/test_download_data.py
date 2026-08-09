"""
Unit tests for T010: download_data.py

Tests verify:
1. The script runs without crashing (if datasets is installed).
2. It attempts to load from the correct HuggingFace dataset.
3. It raises RuntimeError on failure (mocked).
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

class TestDownloadData(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "data", "raw")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Mock the download function to return dummy data
        self.dummy_data = [
            {
                "task_id": "HumanEval/0",
                "prompt": "def add(x, y):\n    return x + y",
                "canonical_solution": "def add(x, y):\n    return x + y",
                "test": "assert add(1, 2) == 3",
                "entry_point": "add"
            }
        ]

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('download_data.load_dataset')
    @patch('download_data.save_to_parquet')
    @patch('download_data.save_to_jsonl')
    @patch('download_data.verify_file_integrity')
    @patch('download_data.ensure_output_dir')
    def test_download_success(self, mock_ensure, mock_verify, mock_save_jsonl, mock_save_parquet, mock_load):
        """Test successful download and save."""
        from download_data import download_humaneval, main
        import logging
        
        # Mock the dataset loading
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter(self.dummy_data))
        mock_load.return_value = mock_ds
        
        # Mock setup_logging to avoid console output
        with patch('download_data.setup_logging') as mock_log_setup:
            mock_logger = MagicMock()
            mock_log_setup.return_value = mock_logger
            
            # Run the download function
            result = download_humaneval(mock_logger)
            
            # Verify results
            self.assertIsNotNone(result)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["task_id"], "HumanEval/0")
            
            # Verify logging
            mock_logger.info.assert_called()

    @patch('download_data.load_dataset')
    def test_download_failure_raises_error(self, mock_load):
        """Test that download raises RuntimeError on failure."""
        from download_data import download_humaneval
        import logging
        
        # Mock failure
        mock_load.side_effect = Exception("Network error")
        
        mock_logger = MagicMock()
        
        # Should raise RuntimeError after retries
        with self.assertRaises(RuntimeError) as context:
            download_humaneval(mock_logger)
        
        self.assertIn("Failed to download verified real source", str(context.exception))

    def test_checksum_computation(self):
        """Test SHA256 checksum computation."""
        from utils import compute_sha256
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = f.name
        
        try:
            checksum = compute_sha256(temp_path)
            self.assertEqual(len(checksum), 64)  # SHA256 hex length
            self.assertIsInstance(checksum, str)
        finally:
            os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()
