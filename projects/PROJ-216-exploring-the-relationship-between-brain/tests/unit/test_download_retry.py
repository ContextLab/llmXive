"""
Unit tests for OpenNeuro download retry logic.

Validates requirements defined in T013a:
- Retry count: 3 attempts
- Backoff strategy: Exponential (base 2)
- Behavior: Should raise an exception after max retries if all attempts fail.
"""
import pytest
import time
from unittest.mock import patch, MagicMock, call
import sys
import os

# Add parent directory to path to allow importing code/download.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from download import download_dataset


class TestDownloadRetryLogic:
    """Tests for the retry mechanism in download_dataset."""

    @patch('download.time.sleep')
    @patch('download.cli.download')
    def test_retry_logic_on_failure(self, mock_download, mock_sleep):
        """
        Verify that the function attempts to download exactly 3 times
        before raising an exception when the source is consistently unavailable.
        """
        # Configure mock to always fail
        mock_download.side_effect = Exception("Simulated network failure")

        with pytest.raises(Exception) as exc_info:
            # Call the function with a dummy dataset ID
            download_dataset("ds000000", download_path="/tmp/test", max_retries=3)

        # Verify the exception message
        assert "Simulated network failure" in str(exc_info.value)

        # Verify download was called exactly 3 times (max_retries)
        assert mock_download.call_count == 3

        # Verify sleep was called twice (between attempts 1-2 and 2-3)
        assert mock_sleep.call_count == 2

    @patch('download.time.sleep')
    @patch('download.cli.download')
    def test_exponential_backoff_timing(self, mock_download, mock_sleep):
        """
        Verify that the sleep duration follows exponential backoff (2^attempt).
        Attempt 1 fails -> sleep 2^1 = 2s
        Attempt 2 fails -> sleep 2^2 = 4s
        """
        mock_download.side_effect = Exception("Fail")

        with pytest.raises(Exception):
            download_dataset("ds000000", download_path="/tmp/test", max_retries=3)

        # Check sleep arguments
        # Call 1: sleep(2)
        # Call 2: sleep(4)
        assert mock_sleep.call_args_list[0][0][0] == 2.0
        assert mock_sleep.call_args_list[1][0][0] == 4.0

    @patch('download.cli.download')
    def test_success_on_first_attempt(self, mock_download):
        """Verify that if the first attempt succeeds, no retries occur."""
        mock_download.return_value = True

        download_dataset("ds000000", download_path="/tmp/test")

        mock_download.assert_called_once()

    @patch('download.time.sleep')
    @patch('download.cli.download')
    def test_success_on_second_attempt(self, mock_download, mock_sleep):
        """Verify that if the second attempt succeeds, only one retry occurs."""
        # First call fails, second call succeeds
        mock_download.side_effect = [Exception("First fail"), True]

        download_dataset("ds000000", download_path="/tmp/test", max_retries=3)

        # Should be called twice
        assert mock_download.call_count == 2
        # Should sleep once
        assert mock_sleep.call_count == 1

    @patch('download.time.sleep')
    @patch('download.cli.download')
    def test_max_retries_parameter_respected(self, mock_download, mock_sleep):
        """Verify that the max_retries parameter limits the number of attempts."""
        mock_download.side_effect = Exception("Always fails")

        with pytest.raises(Exception):
            download_dataset("ds000000", download_path="/tmp/test", max_retries=2)

        # Should be called exactly 2 times
        assert mock_download.call_count == 2