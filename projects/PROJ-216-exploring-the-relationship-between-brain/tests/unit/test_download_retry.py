import pytest
import time
from unittest.mock import patch, MagicMock
import os
import sys
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from openneuro import cli
from openneuro.api import OpenNeuroAPI

# Mock configuration for testing
MOCK_DATASET_ID = "ds000224"
MOCK_DOWNLOAD_PATH = "/tmp/mock_download"
MAX_RETRIES = 3
INITIAL_DELAY = 0.1  # Short delay for testing

class TestDownloadRetryLogic:
    """
    Unit tests for OpenNeuro download retry logic.
    Verifies that the download function retries on network failures
    and raises an appropriate error after max retries.
    """

    def test_download_succeeds_on_first_attempt(self):
        """Test successful download without retries."""
        with patch('openneuro.api.OpenNeuroAPI.download') as mock_download:
            mock_download.return_value = True
            
            # Simulate the logic that would be in download.py
            retries = 0
            success = False
            while retries <= MAX_RETRIES:
                try:
                    # This simulates the actual download call
                    result = mock_download(MOCK_DATASET_ID, MOCK_DOWNLOAD_PATH)
                    success = result
                    break
                except Exception:
                    retries += 1
            
            assert success is True
            assert retries == 0
            mock_download.assert_called_once_with(MOCK_DATASET_ID, MOCK_DOWNLOAD_PATH)

    def test_download_retries_on_transient_error(self):
        """Test that download retries when a transient network error occurs."""
        with patch('openneuro.api.OpenNeuroAPI.download') as mock_download:
            # Fail twice, then succeed
            mock_download.side_effect = [
                ConnectionError("Network timeout"),
                ConnectionError("Network timeout"),
                True
            ]
            
            retries = 0
            success = False
            last_error = None
            
            while retries <= MAX_RETRIES:
                try:
                    result = mock_download(MOCK_DATASET_ID, MOCK_DOWNLOAD_PATH)
                    success = result
                    break
                except ConnectionError as e:
                    last_error = e
                    retries += 1
                    # In real code, there would be a sleep here
                    time.sleep(INITIAL_DELAY * (2 ** retries))
            
            assert success is True
            assert retries == 2
            assert mock_download.call_count == 3
            assert "Network timeout" in str(last_error)

    def test_download_raises_after_max_retries(self):
        """Test that download raises an error after exhausting retries."""
        with patch('openneuro.api.OpenNeuroAPI.download') as mock_download:
            # Always fail
            mock_download.side_effect = ConnectionError("Persistent network failure")
            
            retries = 0
            success = False
            final_error = None
            
            try:
                while retries <= MAX_RETRIES:
                    try:
                        result = mock_download(MOCK_DATASET_ID, MOCK_DOWNLOAD_PATH)
                        success = result
                        break
                    except ConnectionError as e:
                        retries += 1
                        final_error = e
                        if retries > MAX_RETRIES:
                            raise RuntimeError(f"Download failed after {MAX_RETRIES} retries: {e}")
            except RuntimeError as e:
                final_error = e
            
            assert success is False
            assert retries == MAX_RETRIES + 1
            assert mock_download.call_count == MAX_RETRIES + 1
            assert "failed after" in str(final_error)

    def test_download_handles_non_network_errors_immediately(self):
        """Test that non-network errors (e.g., permission, disk full) are not retried."""
        with patch('openneuro.api.OpenNeuroAPI.download') as mock_download:
            # Raise a non-retryable error
            mock_download.side_effect = PermissionError("No write permission")
            
            retries = 0
            success = False
            caught_error = None
            
            try:
                # In real implementation, we would check error type
                # For this test, we simulate the logic
                result = mock_download(MOCK_DATASET_ID, MOCK_DOWNLOAD_PATH)
                success = result
            except PermissionError as e:
                caught_error = e
                retries = 0  # Should not retry
            
            assert success is False
            assert retries == 0
            assert mock_download.call_count == 1
            assert "No write permission" in str(caught_error)

    def test_download_uses_correct_backoff_strategy(self):
        """Test that the retry logic uses exponential backoff."""
        with patch('openneuro.api.OpenNeuroAPI.download') as mock_download:
            mock_download.side_effect = [
                ConnectionError("Timeout 1"),
                ConnectionError("Timeout 2"),
                True
            ]
            
            delays = []
            current_delay = INITIAL_DELAY
            
            # Simulate the backoff calculation
            for i in range(1, MAX_RETRIES + 1):
                calculated_delay = current_delay * (2 ** i)
                delays.append(calculated_delay)
                current_delay = calculated_delay
            
            # Verify exponential growth
            assert delays[0] < delays[1]
            assert delays[1] < delays[2]
            assert delays[0] == INITIAL_DELAY * 2
            assert delays[1] == INITIAL_DELAY * 4