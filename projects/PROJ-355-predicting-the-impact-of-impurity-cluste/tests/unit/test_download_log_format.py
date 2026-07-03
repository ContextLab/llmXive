"""
Unit tests for T013b: Verify the [DATA_UNAVAILABLE] log format and 3-attempt limit behavior.

This task verifies that the download logic in code/data/download.py:
1. Logs exactly the format: "[DATA_UNAVAILABLE] URL=<url> attempts=3" upon failure.
2. Retries exactly 3 times before giving up.
3. Logs the failure only after the 3rd attempt fails.

Since T013 (download.py) is implemented, we import and test its behavior
by mocking the network calls to simulate failure.
"""
import logging
import io
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.download import download_bulk_configs
from code.validators import validate_citations


def test_download_attempts_limit_and_log_format():
    """
    Test that download_bulk_configs:
    1. Attempts to fetch exactly 3 times.
    2. Logs the specific format "[DATA_UNAVAILABLE] URL=<url> attempts=3" on failure.
    """
    # Setup a mock URL that will always fail
    mock_url = "https://materialsproject.org/api/fake-endpoint"
    
    # Capture log output
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.ERROR)
    
    # Get the logger used by download module (assuming it uses standard logging)
    logger = logging.getLogger("code.data.download")
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)

    # Mock the requests.get to raise an exception every time
    with patch('code.data.download.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Connection Refused")
        mock_get.return_value = mock_response

        # Mock validate_citations to return True (simulating a valid URL check)
        # so we can focus on the download retry logic
        with patch('code.data.download.validate_citations', return_value=True):
            try:
                # Call the function. It should fail after 3 attempts.
                # We expect it to raise an error or return None, 
                # but the key is the logging side effect.
                result = download_bulk_configs(mock_url, max_retries=3)
            except Exception:
                # Expected to fail eventually
                pass

    # Verify the number of calls (3 attempts)
    assert mock_get.call_count == 3, f"Expected 3 attempts, got {mock_get.call_count}"

    # Get the log output
    log_contents = log_stream.getvalue()

    # Verify the exact log format
    expected_log_line = f"[DATA_UNAVAILABLE] URL={mock_url} attempts=3"
    
    # Check if the specific line exists in the logs
    assert expected_log_line in log_contents, (
        f"Expected log line '{expected_log_line}' not found in logs. "
        f"Actual logs:\n{log_contents}"
    )

    logger.removeHandler(handler)


def test_download_success_on_retry():
    """
    Test that if the request succeeds on the 2nd attempt, 
    it returns the path and does NOT log the error.
    """
    mock_url = "https://materialsproject.org/api/real-endpoint"
    temp_file = Path("data/raw/test_structure.json")
    temp_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file.write_text("{}")

    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.ERROR)
    logger = logging.getLogger("code.data.download")
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)

    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First attempt fails
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("Temporary Fail")
            return mock_response
        else:
            # Second attempt succeeds
            mock_response = MagicMock()
            mock_response.json.return_value = {"structure": "mock"}
            mock_response.status_code = 200
            return mock_response

    with patch('code.data.download.requests.get', side_effect=side_effect):
        with patch('code.data.download.validate_citations', return_value=True):
            # Mock the internal save logic to just return the temp file
            with patch('code.data.download._save_structure', return_value=temp_file):
                result = download_bulk_configs(mock_url, max_retries=3)

    # Verify it only tried twice
    assert call_count == 2, f"Expected 2 attempts, got {call_count}"

    # Verify NO error log was produced
    log_contents = log_stream.getvalue()
    assert "[DATA_UNAVAILABLE]" not in log_contents, (
        "Error log should not appear if download succeeded on retry."
    )

    logger.removeHandler(handler)
    temp_file.unlink()
    if temp_file.parent.exists() and not any(temp_file.parent.iterdir()):
        temp_file.parent.rmdir()