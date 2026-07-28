"""
Unit tests for dataset loaders in pipeline/loader.py.
Verifies fail-fast logic for missing datasets.
"""
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os

# Add code directory to path if running from tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.loader import load_openwebtext, load_gsm8k, load_arc_challenge, load_wikitext2
from datasets import Dataset

class TestDatasetLoaders(unittest.TestCase):
    
    @patch('pipeline.loader.load_dataset')
    def test_load_openwebtext_success(self, mock_load):
        """Test successful loading of OpenWebText."""
        mock_ds = MagicMock(spec=Dataset)
        mock_load.return_value = mock_ds
        
        result = load_openwebtext()
        mock_load.assert_called_once_with("openwebtext", split="train", streaming=True)
        self.assertEqual(result, mock_ds)

    @patch('pipeline.loader.load_dataset')
    def test_load_gsm8k_success(self, mock_load):
        """Test successful loading of GSM8K."""
        mock_ds = MagicMock(spec=Dataset)
        mock_load.return_value = mock_ds
        
        result = load_gsm8k()
        mock_load.assert_called_once_with("gsm8k", "main", split="train", streaming=True)
        self.assertEqual(result, mock_ds)

    @patch('pipeline.loader.load_dataset')
    def test_load_arc_challenge_success(self, mock_load):
        """Test successful loading of ARC-Challenge."""
        mock_ds = MagicMock(spec=Dataset)
        mock_load.return_value = mock_ds
        
        result = load_arc_challenge()
        mock_load.assert_called_once_with("ai2_arc", "ARC-Challenge", split="train", streaming=True)
        self.assertEqual(result, mock_ds)

    @patch('pipeline.loader.load_dataset')
    def test_load_wikitext2_success(self, mock_load):
        """Test successful loading of Wikitext-2."""
        mock_ds = MagicMock(spec=Dataset)
        mock_load.return_value = mock_ds
        
        result = load_wikitext2()
        mock_load.assert_called_once_with("wikitext", "wikitext-2-raw-v1", split="train", streaming=True)
        self.assertEqual(result, mock_ds)

    @patch('pipeline.loader.load_dataset')
    def test_load_openwebtext_missing_file_fails_fast(self, mock_load):
        """
        Test that loading a non-existent dataset raises FileNotFoundError immediately.
        Does NOT fallback to synthetic data or retry indefinitely.
        """
        mock_load.side_effect = FileNotFoundError("Dataset not found")
        
        with self.assertRaises(FileNotFoundError) as context:
            load_openwebtext()
        
        self.assertIn("not found", str(context.exception).lower())
        # Verify no synthetic data generation occurred (just checking the exception is raised)

    @patch('pipeline.loader.load_dataset')
    def test_load_gsm8k_missing_file_fails_fast(self, mock_load):
        """Test fail-fast for GSM8K."""
        mock_load.side_effect = FileNotFoundError("Dataset not found")
        
        with self.assertRaises(FileNotFoundError):
            load_gsm8k()

    @patch('pipeline.loader.load_dataset')
    def test_load_arc_missing_file_fails_fast(self, mock_load):
        """Test fail-fast for ARC-Challenge."""
        mock_load.side_effect = FileNotFoundError("Dataset not found")
        
        with self.assertRaises(FileNotFoundError):
            load_arc_challenge()

    @patch('pipeline.loader.load_dataset')
    def test_load_wikitext_missing_file_fails_fast(self, mock_load):
        """Test fail-fast for Wikitext-2."""
        mock_load.side_effect = FileNotFoundError("Dataset not found")
        
        with self.assertRaises(FileNotFoundError):
            load_wikitext2()

    @patch('pipeline.loader.load_dataset')
    def test_load_network_error_retries(self, mock_load):
        """Test that transient network errors trigger retries with backoff."""
        # Simulate 2 transient errors then success
        transient_error = ConnectionError("Network error")
        mock_load.side_effect = [transient_error, transient_error, MagicMock(spec=Dataset)]
        
        result = load_openwebtext()
        
        # Should have been called 3 times (2 failures + 1 success)
        self.assertEqual(mock_load.call_count, 3)
        self.assertIsInstance(result, MagicMock)

    @patch('pipeline.loader.load_dataset')
    def test_load_max_retries_exceeded_raises(self, mock_load):
        """Test that max retries exceeded raises the last exception."""
        transient_error = ConnectionError("Network error")
        mock_load.side_effect = [transient_error] * 6  # 5 retries + 1 initial = 6 calls
        
        with self.assertRaises(ConnectionError):
            load_openwebtext()
        
        # Should have been called 6 times (1 initial + 5 retries)
        self.assertEqual(mock_load.call_count, 6)

if __name__ == '__main__':
    unittest.main()