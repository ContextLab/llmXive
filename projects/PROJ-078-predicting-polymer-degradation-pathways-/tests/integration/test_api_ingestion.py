"""Integration tests for API ingestion and rate limiting."""
import pytest
import time
from utils import retry_with_backoff
import requests

class TestRateLimitBackoff:
    @pytest.mark.skip(reason="Requires external API or mock server setup")
    def test_backoff_on_rate_limit(self):
        """
        Test that the backoff mechanism triggers on rate limits.
        This requires a mock server that returns 429.
        """
        # Placeholder for integration test logic
        # In a real scenario, this would spin up a local server returning 429
        # and verify the retry logic delays execution.
        pass

    def test_retry_with_backoff_success(self):
        """Test that retry_with_backoff works for successful calls."""
        def mock_success():
            return "success"

        result = retry_with_backoff(mock_success, max_retries=3)
        assert result == "success"

    def test_retry_with_backoff_failure(self):
        """Test that retry_with_backoff raises after max retries."""
        def mock_failure():
            raise requests.exceptions.RequestException("Connection error")

        with pytest.raises(requests.exceptions.RequestException):
            retry_with_backoff(mock_failure, max_retries=3)
