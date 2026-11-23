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

from download import download_dataset_with_retry


class TestDownloadRetryLogic:
    """Tests for the retry mechanism in download_dataset_with_retry."""

    @patch('download.time.sleep')
    @patch('download.subprocess.run')
    def test_retry_logic_on_failure(self, mock_run, mock_sleep):
        """
        Verify that the function attempts to download exactly 3 times
        before raising an exception when the source is consistently unavailable.
        """
        # Configure mock to always fail
        mock_run.return_value = MagicMock(returncode=1, stderr="Simulated network failure")

        with pytest.raises(RuntimeError) as exc_info:
            # Call the function with a dummy dataset ID
            download_dataset_with_retry("ds000000", download_path=MagicMock(), max_retries=3)

        # Verify the exception message
        assert "Failed to download" in str(exc_info.value)

        # Verify subprocess.run was called exactly 3 times (max_retries)
        assert mock_run.call_count == 3

        # Verify sleep was called twice (between attempts 1-2 and 2-3)
        assert mock_sleep.call_count == 2

    @patch('download.time.sleep')
    @patch('download.subprocess.run')
    def test_exponential_backoff_timing(self, mock_run, mock_sleep):
        """
        Verify that the sleep duration follows exponential backoff (2^attempt).
        Attempt 1 fails -> sleep 2^1 = 2s (initial_delay=2 in test? No, default is 1.0)
        Default initial_delay=1.0, multiplier=2.0
        Attempt 1 fails -> sleep 1.0
        Attempt 2 fails -> sleep 2.0
        """
        mock_run.return_value = MagicMock(returncode=1, stderr="Fail")

        with pytest.raises(RuntimeError):
            download_dataset_with_retry("ds000000", download_path=MagicMock(), max_retries=3, initial_delay=1.0)

        # Check sleep arguments
        # Call 1: sleep(1.0)
        # Call 2: sleep(2.0)
        assert mock_sleep.call_args_list[0][0][0] == 1.0
        assert mock_sleep.call_args_list[1][0][0] == 2.0

    @patch('download.subprocess.run')
    def test_success_on_first_attempt(self, mock_run):
        """Verify that if the first attempt succeeds, no retries occur."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Success")

        download_dataset_with_retry("ds000000", download_path=MagicMock())

        mock_run.assert_called_once()

    @patch('download.time.sleep')
    @patch('download.subprocess.run')
    def test_success_on_second_attempt(self, mock_run, mock_sleep):
        """Verify that if the second attempt succeeds, only one retry occurs."""
        # First call fails, second call succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1, stderr="First fail"),
            MagicMock(returncode=0, stdout="Success")
        ]

        download_dataset_with_retry("ds000000", download_path=MagicMock(), max_retries=3)

        # Should be called twice
        assert mock_run.call_count == 2
        # Should sleep once
        assert mock_sleep.call_count == 1

    @patch('download.time.sleep')
    @patch('download.subprocess.run')
    def test_max_retries_parameter_respected(self, mock_run, mock_sleep):
        """Verify that the max_retries parameter limits the number of attempts."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Always fails")

        with pytest.raises(RuntimeError):
            download_dataset_with_retry("ds000000", download_path=MagicMock(), max_retries=2)

        # Should be called exactly 2 times
        assert mock_run.call_count == 2
