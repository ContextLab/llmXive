"""
Integration test for API retry logic and error handling.

This test verifies that the fetch_with_retry and fetch_text_with_retry functions
in code/utils/data_fetcher.py correctly implement exponential backoff and error
handling as specified in T006.

The test uses a local mock server to simulate:
1. Successful response on first attempt
2. Server error (500) followed by success
3. Connection timeout
4. HTTP 404 error (no retry expected for client errors)
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from urllib.error import URLError, HTTPError
from typing import Optional

# Import the module under test
# Note: Using relative import structure matching the project layout
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.data_fetcher import fetch_with_retry, fetch_text_with_retry, FetchError


class MockResponse:
    """Mock response object simulating urllib response"""
    def __init__(self, status_code: int, data: bytes = b''):
        self.status = status_code
        self.data = data
        self._read_count = 0

    def read(self) -> bytes:
        return self.data

    def getcode(self) -> int:
        return self.status


class MockURLError:
    """Mock URLError for testing timeout scenarios"""
    def __init__(self, reason: str = "Connection timed out"):
        self.reason = reason


class TestRetryLogic:
    """Integration tests for retry logic and error handling"""

    @pytest.fixture
    def mock_success_response(self):
        """Fixture providing a successful mock response"""
        return MockResponse(200, b'{"status": "ok", "data": [1, 2, 3]}')

    @pytest.fixture
    def mock_server_error_response(self):
        """Fixture providing a server error response"""
        return MockResponse(500, b'{"error": "Internal Server Error"}')

    @pytest.fixture
    def mock_not_found_response(self):
        """Fixture providing a 404 response"""
        return MockResponse(404, b'{"error": "Not Found"}')

    def test_successful_fetch_no_retry(self, mock_success_response):
        """Test that successful fetch returns immediately without retries"""
        call_count = 0

        def mock_urlopen(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_success_response

        with patch('utils.data_fetcher.urlopen', side_effect=mock_urlopen):
            result = fetch_with_retry("http://example.com/api/data", max_retries=3)

        assert result.status == 200
        assert call_count == 1  # Should succeed on first try

    def test_retry_on_server_error(self, mock_server_error_response, mock_success_response):
        """Test that server errors trigger retry with exponential backoff"""
        call_count = 0

        def mock_urlopen(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return mock_server_error_response
            return mock_success_response

        with patch('utils.data_fetcher.urlopen', side_effect=mock_urlopen):
            # Use very short backoff for testing (0.01s)
            result = fetch_with_retry(
                "http://example.com/api/data",
                max_retries=3,
                base_delay=0.01
            )

        assert result.status == 200
        assert call_count == 3  # Failed twice, succeeded on third

    def test_no_retry_on_client_error(self, mock_not_found_response):
        """Test that client errors (4xx) do not trigger retries"""
        call_count = 0

        def mock_urlopen(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_not_found_response

        with patch('utils.data_fetcher.urlopen', side_effect=mock_urlopen):
            with pytest.raises(FetchError) as exc_info:
                fetch_with_retry("http://example.com/api/data", max_retries=3)

        assert call_count == 1  # Should not retry on 404
        assert "404" in str(exc_info.value)

    def test_retry_on_timeout(self):
        """Test that URLError (timeout) triggers retry"""
        call_count = 0

        def mock_urlopen(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise URLError("Connection timed out")
            return MockResponse(200, b'{"success": true}')

        with patch('utils.data_fetcher.urlopen', side_effect=mock_urlopen):
            result = fetch_with_retry(
                "http://example.com/api/data",
                max_retries=3,
                base_delay=0.01
            )

        assert result.status == 200
        assert call_count == 2

    def test_max_retries_exceeded(self, mock_server_error_response):
        """Test that FetchError is raised when all retries are exhausted"""
        def mock_urlopen(*args, **kwargs):
            return mock_server_error_response

        with patch('utils.data_fetcher.urlopen', side_effect=mock_urlopen):
            with pytest.raises(FetchError) as exc_info:
                fetch_with_retry(
                    "http://example.com/api/data",
                    max_retries=2,
                    base_delay=0.01
                )

        assert "Max retries exceeded" in str(exc_info.value)
        assert "500" in str(exc_info.value)

    def test_exponential_backoff_timing(self, mock_server_error_response, mock_success_response):
        """Test that delays between retries follow exponential backoff pattern"""
        call_times = []

        def mock_urlopen(*args, **kwargs):
            call_times.append(time.time())
            if len(call_times) < 3:
                return mock_server_error_response
            return mock_success_response

        base_delay = 0.05  # 50ms for faster testing
        with patch('utils.data_fetcher.urlopen', side_effect=mock_urlopen):
            fetch_with_retry(
                "http://example.com/api/data",
                max_retries=3,
                base_delay=base_delay
            )

        # Verify exponential backoff: delays should be approximately
        # base_delay, base_delay*2, etc.
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]

            # Allow 50% tolerance for timing variations
            assert base_delay <= delay1 <= base_delay * 3, f"First delay {delay1} not in expected range"
            assert base_delay * 1.5 <= delay2 <= base_delay * 4, f"Second delay {delay2} not in expected range (should be longer than first)"

    def test_fetch_text_with_retry(self, mock_success_response):
        """Test that fetch_text_with_retry correctly decodes response"""
        def mock_urlopen(*args, **kwargs):
            return mock_success_response

        with patch('utils.data_fetcher.urlopen', side_effect=mock_urlopen):
            result = fetch_text_with_retry("http://example.com/api/data", max_retries=3)

        assert result == '{"status": "ok", "data": [1, 2, 3]}'

    def test_fetch_text_retry_on_timeout(self):
        """Test that fetch_text_with_retry handles timeouts correctly"""
        call_count = 0

        def mock_urlopen(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise URLError("Connection timed out")
            return MockResponse(200, b'{"text": "success"}')

        with patch('utils.data_fetcher.urlopen', side_effect=mock_urlopen):
            result = fetch_text_with_retry(
                "http://example.com/api/data",
                max_retries=3,
                base_delay=0.01
            )

        assert result == '{"text": "success"}'
        assert call_count == 2

    def test_invalid_url_handling(self):
        """Test handling of invalid URLs"""
        with pytest.raises(FetchError):
            fetch_with_retry("http://invalid.url.that.does.not.exist.test", max_retries=1)

    def test_retry_count_logging(self, mock_server_error_response, mock_success_response, caplog):
        """Test that retry attempts are logged appropriately"""
        import logging

        def mock_urlopen(*args, **kwargs):
            if mock_urlopen.call_count < 2:
                mock_urlopen.call_count += 1
                return mock_server_error_response
            return mock_success_response

        mock_urlopen.call_count = 0

        with patch('utils.data_fetcher.urlopen', side_effect=mock_urlopen):
            with caplog.at_level(logging.INFO):
                fetch_with_retry(
                    "http://example.com/api/data",
                    max_retries=3,
                    base_delay=0.01
                )

        # Verify that retry attempts were logged
        assert any("retry" in msg.lower() for msg in caplog.messages)