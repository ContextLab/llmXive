"""
Unit tests for dataset loaders in pipeline.loader.
Tests verify that loaders attempt to fetch real data and fail fast if unavailable.
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from pipeline.loader import load_openwebtext, load_gsm8k, load_arc_challenge, load_wikitext2, load_all_datasets

class TestDatasetLoaders(unittest.TestCase):
    
    @patch('pipeline.loader.load_dataset')
    def test_load_openwebtext_success(self, mock_load_dataset):
        """Test successful loading of OpenWebText."""
        mock_ds = MagicMock()
        mock_ds.__len__ = MagicMock(return_value=100)
        mock_ds.select = MagicMock(return_value=mock_ds)
        mock_load_dataset.return_value = mock_ds
        
        result = load_openwebtext(max_samples=10)
        
        self.assertIn("train", result)
        self.assertEqual(len(result["train"]), 100)
        mock_load_dataset.assert_called_once()
        
    @patch('pipeline.loader.load_dataset')
    def test_load_openwebtext_failure_fail_fast(self, mock_load_dataset):
        """Test that OpenWebText loader raises RuntimeError on failure (Fail-Fast)."""
        mock_load_dataset.side_effect = Exception("Connection refused")
        
        with self.assertRaises(RuntimeError) as context:
            load_openwebtext()
        
        self.assertIn("Failed to load OpenWebText", str(context.exception))
        
    @patch('pipeline.loader.load_dataset')
    def test_load_gsm8k_success(self, mock_load_dataset):
        """Test successful loading of GSM8K."""
        mock_ds = MagicMock()
        mock_ds.__len__ = MagicMock(return_value=50)
        mock_ds.select = MagicMock(return_value=mock_ds)
        mock_load_dataset.return_value = mock_ds
        
        result = load_gsm8k(max_samples=5)
        
        self.assertIn("train", result)
        mock_load_dataset.assert_called_once()

    @patch('pipeline.loader.load_dataset')
    def test_load_arc_challenge_success(self, mock_load_dataset):
        """Test successful loading of ARC-Challenge."""
        mock_ds = MagicMock()
        mock_ds.__len__ = MagicMock(return_value=200)
        mock_ds.select = MagicMock(return_value=mock_ds)
        mock_load_dataset.return_value = mock_ds
        
        result = load_arc_challenge(max_samples=20)
        
        self.assertIn("train", result)
        # Verify subset argument is passed correctly
        call_args = mock_load_dataset.call_args
        self.assertEqual(call_args.kwargs['subset'], 'ARC-Challenge')

    @patch('pipeline.loader.load_dataset')
    def test_load_wikitext2_success(self, mock_load_dataset):
        """Test successful loading of WikiText-2."""
        mock_ds = MagicMock()
        mock_ds.__len__ = MagicMock(return_value=1000)
        mock_ds.select = MagicMock(return_value=mock_ds)
        mock_load_dataset.return_value = mock_ds
        
        result = load_wikitext2(max_samples=100)
        
        self.assertIn("train", result)
        # Verify subset argument
        call_args = mock_load_dataset.call_args
        self.assertEqual(call_args.kwargs['subset'], 'wikitext-2-raw-v1')

    @patch('pipeline.loader.load_dataset')
    def test_load_all_datasets_fail_fast(self, mock_load_dataset):
        """Test that load_all_datasets fails immediately if one dataset fails."""
        # First call succeeds, second call fails
        mock_ds = MagicMock()
        mock_ds.__len__ = MagicMock(return_value=10)
        mock_ds.select = MagicMock(return_value=mock_ds)
        
        def side_effect(*args, **kwargs):
            if args[0] == "gsm8k":
                raise Exception("GSM8K Unavailable")
            return mock_ds
        
        mock_load_dataset.side_effect = side_effect
        
        with self.assertRaises(RuntimeError) as context:
            load_all_datasets(max_samples_per_dataset=1)
        
        self.assertIn("Critical failure loading gsm8k", str(context.exception))

if __name__ == '__main__':
    unittest.main()