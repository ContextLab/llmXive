"""
Unit tests for download.py retry logic and log formatting.
Verifies:
1. The exact log format for [DATA_UNAVAILABLE] matches specification.
2. The retry mechanism attempts exactly 3 times before failing.
"""
import logging
import io
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.download import download_bulk_configs
from validators import validate_citations

def test_download_retry_count_and_log_format():
    """
    Test that download_bulk_configs attempts exactly 3 retries
    and logs the exact format: [DATA_UNAVAILABLE] URL=<url> attempts=3
    """
    # Setup in-memory log capture
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.ERROR)
    
    logger = logging.getLogger("data.download")
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)

    # Mock the validate_citations to pass (so we hit the download logic)
    # Mock requests.head to always fail
    with patch('data.download.validate_citations', return_value=True):
        with patch('data.download.requests.head') as mock_head:
            mock_head.side_effect = Exception("Network Error")
            
            # Call the function with a dummy URL
            # Note: The function expects a URL that points to a directory or file list.
            # We pass a dummy URL to trigger the retry loop.
            dummy_url = "https://fake-mp-source.invalid/test"
            
            try:
                # We expect this to raise an error after 3 attempts
                # The implementation in T013 should catch exceptions and retry
                download_bulk_configs(dummy_url, max_retries=3)
            except Exception:
                pass # Expected to fail

    # Remove handler
    logger.removeHandler(handler)

    # Get log output
    log_output = log_stream.getvalue()

    # Verify the exact log format
    # Expected format: [DATA_UNAVAILABLE] URL=<url> attempts=3
    expected_log_fragment = f"[DATA_UNAVAILABLE] URL={dummy_url} attempts=3"
    
    assert expected_log_fragment in log_output, (
        f"Log output did not match expected format.\n"
        f"Expected fragment: {expected_log_fragment}\n"
        f"Actual log output: {log_output}"
    )

    # Verify it was called exactly 3 times (1 initial + 2 retries, or 3 total attempts)
    # The logic in T013 should loop 3 times.
    assert mock_head.call_count == 3, (
        f"Expected 3 attempts, but requests.head was called {mock_head.call_count} times."
    )

    print("Test passed: Log format and retry count verified.")

if __name__ == "__main__":
    test_download_retry_count_and_log_format()
    print("All tests in test_download_retry.py passed.")