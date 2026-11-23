import pytest
import time
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data.download import download_with_retry, RETRY_DELAYS, MAX_RETRIES
from code.utils.logging import get_logger

class TestRetryLogic:
    """Tests for the retry logic with exponential backoff in download.py"""

    def test_exponential_backoff_timings(self):
        """Verify that retry delays follow the 1s, 2s, 4s pattern (FR-002)"""
        expected_delays = [1, 2, 4]
        assert RETRY_DELAYS == expected_delays, f"Expected {expected_delays}, got {RETRY_DELAYS}"

    def test_max_retries_count(self):
        """Verify that the number of retries matches the number of delay intervals"""
        assert MAX_RETRIES == len(RETRY_DELAYS), "MAX_RETRIES should match number of delay intervals"

    @patch('code.data.download.load_dataset')
    @patch('code.data.download.time.sleep')
    def test_retry_on_failure_then_success(self, mock_sleep, mock_load_dataset, tmp_path):
        """Test that the function retries on failure and succeeds on the second attempt"""
        logger = get_logger("test_download")
        dataset_id = "test/dataset"
        target_path = tmp_path / "test_dataset"

        # First call fails, second call succeeds
        mock_load_dataset.side_effect = [
            Exception("Connection timeout"),
            MagicMock(__len__=MagicMock(return_value=10))
        ]

        # Mock Path.mkdir to avoid actual file system operations
        with patch.object(Path, 'mkdir', return_value=None):
            result = download_with_retry(dataset_id, target_path, logger)

        # Verify that sleep was called with correct delays
        mock_sleep.assert_has_calls([call(1), call(2)])

        # Verify that load_dataset was called twice
        assert mock_load_dataset.call_count == 2

        # Verify that the function returned the target path on success
        assert result == target_path

    @patch('code.data.download.load_dataset')
    @patch('code.data.download.time.sleep')
    def test_all_retries_fail(self, mock_sleep, mock_load_dataset, tmp_path):
        """Test that the function raises an exception after all retries fail"""
        logger = get_logger("test_download")
        dataset_id = "test/dataset"
        target_path = tmp_path / "test_dataset"

        # All calls fail
        mock_load_dataset.side_effect = Exception("Connection timeout")

        # Mock Path.mkdir
        with patch.object(Path, 'mkdir', return_value=None):
            with pytest.raises(Exception) as exc_info:
                download_with_retry(dataset_id, target_path, logger)

        # Verify that sleep was called with all delays
        mock_sleep.assert_has_calls([call(1), call(2), call(4)])

        # Verify that load_dataset was called MAX_RETRIES times
        assert mock_load_dataset.call_count == MAX_RETRIES

        # Verify the error message
        assert "Connection timeout" in str(exc_info.value)

    @patch('code.data.download.load_dataset')
    @patch('code.data.download.time.sleep')
    def test_success_on_first_attempt(self, mock_sleep, mock_load_dataset, tmp_path):
        """Test that the function succeeds on the first attempt without retries"""
        logger = get_logger("test_download")
        dataset_id = "test/dataset"
        target_path = tmp_path / "test_dataset"

        # First call succeeds
        mock_load_dataset.return_value = MagicMock(__len__=MagicMock(return_value=10))

        # Mock Path.mkdir
        with patch.object(Path, 'mkdir', return_value=None):
            result = download_with_retry(dataset_id, target_path, logger)

        # Verify that sleep was never called
        mock_sleep.assert_not_called()

        # Verify that load_dataset was called once
        assert mock_load_dataset.call_count == 1

        # Verify that the function returned the target path
        assert result == target_path

    def test_retry_delays_are_increasing(self):
        """Verify that retry delays are strictly increasing (exponential)"""
        for i in range(1, len(RETRY_DELAYS)):
            assert RETRY_DELAYS[i] > RETRY_DELAYS[i-1], "Retry delays should be strictly increasing"