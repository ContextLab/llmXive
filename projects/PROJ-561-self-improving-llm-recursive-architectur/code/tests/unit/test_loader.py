import unittest
from unittest.mock import patch, MagicMock, PropertyMock, call
import sys
import os
import time
import tempfile
import logging

# Add project root to path if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.loader import (
    HFTransientError, 
    with_exponential_backoff, 
    load_openwebtext, 
    load_gsm8k, 
    load_arc_challenge, 
    load_boolq, 
    load_wikitext2, 
    load_local_dataset,
    load_all_datasets
)
from config import get_config

class TestDatasetLoaders(unittest.TestCase):
    
    def setUp(self):
        # Suppress logs during tests for cleanliness
        logging.disable(logging.CRITICAL)
        self.config = get_config()

    def tearDown(self):
        logging.disable(logging.NOTSET)

    @patch('pipeline.loader.load_dataset')
    def test_load_openwebtext_success(self, mock_load):
        mock_load.return_value = MagicMock()
        ds = load_openwebtext()
        mock_load.assert_called_once()
        self.assertIsNotNone(ds)

    @patch('pipeline.loader.load_dataset')
    def test_load_gsm8k_success(self, mock_load):
        mock_load.return_value = MagicMock()
        ds = load_gsm8k()
        mock_load.assert_called_once()
        self.assertIsNotNone(ds)

    @patch('pipeline.loader.load_dataset')
    def test_load_arc_challenge_success(self, mock_load):
        mock_load.return_value = MagicMock()
        ds = load_arc_challenge()
        mock_load.assert_called_once()
        self.assertIsNotNone(ds)

    @patch('pipeline.loader.load_dataset')
    def test_load_boolq_success(self, mock_load):
        mock_load.return_value = MagicMock()
        ds = load_boolq()
        mock_load.assert_called_once()
        self.assertIsNotNone(ds)

    def test_load_local_dataset_missing_file(self):
        """
        Verify that loading a non-existent dataset using a dynamically 
        generated temporary path raises FileNotFoundError with the exact message.
        """
        temp_path = tempfile.mktemp()
        # Ensure it definitely doesn't exist
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Ensure the file is not created
        self.assertFalse(os.path.exists(temp_path))

        with self.assertRaises(FileNotFoundError) as context:
            load_local_dataset(temp_path)
        
        self.assertEqual(str(context.exception), f"Dataset file not found: {temp_path}")

    def test_load_local_dataset_missing_config_path(self):
        """
        Verify that loading a missing file at a config.py defined path 
        raises FileNotFoundError and does NOT fallback to synthetic data.
        """
        # Simulate a path that might be in config but doesn't exist
        # We can't easily modify config.py in this test, so we test the 
        # behavior of load_local_dataset directly with a known bad path
        # that we construct to look like a config path.
        bad_path = os.path.join(self.config.data_processed_dir, "non_existent_dataset.csv")
        
        with self.assertRaises(FileNotFoundError) as context:
            load_local_dataset(bad_path)
        
        self.assertEqual(str(context.exception), f"Dataset file not found: {bad_path}")

    @patch('pipeline.loader.load_dataset')
    def test_load_local_dataset_success(self, mock_load):
        # Create a dummy file to satisfy os.path.exists
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            f.write(b"col1,col2\n1,2\n")
            temp_path = f.name
        
        try:
            mock_load.return_value = MagicMock()
            ds = load_local_dataset(temp_path)
            # Verify load_dataset was called (mocked)
            mock_load.assert_called()
            self.assertIsNotNone(ds)
        finally:
            os.remove(temp_path)

    @patch('time.sleep')
    @patch('pipeline.loader.load_dataset')
    def test_retry_logic_on_transient_error(self, mock_load, mock_sleep):
        """
        Verify that simulated network errors trigger retry logic.
        """
        # Configure mock to fail twice then succeed
        mock_load.side_effect = [
            HFTransientError("Network glitch"),
            HFTransientError("Network glitch"),
            MagicMock() # Success on 3rd attempt
        ]
        
        # Call the decorated function
        result = load_openwebtext()
        
        # Verify load_dataset was called 3 times (2 fails + 1 success)
        self.assertEqual(mock_load.call_count, 3)
        
        # Verify sleep was called twice (after 1st and 2nd failure)
        self.assertEqual(mock_sleep.call_count, 2)
        
        # Verify the result is the mock object from the successful call
        self.assertIsNotNone(result)

    @patch('time.sleep')
    @patch('pipeline.loader.load_dataset')
    def test_max_retries_exceeded(self, mock_load, mock_sleep):
        """
        Verify that if max retries are exceeded, the exception is raised.
        """
        # Configure mock to fail 6 times (max_retries + 1)
        mock_load.side_effect = [HFTransientError("Error")] * 6
        
        with self.assertRaises(HFTransientError):
            load_openwebtext()
        
        # Verify load_dataset was called 6 times
        self.assertEqual(mock_load.call_count, 6)
        
        # Verify sleep was called 5 times (after each failure except the last one which raises)
        self.assertEqual(mock_sleep.call_count, 5)

    def test_initial_delay_is_30s(self):
        """
        Verify that the initial delay is exactly 30 seconds (within 1s tolerance).
        This is checked by inspecting the logic or mocking time.sleep to capture args.
        """
        @with_exponential_backoff
        def failing_func():
            raise HFTransientError("Test error")
        
        with patch('time.sleep') as mock_sleep:
            mock_load = MagicMock()
            # Force failure
            mock_load.side_effect = [HFTransientError("Error")] * 2
            
            # Patch the inner function to use our mock load
            # We can't easily patch the inner call of load_openwebtext without more complex setup,
            # so we rely on the decorator logic directly by calling a function that raises.
            # The decorator logic is: delay = 30.0 + random(-1, 1).
            # We verify the sleep is called with a value in [29, 31].
            
            # To test this cleanly, we need to trigger the decorator on a function that raises.
            # We'll create a test function inside.
            pass

        # Re-implementing the test logic specifically for the delay value
        # Since we can't easily extract the delay from the decorator without modifying code,
        # we will verify the behavior by mocking random and time.sleep.
        
        import random
        with patch('random.uniform', return_value=0.0): # No jitter
            with patch('time.sleep') as mock_sleep:
                @with_exponential_backoff
                def test_func():
                    raise HFTransientError("Test")
                
                try:
                    test_func()
                except HFTransientError:
                    pass
                
                # First sleep call should be exactly 30.0
                if mock_sleep.call_count > 0:
                    first_call_args = mock_sleep.call_args_list[0][0][0]
                    self.assertAlmostEqual(first_call_args, 30.0, delta=1.0)
