"""
Integration test for data_fetcher retry logic (T056).
Simulates network failures and verifies exponential backoff.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from urllib.error import URLError

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.data_fetcher import fetch_with_retry, load_config, FetchError

def test_exponential_backoff():
    """Verify that retry logic uses exponential backoff."""
    # Mock the requests.get to always fail
    with patch('code.utils.data_fetcher.requests.get') as mock_get:
        mock_get.side_effect = URLError("Network error")
        
        # We need to ensure the config is loaded with a small delay for testing
        # But we can't easily patch the config file read in a unit test without creating a temp file.
        # Instead, we verify the logic by checking the time taken for 3 retries.
        
        start_time = time.time()
        try:
            # This should raise FetchError after max retries
            fetch_with_retry("http://example.com/fail", max_retries=3, base_delay=0.1, delay_multiplier=2.0)
        except FetchError:
            pass
        
        end_time = time.time()
        duration = end_time - start_time

        # Expected delays: 0.1, 0.2, 0.4 (before 3rd retry attempt fails? or after?)
        # Logic: Retry 1 (delay 0.1), Retry 2 (delay 0.2), Retry 3 (delay 0.4) -> Fail
        # Total sleep time: 0.1 + 0.2 + 0.4 = 0.7 seconds
        # We expect the duration to be at least 0.7 seconds (plus overhead)
        
        assert duration >= 0.6, f"Exponential backoff not working. Duration: {duration}s (expected >= 0.6s)"
        assert duration < 2.0, f"Duration too long: {duration}s"

def test_max_retries_exceeded():
    """Verify that FetchError is raised after max retries."""
    with patch('code.utils.data_fetcher.requests.get') as mock_get:
        mock_get.side_effect = URLError("Network error")
        
        with pytest.raises(FetchError):
            fetch_with_retry("http://example.com/fail", max_retries=2, base_delay=0.01)
