"""
Unit tests for dataset loaders.

These tests verify the structure and error handling of the loaders
without actually loading real data (using mocks).
"""
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from pipeline.loader import (
    load_openwebtext,
    load_gsm8k,
    load_arc_challenge,
    load_wikitext2,
    load_all_datasets,
    exponential_backoff
)

class TestDatasetLoaders(unittest.TestCase):
    
    def test_exponential_backoff_decorator(self):
        """Test that the exponential backoff decorator is properly defined."""
        @exponential_backoff(initial_delay=0.1, max_retries=2)
        def failing_function():
            raise ValueError("Simulated failure")
        
        with self.assertRaises(RuntimeError):
            failing_function()
    
    @patch('pipeline.loader.load_dataset')
    def test_load_openwebtext_success(self, mock_load_dataset):
        """Test successful loading of OpenWebText."""
        # Mock the dataset object
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(side_effect=lambda x: f"split_{x}")
        mock_load_dataset.return_value = mock_dataset
        
        result = load_openwebtext()
        
        self.assertIn("train", result)
        self.assertIn("test", result)
        mock_load_dataset.assert_called_once_with(
            "openwebtext", 
            split=["train", "test"], 
            streaming=True
        )
    
    @patch('pipeline.loader.load_dataset')
    def test_load_gsm8k_success(self, mock_load_dataset):
        """Test successful loading of GSM8K."""
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(side_effect=lambda x: f"split_{x}")
        mock_load_dataset.return_value = mock_dataset
        
        result = load_gsm8k()
        
        self.assertIn("train", result)
        self.assertIn("test", result)
        mock_load_dataset.assert_called_once_with(
            "gsm8k", "main", 
            split=["train", "test"], 
            streaming=True
        )
    
    @patch('pipeline.loader.load_dataset')
    def test_load_arc_challenge_success(self, mock_load_dataset):
        """Test successful loading of ARC-Challenge."""
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(side_effect=lambda x: f"split_{x}")
        mock_load_dataset.return_value = mock_dataset
        
        result = load_arc_challenge()
        
        self.assertIn("train", result)
        self.assertIn("test", result)
        mock_load_dataset.assert_called_once_with(
            "ai2_arc", "ARC-Challenge", 
            split=["train", "test"], 
            streaming=True
        )
    
    @patch('pipeline.loader.load_dataset')
    def test_load_wikitext2_success(self, mock_load_dataset):
        """Test successful loading of Wikitext-2."""
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(side_effect=lambda x: f"split_{x}")
        mock_load_dataset.return_value = mock_dataset
        
        result = load_wikitext2()
        
        self.assertIn("train", result)
        self.assertIn("test", result)
        mock_load_dataset.assert_called_once_with(
            "wikitext", "wikitext-2-raw-v1", 
            split=["train", "test"], 
            streaming=True
        )
    
    @patch('pipeline.loader.load_dataset')
    def test_load_all_datasets(self, mock_load_dataset):
        """Test loading all datasets."""
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(side_effect=lambda x: f"split_{x}")
        mock_load_dataset.return_value = mock_dataset
        
        result = load_all_datasets()
        
        self.assertIn("openwebtext", result)
        self.assertIn("gsm8k", result)
        self.assertIn("arc_challenge", result)
        self.assertIn("wikitext2", result)
        
        # Should be called 4 times
        self.assertEqual(mock_load_dataset.call_count, 4)
    
    @patch('pipeline.loader.load_dataset')
    def test_load_openwebtext_failure(self, mock_load_dataset):
        """Test that load_openwebtext fails fast on error."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        with self.assertRaises(RuntimeError):
            load_openwebtext()
    
    @patch('pipeline.loader.load_dataset')
    def test_load_gsm8k_failure(self, mock_load_dataset):
        """Test that load_gsm8k fails fast on error."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        with self.assertRaises(RuntimeError):
            load_gsm8k()

if __name__ == '__main__':
    unittest.main()