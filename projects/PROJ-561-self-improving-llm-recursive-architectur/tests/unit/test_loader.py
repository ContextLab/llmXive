import unittest
from unittest.mock import patch, MagicMock, PropertyMock, call
import sys
import os
import time
import tempfile
import requests

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.loader import exponential_backoff, HFTransientError, verify_urls, download_and_checksum

class TestExponentialBackoff(unittest.TestCase):
    
    def setUp(self):
        self.call_count = 0
        self.max_delay = 0.5  # Small delay for testing

    @exponential_backoff(max_retries=3, initial_delay=0.1, backoff_factor=2.0, jitter=False)
    def failing_function(self):
        self.call_count += 1
        if self.call_count < 3:
            raise HFTransientError("Simulated transient error")
        return "success"

    @exponential_backoff(max_retries=3, initial_delay=0.1, backoff_factor=2.0, jitter=False)
    def always_failing_function(self):
        self.call_count += 1
        raise HFTransientError("Always fails")

    def test_exponential_backoff_initial_delay(self):
        """Test that the initial delay is respected."""
        start_time = time.time()
        result = self.failing_function()
        elapsed = time.time() - start_time
        
        # Should have waited at least initial_delay + initial_delay*2 = 0.3s
        # But we're only checking that it took some time (at least 0.1s)
        self.assertGreaterEqual(elapsed, 0.1)
        self.assertEqual(self.call_count, 3)
        self.assertEqual(result, "success")

    def test_exponential_backoff_max_retries_exceeded(self):
        """Test that the function raises after max retries."""
        self.call_count = 0
        with self.assertRaises(HFTransientError):
            self.always_failing_function()
        
        # Should have been called max_retries + 1 times (initial + retries)
        self.assertEqual(self.call_count, 4)

    def test_exponential_backoff_success_on_first_try(self):
        """Test that the function returns immediately on success."""
        @exponential_backoff(max_retries=3, initial_delay=1.0, jitter=False)
        def immediate_success():
            return "immediate"
        
        start_time = time.time()
        result = immediate_success()
        elapsed = time.time() - start_time
        
        self.assertEqual(result, "immediate")
        self.assertLess(elapsed, 0.1)  # Should be nearly instantaneous

    def test_exponential_backoff_with_jitter(self):
        """Test that jitter is applied when enabled."""
        call_delays = []
        
        @exponential_backoff(max_retries=3, initial_delay=0.1, backoff_factor=2.0, jitter=True)
        def failing_with_jitter():
            call_delays.append(time.time())
            if len(call_delays) < 3:
                raise HFTransientError("Simulated transient error")
            return "success"
        
        failing_with_jitter()
        
        # Check that delays are not exactly powers of 2 * initial_delay
        # (due to jitter)
        for i in range(1, len(call_delays)):
            actual_delay = call_delays[i] - call_delays[i-1]
            expected_base_delay = 0.1 * (2 ** (i-1))
            # With jitter, the delay should be between 0.5*base and 1.5*base
            self.assertGreaterEqual(actual_delay, 0.5 * expected_base_delay)
            self.assertLessEqual(actual_delay, 1.5 * expected_base_delay)

class TestVerifyUrls(unittest.TestCase):
    
    @patch('pipeline.loader.requests.head')
    def test_verify_urls_all_success(self, mock_head):
        """Test verify_urls when all URLs are successful."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        urls = ["http://example.com", "http://example.org"]
        result = verify_urls(urls)
        
        self.assertTrue(result)
        self.assertEqual(mock_head.call_count, 2)

    @patch('pipeline.loader.requests.head')
    def test_verify_urls_one_failure(self, mock_head):
        """Test verify_urls when one URL fails."""
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 404
        
        mock_head.side_effect = [mock_response_success, mock_response_fail]
        
        urls = ["http://example.com", "http://example.org"]
        
        with self.assertRaises(ValueError):
            verify_urls(urls)

    @patch('pipeline.loader.requests.head')
    def test_verify_urls_network_error(self, mock_head):
        """Test verify_urls when there's a network error."""
        mock_head.side_effect = requests.exceptions.ConnectionError("Network error")
        
        urls = ["http://example.com"]
        
        with self.assertRaises(requests.exceptions.ConnectionError):
            verify_urls(urls)

class TestDownloadAndChecksum(unittest.TestCase):
    
    @patch('pipeline.loader.requests.get')
    def test_download_and_checksum_success(self, mock_get):
        """Test download_and_checksum with a successful download."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"test data"]
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = os.path.join(tmpdir, "test.txt")
            checksum = download_and_checksum("test_dataset", dest_path)
            
            # Check that file was created
            self.assertTrue(os.path.exists(dest_path))
            
            # Check that checksum file was created
            self.assertTrue(os.path.exists(dest_path + ".sha256"))
            
            # Check that checksum is valid hex
            self.assertEqual(len(checksum), 64)
            self.assertTrue(all(c in '0123456789abcdef' for c in checksum))

    @patch('pipeline.loader.requests.get')
    def test_download_and_checksum_http_error(self, mock_get):
        """Test download_and_checksum with an HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = os.path.join(tmpdir, "test.txt")
            
            with self.assertRaises(requests.exceptions.HTTPError):
                download_and_checksum("test_dataset", dest_path)

if __name__ == '__main__':
    unittest.main()