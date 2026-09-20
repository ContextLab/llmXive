"""Unit tests for retry logic in download.py."""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import logging
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import download_bulk_configs
from config import get_project_root


class TestRetryLogic:
    """Tests for the retry mechanism in download_bulk_configs."""

    @patch('data.download.requests.head')
    @patch('data.download.validate_citations')
    def test_success_on_first_attempt(self, mock_validate, mock_head):
        """Test that download succeeds immediately if the URL is valid."""
        # Setup mocks
        mock_validate.return_value = True
        mock_head.return_value.status_code = 200

        # Create a mock response for requests.get (implied by context of download)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"fake_data"]
        
        with patch('data.download.requests.get', return_value=mock_response) as mock_get:
            result = download_bulk_configs("https://materialsproject.org/test", max_retries=3)
            
            # Verify validation was called
            mock_validate.assert_called_once()
            # Verify HEAD request was made once
            assert mock_head.call_count == 1
            # Verify GET request was made once
            assert mock_get.call_count == 1
            # Verify result is a Path object
            assert isinstance(result, Path)
            assert result.exists()

    @patch('data.download.requests.head')
    @patch('data.download.validate_citations')
    def test_retry_on_transient_failure(self, mock_validate, mock_head):
        """Test that the function retries on transient failures (503)."""
        # Setup mocks
        mock_validate.return_value = True
        
        # Fail first 2 times, succeed on 3rd
        mock_head.side_effect = [
            MagicMock(status_code=503),
            MagicMock(status_code=503),
            MagicMock(status_code=200)
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"fake_data"]
        
        with patch('data.download.requests.get', return_value=mock_response) as mock_get:
            result = download_bulk_configs("https://materialsproject.org/test", max_retries=3)
            
            # Verify HEAD was called 3 times (2 failures + 1 success)
            assert mock_head.call_count == 3
            # Verify GET was called only once (after success)
            assert mock_get.call_count == 1
            assert result.exists()

    @patch('data.download.requests.head')
    @patch('data.download.validate_citations')
    def test_fail_after_max_retries(self, mock_validate, mock_head, caplog):
        """Test that the function fails loudly after max_retries attempts."""
        # Setup mocks
        mock_validate.return_value = True
        
        # Always fail
        mock_head.return_value = MagicMock(status_code=503)

        with patch('data.download.requests.get') as mock_get:
            # We expect a ValueError or similar to be raised by the retry logic
            # The download.py logic should raise an error after 3 failed HEAD checks
            with pytest.raises(ValueError) as exc_info:
                download_bulk_configs("https://materialsproject.org/test", max_retries=3)
            
            assert "Max retries exceeded" in str(exc_info.value)
            assert mock_head.call_count == 3
            assert mock_get.call_count == 0

    @patch('data.download.requests.head')
    @patch('data.download.validate_citations')
    def test_log_format_on_failure(self, mock_validate, mock_head, caplog):
        """Verify the exact log format [DATA_UNAVAILABLE] URL=<url> attempts=<n>."""
        mock_validate.return_value = True
        mock_head.return_value = MagicMock(status_code=503)

        with patch('data.download.requests.get'):
            with caplog.at_level(logging.ERROR):
                with pytest.raises(ValueError):
                    download_bulk_configs("https://materialsproject.org/test", max_retries=3)
                
                # Check that the log message matches the required format
                # The log should appear when the retry loop exhausts attempts
                log_messages = [record.message for record in caplog.records]
                # We expect a log entry indicating the failure after attempts
                # The exact implementation in download.py should log this before raising
                assert any("[DATA_UNAVAILABLE]" in msg for msg in log_messages)
                
                # Verify the specific URL and attempt count are in the log
                # Note: The exact log message structure depends on download.py implementation
                # Assuming it logs: f"[DATA_UNAVAILABLE] URL={url} attempts={max_retries}"
                found_expected = False
                for msg in log_messages:
                    if "[DATA_UNAVAILABLE]" in msg and "URL=https://materialsproject.org/test" in msg and "attempts=3" in msg:
                        found_expected = True
                        break
                assert found_expected, f"Expected log format not found in: {log_messages}"