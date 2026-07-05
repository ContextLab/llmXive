"""
Unit tests for download.py error handling and retry logic.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

# Import the module under test
from code.download import fetch_with_retry, download_file, validate_url

class TestFetchWithRetry:
    @patch('code.download.requests.get')
    def test_success_on_first_attempt(self, mock_get):
        """Test successful download on first try."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [b"test data"]
        mock_response.headers = {'content-length': '9'}
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "test.txt"
            result = fetch_with_retry("http://example.com/file", output_path=dest)

            assert result == dest
            assert dest.exists()
            with open(dest, 'rb') as f:
                assert f.read() == b"test data"
            mock_get.assert_called_once()

    @patch('code.download.requests.get')
    def test_retry_on_503(self, mock_get):
        """Test retry logic triggers on 503 status."""
        mock_error = MagicMock()
        mock_error.status_code = 503
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.iter_content = lambda chunk_size: [b"success"]
        mock_response_success.headers = {'content-length': '7'}

        # First call raises HTTPError (simulated via status check logic in function)
        # The function checks status_code and raises HTTPError manually if in list
        # So we mock the response to have status 503
        mock_get.side_effect = [
            MagicMock(status_code=503, raise_for_status=lambda: None, headers={}), # First attempt
            MagicMock(status_code=200, iter_content=lambda chunk_size: [b"success"], headers={'content-length': '7'}) # Second
        ]
        
        # Actually, the function logic:
        # response = requests.get(...)
        # if status in list: raise HTTPError
        # So we need the side_effect to be the response object itself, and the function will raise.
        # Let's adjust: side_effect should be the response object, and we need to simulate the raise inside.
        # Better: Mock requests.get to return a response, then the function raises.
        
        # Re-implementation of mock strategy:
        # 1st call: returns response with 503. Function raises HTTPError.
        # 2nd call: returns response with 200. Function succeeds.
        
        mock_resp_503 = MagicMock()
        mock_resp_503.status_code = 503
        mock_resp_503.headers = {}
        
        mock_resp_200 = MagicMock()
        mock_resp_200.status_code = 200
        mock_resp_200.iter_content = lambda chunk_size: [b"success"]
        mock_resp_200.headers = {'content-length': '7'}

        mock_get.side_effect = [mock_resp_503, mock_resp_200]

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "test.txt"
            # Backoff factor 0.01 for speed in test
            result = fetch_with_retry("http://example.com/file", output_path=dest, backoff_factor=0.01)
            
            assert result == dest
            assert mock_get.call_count == 2

    @patch('code.download.requests.get')
    def test_failure_after_retries(self, mock_get):
        """Test that function returns None after exhausting retries."""
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "test.txt"
            result = fetch_with_retry("http://example.com/file", output_path=dest, retries=1, backoff_factor=0.01)
            
            assert result is None
            assert mock_get.call_count == 2 # Initial + 1 retry

class TestDownloadFile:
    @patch('code.download.fetch_with_retry')
    def test_download_file_wrapper(self, mock_fetch):
        """Test download_file wrapper returns True on success."""
        mock_fetch.return_value = Path("/tmp/test.txt")
        result = download_file("http://example.com", "/tmp/test.txt")
        assert result is True
        mock_fetch.assert_called_once()

    @patch('code.download.fetch_with_retry')
    def test_download_file_failure(self, mock_fetch):
        """Test download_file wrapper returns False on failure."""
        mock_fetch.return_value = None
        result = download_file("http://example.com", "/tmp/test.txt")
        assert result is False

class TestValidateUrl:
    @patch('code.download.requests.head')
    def test_validate_success_head(self, mock_head):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_head.return_value = mock_resp
        assert validate_url("http://example.com") is True

    @patch('code.download.requests.head')
    @patch('code.download.requests.get')
    def test_validate_fallback_get(self, mock_get, mock_head):
        mock_head_resp = MagicMock()
        mock_head_resp.status_code = 405 # Method not allowed
        mock_head.return_value = mock_head_resp
        
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get.return_value = mock_get_resp
        
        assert validate_url("http://example.com") is True

    @patch('code.download.requests.head')
    def test_validate_failure(self, mock_head):
        mock_head.side_effect = Exception("Network error")
        assert validate_url("http://example.com") is False
