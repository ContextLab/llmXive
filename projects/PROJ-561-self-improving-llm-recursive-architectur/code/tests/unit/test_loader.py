import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.loader import (
    exponential_backoff, 
    load_openwebtext, 
    load_gsm8k, 
    load_arc_challenge, 
    load_wikitext2, 
    load_all_datasets
)
from datasets import Dataset

class TestDatasetLoaders(unittest.TestCase):
    
    def setUp(self):
        # Mock the load_dataset function to avoid real network calls during unit tests
        # but verify the logic calls it correctly.
        self.patcher = patch('pipeline.loader.load_dataset')
        self.mock_load_dataset = self.patcher.start()
        
        # Create a mock dataset object
        self.mock_dataset = MagicMock(spec=Dataset)
        self.mock_load_dataset.return_value = self.mock_dataset

    def tearDown(self):
        self.patcher.stop()

    def test_load_openwebtext_calls_correct_params(self):
        """Verify load_openwebtext calls load_dataset with correct arguments."""
        result = load_openwebtext(split="train", streaming=True)
        
        self.mock_load_dataset.assert_called_once_with(
            "openwebtext", 
            split="train", 
            streaming=True
        )
        self.assertEqual(result, self.mock_dataset)

    def test_load_gsm8k_calls_correct_params(self):
        """Verify load_gsm8k calls load_dataset with correct arguments."""
        result = load_gsm8k(split="train", streaming=True)
        
        self.mock_load_dataset.assert_called_once_with(
            "gsm8k", 
            "main", 
            split="train", 
            streaming=True
        )
        self.assertEqual(result, self.mock_dataset)

    def test_load_arc_challenge_calls_correct_params(self):
        """Verify load_arc_challenge calls load_dataset with correct arguments."""
        result = load_arc_challenge(split="train", streaming=True)
        
        self.mock_load_dataset.assert_called_once_with(
            "ai2_arc", 
            "ARC-Challenge", 
            split="train", 
            streaming=True
        )
        self.assertEqual(result, self.mock_dataset)

    def test_load_wikitext2_calls_correct_params(self):
        """Verify load_wikitext2 calls load_dataset with correct arguments."""
        result = load_wikitext2(split="train", streaming=True)
        
        self.mock_load_dataset.assert_called_once_with(
            "wikitext", 
            "wikitext-2-raw-v1", 
            split="train", 
            streaming=True
        )
        self.assertEqual(result, self.mock_dataset)

    def test_load_all_datasets_aggregates_results(self):
        """Verify load_all_datasets returns a dictionary with all datasets."""
        result = load_all_datasets(streaming=True)
        
        self.assertIsInstance(result, dict)
        self.assertIn("openwebtext", result)
        self.assertIn("gsm8k", result)
        self.assertIn("arc_challenge", result)
        self.assertIn("wikitext2", result)
        
        # Verify all are the same mock (since we mocked load_dataset to return same object)
        self.assertEqual(result["openwebtext"], self.mock_dataset)
        self.assertEqual(result["gsm8k"], self.mock_dataset)
        self.assertEqual(result["arc_challenge"], self.mock_dataset)
        self.assertEqual(result["wikitext2"], self.mock_dataset)

    def test_load_all_datasets_raises_on_failure(self):
        """Verify load_all_datasets fails loudly if any dataset load fails."""
        self.mock_load_dataset.side_effect = ConnectionError("Network error")
        
        with self.assertRaises(RuntimeError) as context:
            load_all_datasets(streaming=True)
        
        self.assertIn("Failed to load one or more datasets", str(context.exception))
        # Verify no synthetic data was created (the exception is raised immediately)
        
    def test_exponential_backoff_retry_logic(self):
        """Test that the backoff decorator retries on failure."""
        call_count = 0
        
        @exponential_backoff(initial_delay=0.01, max_retries=2)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        # This should succeed after 2 retries (3 attempts total)
        result = flaky_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)

    def test_exponential_backoff_fails_after_max_retries(self):
        """Test that the backoff decorator raises after max retries."""
        call_count = 0
        
        @exponential_backoff(initial_delay=0.01, max_retries=2)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent failure")
        
        with self.assertRaises(ValueError):
            always_fails()
        
        # Should attempt 3 times (initial + 2 retries)
        self.assertEqual(call_count, 3)
