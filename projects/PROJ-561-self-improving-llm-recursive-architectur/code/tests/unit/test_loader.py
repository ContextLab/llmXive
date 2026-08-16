import unittest
from unittest.mock import patch, MagicMock, PropertyMock, call
import sys
import os
import time
import tempfile
from huggingface_hub import HfHubHTTPError
from requests import Response

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.loader import (
    HFTransientError, 
    exponential_backoff_retry, 
    load_local_dataset, 
    load_openwebtext,
    load_gsm8k,
    load_arc_challenge,
    load_boolq
)
from config import get_config

class TestDatasetLoaders(unittest.TestCase):

    def test_load_local_dataset_missing_file_raises_file_not_found(self):
        """
        Verify that loading a non-existent dataset using a dynamically generated 
        temporary path raises FileNotFoundError with the exact message.
        """
        temp_path = tempfile.mktemp(suffix=".json")
        # Ensure the file does not exist
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        with self.assertRaises(FileNotFoundError) as context:
            load_local_dataset(temp_path)
        
        self.assertIn("Dataset file not found:", str(context.exception))
        self.assertIn(temp_path, str(context.exception))

    @patch('config.get_config')
    def test_load_all_datasets_missing_config_path_raises_file_not_found(self, mock_get_config):
        """
        Verify that loading a missing file at a config.py defined path raises 
        FileNotFoundError and does NOT fallback to synthetic data.
        """
        # Mock config to return a path that doesn't exist
        mock_config = MagicMock()
        mock_config.openwebtext_path = tempfile.mktemp(suffix=".json")
        mock_config.gsm8k_path = tempfile.mktemp(suffix=".json")
        mock_config.arc_challenge_path = tempfile.mktemp(suffix=".json")
        mock_config.boolq_path = tempfile.mktemp(suffix=".json")
        mock_get_config.return_value = mock_config
        
        # Ensure paths don't exist
        for path in [mock_config.openwebtext_path, mock_config.gsm8k_path, 
                     mock_config.arc_challenge_path, mock_config.boolq_path]:
            if os.path.exists(path):
                os.remove(path)

        with self.assertRaises(FileNotFoundError) as context:
            # We need to import inside or reload to pick up the mocked config
            # But since load_all_datasets calls get_config internally, we just call it
            from pipeline.loader import load_all_datasets
            load_all_datasets()
        
        self.assertIn("Dataset file not found:", str(context.exception))

    @patch('pipeline.loader.load_dataset')
    @patch('pipeline.loader.time.sleep')
    def test_hf_hub_http_error_triggers_retry_logic(self, mock_sleep, mock_load_dataset):
        """
        Verify that simulating HfHubHTTPError (from huggingface_hub) triggers 
        the retry logic from T005b.
        """
        # Create a mock response object for HfHubHTTPError
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 503 # Service Unavailable
        
        error = HfHubHTTPError("Server Error", response=mock_response)
        
        # Configure the mock to fail 3 times, then succeed
        mock_load_dataset.side_effect = [error, error, error, MagicMock()]
        
        # Call the decorated function
        result = load_openwebtext()
        
        # Assert that load_dataset was called 4 times (3 failures + 1 success)
        self.assertEqual(mock_load_dataset.call_count, 4)
        
        # Assert that time.sleep was called 3 times (after each failure)
        self.assertEqual(mock_sleep.call_count, 3)

    @patch('pipeline.loader.load_dataset')
    @patch('pipeline.loader.time.sleep')
    def test_429_error_triggers_retry_logic(self, mock_sleep, mock_load_dataset):
        """
        Verify that simulating a 429 (Too Many Requests) error triggers the retry logic.
        """
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 429
        
        error = HfHubHTTPError("Rate Limit", response=mock_response)
        
        mock_load_dataset.side_effect = [error, MagicMock()]
        
        result = load_openwebtext()
        
        # Assert that load_dataset was called 2 times (1 failure + 1 success)
        self.assertEqual(mock_load_dataset.call_count, 2)
        
        # Assert that time.sleep was called 1 time
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('pipeline.loader.load_dataset')
    @patch('pipeline.loader.time.sleep')
    def test_non_transient_error_raises_immediately(self, mock_sleep, mock_load_dataset):
        """
        Verify that a non-transient error (e.g., 404) raises immediately without retry.
        """
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 404 # Not Found
        
        error = HfHubHTTPError("Not Found", response=mock_response)
        
        mock_load_dataset.side_effect = error
        
        with self.assertRaises(HfHubHTTPError):
            load_openwebtext()
        
        # Assert that load_dataset was called only once
        self.assertEqual(mock_load_dataset.call_count, 1)
        
        # Assert that time.sleep was never called
        self.assertEqual(mock_sleep.call_count, 0)

    @patch('pipeline.loader.load_dataset')
    def test_load_gsm8k_calls_hf_correctly(self, mock_load_dataset):
        """Verify GSM8K loader calls HuggingFace with correct parameters."""
        mock_ds = MagicMock()
        mock_load_dataset.return_value = mock_ds
        
        result = load_gsm8k()
        
        mock_load_dataset.assert_called_once_with("gsm8k", "main", split="test", streaming=True)
        self.assertEqual(result, mock_ds)

    @patch('pipeline.loader.load_dataset')
    def test_load_arc_challenge_calls_hf_correctly(self, mock_load_dataset):
        """Verify ARC-Challenge loader calls HuggingFace with correct parameters."""
        mock_ds = MagicMock()
        mock_load_dataset.return_value = mock_ds
        
        result = load_arc_challenge()
        
        mock_load_dataset.assert_called_once_with("ai2_arc", "ARC-Challenge", split="test", streaming=True)
        self.assertEqual(result, mock_ds)

    @patch('pipeline.loader.load_dataset')
    def test_load_boolq_calls_hf_correctly(self, mock_load_dataset):
        """Verify BoolQ loader calls HuggingFace with correct parameters."""
        mock_ds = MagicMock()
        mock_load_dataset.return_value = mock_ds
        
        result = load_boolq()
        
        mock_load_dataset.assert_called_once_with("boolq", split="validation", streaming=True)
        self.assertEqual(result, mock_ds)