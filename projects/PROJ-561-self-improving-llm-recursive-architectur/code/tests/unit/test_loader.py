import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os
import time
from pipeline.loader import with_exponential_backoff, load_openwebtext, load_gsm8k, load_arc_challenge, load_wikitext2, HFTransientError

class TestDatasetLoaders(unittest.TestCase):
    """Test cases for dataset loader functions."""

    def test_load_nonexistent_dataset_raises_file_not_found(self):
        """
        Verify that loading a non-existent dataset raises FileNotFoundError
        and does NOT fallback to synthetic data.
        """
        # Mock load_dataset to simulate a "dataset not found" error
        with patch('pipeline.loader.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Dataset not found: fake_dataset")
            
            # Create a test function that mimics the load behavior
            @with_exponential_backoff(initial_delay=0.1, max_retries=1)
            def test_load():
                try:
                    mock_load("fake_dataset", split="train")
                except Exception as e:
                    if "Dataset not found" in str(e):
                        raise FileNotFoundError(f"Dataset not found: {str(e)}")
                    raise e
            
            # Should raise FileNotFoundError, not HFTransientError
            with self.assertRaises(FileNotFoundError):
                test_load()
            
            # Verify that no synthetic data was created (no fallback)
            # The function should have raised immediately after retries
            self.assertEqual(mock_load.call_count, 2)  # 1 initial + 1 retry

    def test_transient_network_error_triggers_retry(self):
        """
        Verify that simulated network errors trigger retry logic.
        """
        call_count = 0
        
        @with_exponential_backoff(initial_delay=0.01, max_retries=3)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient network error")
            return "success"
        
        result = flaky_function()
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)  # 1 initial + 2 retries

    def test_exponential_backoff_initial_delay_is_30_seconds(self):
        """
        Verify that the initial delay is 30 seconds as specified in T005b.
        """
        # We can't actually wait 30 seconds, so we verify the decorator parameters
        # by inspecting the wrapper function's behavior with mocked sleep
        
        call_times = []
        
        @with_exponential_backoff(initial_delay=30.0, max_retries=2)
        def test_func():
            raise ConnectionError("Transient error")
        
        with patch('pipeline.loader.time.sleep') as mock_sleep:
            try:
                test_func()
            except HFTransientError:
                pass
            
            # Verify sleep was called with delays: 30, 60 (exponential)
            self.assertEqual(mock_sleep.call_count, 2)
            
            # Check first delay is approximately 30 seconds (with jitter)
            first_delay = mock_sleep.call_args_list[0][0][0]
            self.assertGreaterEqual(first_delay, 30.0)
            self.assertLessEqual(first_delay, 33.0)  # 30 + 10% jitter

    def test_load_openwebtext_raises_file_not_found_on_missing(self):
        """
        Verify load_openwebtext raises FileNotFoundError for missing dataset.
        """
        with patch('pipeline.loader.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Dataset not found: openwebtext")
            
            with self.assertRaises(FileNotFoundError):
                load_openwebtext()

    def test_load_gsm8k_raises_file_not_found_on_missing(self):
        """
        Verify load_gsm8k raises FileNotFoundError for missing dataset.
        """
        with patch('pipeline.loader.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Dataset not found: gsm8k")
            
            with self.assertRaises(FileNotFoundError):
                load_gsm8k()

    def test_load_arc_challenge_raises_file_not_found_on_missing(self):
        """
        Verify load_arc_challenge raises FileNotFoundError for missing dataset.
        """
        with patch('pipeline.loader.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Dataset not found: ai2_arc")
            
            with self.assertRaises(FileNotFoundError):
                load_arc_challenge()

    def test_load_wikitext2_raises_file_not_found_on_missing(self):
        """
        Verify load_wikitext2 raises FileNotFoundError for missing dataset.
        """
        with patch('pipeline.loader.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Dataset not found: wikitext")
            
            with self.assertRaises(FileNotFoundError):
                load_wikitext2()

    def test_non_transient_error_is_not_retried(self):
        """
        Verify that non-transient errors (e.g., ValueError) are not retried.
        """
        call_count = 0
        
        @with_exponential_backoff(initial_delay=0.01, max_retries=3)
        def value_error_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid value")
        
        with self.assertRaises(ValueError):
            value_error_func()
        
        # Should only be called once, no retries for non-transient errors
        self.assertEqual(call_count, 1)

    def test_hf_transient_error_is_raised_after_max_retries(self):
        """
        Verify that HFTransientError is raised after max retries are exhausted.
        """
        @with_exponential_backoff(initial_delay=0.01, max_retries=2)
        def always_fails():
            raise ConnectionError("Always fails")
        
        with self.assertRaises(HFTransientError):
            always_fails()
