"""
Unit tests for dataset loaders in pipeline.loader.
Tests verify:
- Exponential backoff behavior.
- Fail-fast logic on unreachable URLs.
- Correct function signatures and streaming flags.
"""
import unittest
from unittest.mock import patch, MagicMock, PropertyMock, call
import sys
import os
import time
import tempfile

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from pipeline.loader import (
    HFTransientError, 
    exponential_backoff, 
    verify_urls, 
    download_and_checksum,
    load_openwebtext,
    load_gsm8k,
    load_arc_challenge,
    load_boolq
)
import requests

class TestDatasetLoaders(unittest.TestCase):
    
    def setUp(self):
        self.mock_ds = MagicMock()
        self.mock_ds.__iter__ = MagicMock(return_value=iter([{"text": "test"}]))

    @patch('pipeline.loader.load_dataset')
    def test_load_openwebtext_streaming(self, mock_load_dataset):
        """Test that load_openwebtext passes streaming=True correctly."""
        mock_load_dataset.return_value = self.mock_ds
        
        result = load_openwebtext(streaming=True)
        
        mock_load_dataset.assert_called_once()
        args, kwargs = mock_load_dataset.call_args
        self.assertEqual(kwargs.get('streaming'), True)
        self.assertEqual(args[0], "OpenWebText")

    @patch('pipeline.loader.load_dataset')
    def test_load_gsm8k_streaming(self, mock_load_dataset):
        """Test that load_gsm8k passes streaming=True correctly."""
        mock_load_dataset.return_value = self.mock_ds
        
        result = load_gsm8k(streaming=True)
        
        mock_load_dataset.assert_called_once()
        args, kwargs = mock_load_dataset.call_args
        self.assertEqual(kwargs.get('streaming'), True)
        self.assertIn("gsm8k", args[0])

    @patch('pipeline.loader.load_dataset')
    def test_load_arc_challenge_streaming(self, mock_load_dataset):
        """Test that load_arc_challenge passes streaming=True correctly."""
        mock_load_dataset.return_value = self.mock_ds
        
        result = load_arc_challenge(streaming=True)
        
        mock_load_dataset.assert_called_once()
        args, kwargs = mock_load_dataset.call_args
        self.assertEqual(kwargs.get('streaming'), True)
        self.assertIn("arc", args[0].lower())

    @patch('pipeline.loader.load_dataset')
    def test_load_boolq_streaming(self, mock_load_dataset):
        """Test that load_boolq passes streaming=True correctly."""
        mock_load_dataset.return_value = self.mock_ds
        
        result = load_boolq(streaming=True)
        
        mock_load_dataset.assert_called_once()
        args, kwargs = mock_load_dataset.call_args
        self.assertEqual(kwargs.get('streaming'), True)
        self.assertEqual(args[0], "boolq")

    @patch('pipeline.loader.requests.head')
    def test_verify_urls_success(self, mock_head):
        """Test verify_urls with successful responses."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        verify_urls(["http://example.com"])
        mock_head.assert_called_once_with("http://example.com", timeout=10)

    @patch('pipeline.loader.requests.head')
    def test_verify_urls_failure(self, mock_head):
        """Test verify_urls raises ValueError on failure."""
        mock_head.side_effect = requests.exceptions.ConnectionError("Network error")
        
        with self.assertRaises(ValueError) as context:
            verify_urls(["http://broken.com"])
        
        self.assertIn("unreachable", str(context.exception))

    def test_exponential_backoff_initial_delay(self):
        """Test that exponential backoff applies delay on failure."""
        call_count = 0
        max_calls = 2
        
        @exponential_backoff
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count <= max_calls:
                raise requests.exceptions.ConnectionError("Transient error")
            return "success"
        
        start_time = time.time()
        result = failing_func()
        elapsed = time.time() - start_time
        
        # Should have retried at least once with a delay
        self.assertEqual(result, "success")
        self.assertGreater(elapsed, 1.0) # Should have slept at least once (2s initial)

    @patch('pipeline.loader.os.path.exists')
    def test_download_and_checksum(self, mock_exists):
        """Test download_and_checksum computes hash correctly."""
        mock_exists.return_value = True
        
        # Create a temp file with known content
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"hello world")
            temp_path = f.name
        
        try:
            checksum = download_and_checksum("dummy", temp_path)
            # SHA256 of "hello world"
            expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
            self.assertEqual(checksum, expected)
        finally:
            os.unlink(temp_path)

    @patch('pipeline.loader.load_dataset')
    def test_load_openwebtext_max_samples(self, mock_load_dataset):
        """Test that max_samples is respected in non-streaming mode."""
        mock_ds = MagicMock()
        mock_ds.select.return_value = self.mock_ds
        mock_load_dataset.return_value = mock_ds
        
        result = load_openwebtext(streaming=False, max_samples=100)
        
        mock_ds.select.assert_called_once_with(range(100))

if __name__ == '__main__':
    unittest.main()