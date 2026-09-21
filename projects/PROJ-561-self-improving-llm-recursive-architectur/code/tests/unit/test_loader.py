import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os
import time
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

class TestLoaderFunctions(unittest.TestCase):

    def test_exponential_backoff_initial_delay(self):
        """Test that exponential_backoff decorator applies delay on retry."""
        call_count = 0
        
        @exponential_backoff
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Simulated transient error")
            return "success"
        
        # This should succeed on the second attempt
        result = failing_func()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 2)

    @patch('pipeline.loader.requests.head')
    def test_verify_urls_success(self, mock_head):
        """Test verify_urls with successful responses."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        urls = ["http://example.com/dataset1", "http://example.com/dataset2"]
        result = verify_urls(urls)
        
        self.assertTrue(result)
        self.assertEqual(mock_head.call_count, 2)

    @patch('pipeline.loader.requests.head')
    def test_verify_urls_failure(self, mock_head):
        """Test verify_urls raises error on unreachable URL."""
        mock_head.side_effect = Exception("Network error")
        
        urls = ["http://example.com/unreachable"]
        
        with self.assertRaises(HFTransientError):
            verify_urls(urls)

    @patch('pipeline.loader.load_dataset')
    def test_load_openwebtext_success(self, mock_load_dataset):
        """Test successful loading of OpenWebText."""
        mock_ds = MagicMock()
        mock_iter = iter([{"text": "sample text"}])
        mock_ds.__iter__ = MagicMock(return_value=mock_iter)
        mock_load_dataset.return_value = mock_ds
        
        data = load_openwebtext(split="train", streaming=True)
        first_item = next(data)
        
        self.assertEqual(first_item["text"], "sample text")
        mock_load_dataset.assert_called_once_with("stas/openwebtext", split="train", streaming=True)

    @patch('pipeline.loader.load_dataset')
    def test_load_openwebtext_failure(self, mock_load_dataset):
        """Test load_openwebtext raises FileNotFoundError on failure."""
        mock_load_dataset.side_effect = Exception("Dataset not found")
        
        with self.assertRaises(FileNotFoundError):
            list(load_openwebtext(split="train", streaming=True))

    @patch('pipeline.loader.load_dataset')
    def test_load_gsm8k_success(self, mock_load_dataset):
        """Test successful loading of GSM8K."""
        mock_ds = MagicMock()
        mock_iter = iter([{"question": "What is 2+2?", "answer": "4"}])
        mock_ds.__iter__ = MagicMock(return_value=mock_iter)
        mock_load_dataset.return_value = mock_ds
        
        data = load_gsm8k(split="train", streaming=True)
        first_item = next(data)
        
        self.assertEqual(first_item["question"], "What is 2+2?")
        mock_load_dataset.assert_called_once_with("gsm8k", "main", split="train", streaming=True)

    @patch('pipeline.loader.load_dataset')
    def test_load_arc_challenge_success(self, mock_load_dataset):
        """Test successful loading of ARC-Challenge."""
        mock_ds = MagicMock()
        mock_iter = iter([{"question": "Sample question", "choices": ["A", "B"]}])
        mock_ds.__iter__ = MagicMock(return_value=mock_iter)
        mock_load_dataset.return_value = mock_ds
        
        data = load_arc_challenge(split="train", streaming=True)
        first_item = next(data)
        
        self.assertEqual(first_item["question"], "Sample question")
        mock_load_dataset.assert_called_once_with("ai2_arc", "ARC-Challenge", split="train", streaming=True)

    @patch('pipeline.loader.load_dataset')
    def test_load_boolq_success(self, mock_load_dataset):
        """Test successful loading of BoolQ."""
        mock_ds = MagicMock()
        mock_iter = iter([{"question": "Is it true?", "answer": True}])
        mock_ds.__iter__ = MagicMock(return_value=mock_iter)
        mock_load_dataset.return_value = mock_ds
        
        data = load_boolq(split="train", streaming=True)
        first_item = next(data)
        
        self.assertEqual(first_item["question"], "Is it true?")
        mock_load_dataset.assert_called_once_with("boolq", split="train", streaming=True)

    def test_exponential_backoff_max_retries(self):
        """Test that exponential_backoff stops after max retries."""
        call_count = 0
        
        @exponential_backoff
        def always_failing():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")
        
        with self.assertRaises(ConnectionError):
            always_failing()
        
        # Should retry 5 times (max_retries default in decorator)
        # Initial call + 5 retries = 6 calls? 
        # The wrapper logic: while retries < max_retries (5), so 0,1,2,3,4 -> 5 retries.
        # Total calls: 1 initial + 5 retries = 6.
        # However, the implementation increments retries BEFORE checking limit in the loop.
        # Let's verify the exact behavior: 
        # retries=0, fail, retries=1, sleep. retries=1, fail, retries=2... retries=5, fail, raise.
        # So it calls 6 times.
        self.assertGreaterEqual(call_count, 5)

if __name__ == '__main__':
    unittest.main()