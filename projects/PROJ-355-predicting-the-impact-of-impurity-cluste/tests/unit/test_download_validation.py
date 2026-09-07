"""
Unit tests for T013b: Verify the [DATA_UNAVAILABLE] log format and 3-attempt limit behavior.

This test verifies that the download_bulk_configs function:
1. Attempts to fetch data exactly 3 times before failing.
2. Logs the error message in the exact format: "[DATA_UNAVAILABLE] URL=<url> attempts=3"
3. Raises a ValueError with the correct message structure.
"""
import logging
import io
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from requests import RequestException

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import download_bulk_configs
from validators import validate_citations


class TestDownloadValidation:
    """Tests for download validation logic (T013b)."""

    def test_max_retries_and_log_format(self, caplog):
        """
        Verify that the function attempts exactly 3 times and logs the specific format.
        """
        # Setup logging capture
        caplog.set_level(logging.INFO)
        
        # Mock the validate_citations to pass (simulate valid metadata)
        with patch('data.download.validate_citations', return_value=True):
            # Mock the requests.get to always fail
            with patch('data.download.requests.get') as mock_get:
                mock_get.side_effect = RequestException("Connection refused")
                
                # Call the function
                url = "https://materialsproject.org/test"
                
                # We expect a ValueError because the data is unavailable after retries
                with pytest.raises(ValueError) as excinfo:
                    download_bulk_configs(url, max_retries=3)
                
                # Verify the error message contains the URL
                assert "URL=" in str(excinfo.value)
                
                # Check the logs for the specific format
                # We expect the log to appear on the final attempt (attempt 3)
                # The format must be: "[DATA_UNAVAILABLE] URL=<url> attempts=3"
                
                # Filter logs for the specific pattern
                data_unavailable_logs = [
                    record.message 
                    for record in caplog.records 
                    if "DATA_UNAVAILABLE" in record.message
                ]
                
                # Verify at least one log entry exists
                assert len(data_unavailable_logs) > 0, "Expected DATA_UNAVAILABLE log entry not found"
                
                # Verify the format of the last log entry (the final attempt)
                final_log = data_unavailable_logs[-1]
                expected_format = f"[DATA_UNAVAILABLE] URL={url} attempts=3"
                
                # The log might have additional context, so we check for the core pattern
                assert expected_format in final_log, (
                    f"Log format mismatch.\nExpected substring: {expected_format}\nActual log: {final_log}"
                )

    def test_retry_count_is_exactly_three(self, caplog):
        """
        Verify that the function makes exactly 3 attempts before raising an error.
        """
        caplog.set_level(logging.INFO)
        
        with patch('data.download.validate_citations', return_value=True):
            with patch('data.download.requests.get') as mock_get:
                mock_get.side_effect = RequestException("Connection refused")
                
                url = "https://materialsproject.org/test"
                
                with pytest.raises(ValueError):
                    download_bulk_configs(url, max_retries=3)
                
                # Verify that get was called exactly 3 times
                assert mock_get.call_count == 3, (
                    f"Expected 3 attempts, but requests.get was called {mock_get.call_count} times"
                )

    def test_valid_data_does_not_retry(self, caplog):
        """
        Verify that if data is available, no retries occur and no error is logged.
        """
        caplog.set_level(logging.INFO)
        
        # Create a mock response that succeeds on the first try
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"structures": []}
        
        with patch('data.download.validate_citations', return_value=True):
            with patch('data.download.requests.get', return_value=mock_response) as mock_get:
                url = "https://materialsproject.org/test"
                
                # This should succeed without raising an error
                result = download_bulk_configs(url, max_retries=3)
                
                # Verify only one attempt was made
                assert mock_get.call_count == 1, (
                    f"Expected 1 attempt for valid data, but got {mock_get.call_count}"
                )
                
                # Verify no DATA_UNAVAILABLE logs were generated
                data_unavailable_logs = [
                    record.message 
                    for record in caplog.records 
                    if "DATA_UNAVAILABLE" in record.message
                ]
                assert len(data_unavailable_logs) == 0, (
                    "Unexpected DATA_UNAVAILABLE log found for valid data"
                )