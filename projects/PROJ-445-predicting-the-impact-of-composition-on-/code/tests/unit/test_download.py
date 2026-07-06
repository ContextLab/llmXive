import pytest
import time
from unittest.mock import patch, MagicMock
import requests
from requests.exceptions import RequestException, Timeout, HTTPError

import sys
import os

# Ensure src is in path for imports if running from root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.download import download_dataset_with_retry


class TestDownloadRetryLogic:
    """Unit tests for data download retry logic in src/data/download.py."""

    @patch('src.data.download.requests.get')
    def test_download_success_on_first_try(self, mock_get):
        """Test that a successful download on the first attempt returns data immediately."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "composition,Tg\nAs2S3,250\n"
        mock_get.return_value = mock_response

        url = "http://example.com/data.csv"
        result = download_dataset_with_retry(url, max_retries=3)

        assert result == mock_response
        assert mock_get.call_count == 1

    @patch('src.data.download.requests.get')
    def test_download_success_after_retry(self, mock_get):
        """Test that the function retries on transient failure and succeeds eventually."""
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.text = "composition,Tg\nAs2S3,250\n"

        # First two calls fail, third succeeds
        mock_get.side_effect = [
            RequestException("Network error"),
            RequestException("Network error"),
            mock_response_success
        ]

        url = "http://example.com/data.csv"
        result = download_dataset_with_retry(url, max_retries=3)

        assert result == mock_response_success
        assert mock_get.call_count == 3

    @patch('src.data.download.requests.get')
    def test_download_fails_after_max_retries(self, mock_get):
        """Test that the function raises an exception after exhausting retries."""
        mock_get.side_effect = RequestException("Persistent network error")

        url = "http://example.com/data.csv"
        with pytest.raises(Exception) as exc_info:
            download_dataset_with_retry(url, max_retries=2)

        assert "Persistent network error" in str(exc_info.value)
        assert mock_get.call_count == 2  # Initial + 1 retry

    @patch('src.data.download.requests.get')
    def test_download_handles_timeout_exception(self, mock_get):
        """Test that Timeout exceptions are caught and trigger a retry."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.side_effect = [
            Timeout("Connection timed out"),
            mock_response
        ]

        url = "http://example.com/data.csv"
        result = download_dataset_with_retry(url, max_retries=3)

        assert result == mock_response
        assert mock_get.call_count == 2

    @patch('src.data.download.requests.get')
    def test_download_handles_http_error_exception(self, mock_get):
        """Test that HTTPError exceptions (5xx) are caught and trigger a retry."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        http_error_500 = HTTPError("500 Server Error")
        http_error_500.response = MagicMock()
        http_error_500.response.status_code = 500

        mock_get.side_effect = [
            http_error_500,
            mock_response
        ]

        url = "http://example.com/data.csv"
        result = download_dataset_with_retry(url, max_retries=3)

        assert result == mock_response
        assert mock_get.call_count == 2

    @patch('src.data.download.time.sleep')
    @patch('src.data.download.requests.get')
    def test_download_waits_between_retries(self, mock_get, mock_sleep):
        """Test that the function waits (sleeps) between retry attempts."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.side_effect = [
            RequestException("Error"),
            mock_response
        ]

        url = "http://example.com/data.csv"
        download_dataset_with_retry(url, max_retries=2, wait_time=0.1)

        # Should have called sleep once (after first failure, before second attempt)
        assert mock_sleep.called
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(0.1)
