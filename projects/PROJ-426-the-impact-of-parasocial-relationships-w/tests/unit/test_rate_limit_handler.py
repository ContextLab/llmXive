"""
Unit tests for rate_limit_handler.py
Verifies 429 handling, backoff integration, and error conditions.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from src.utils.rate_limit_handler import (
    RateLimitError,
    extract_retry_after,
    is_rate_limited,
    handle_429_response,
    rate_limit_handler,
    safe_api_call
)
from src.utils.retry_policy import RetryConfig


class TestRateLimitExtraction:
    def test_extract_retry_after_integer(self):
        headers = {'Retry-After': '60'}
        assert extract_retry_after(headers) == 60

    def test_extract_retry_after_missing(self):
        headers = {'Content-Type': 'application/json'}
        assert extract_retry_after(headers) is None

    def test_extract_retry_after_invalid_format(self):
        headers = {'Retry-After': 'invalid'}
        assert extract_retry_after(headers) is None

    def test_extract_retry_after_http_date(self):
        # Pushshift usually uses seconds, but test robustness
        headers = {'Retry-After': 'Wed, 21 Oct 2015 07:28:00 GMT'}
        # Our implementation expects integer, so this should return None
        assert extract_retry_after(headers) is None


class TestIsRateLimited:
    def test_is_rate_limited_true(self):
        assert is_rate_limited(429) is True

    def test_is_rate_limited_false(self):
        assert is_rate_limited(200) is False
        assert is_rate_limited(500) is False
        assert is_rate_limited(404) is False


class TestHandle429Response:
    def test_handle_429_with_retry_after_header(self):
        headers = {'Retry-After': '30'}
        config = RetryConfig(base_delay=1, max_delay=60, max_retries=3)
        
        delay = handle_429_response(429, headers, config, 0)
        assert delay == 30

    def test_handle_429_without_retry_after_header(self):
        headers = {}
        config = RetryConfig(base_delay=1, max_delay=60, max_retries=3)
        
        # Should use exponential backoff
        delay = handle_429_response(429, headers, config, 0)
        # Base delay is 1, so first attempt (0) should be 1 * (2^0) = 1
        assert delay == 1

    def test_handle_429_max_delay_cap(self):
        headers = {}
        config = RetryConfig(base_delay=10, max_delay=5, max_retries=3)
        
        # Attempt 5 would be huge, but capped at max_delay
        delay = handle_429_response(429, headers, config, 10)
        assert delay == 5

    def test_handle_429_raises_on_invalid_code(self):
        headers = {}
        config = RetryConfig()
        
        with pytest.raises(ValueError, match="handle_429_response should only be called for 429 status codes"):
            handle_429_response(200, headers, config, 0)


class TestRateLimitHandlerDecorator:
    @rate_limit_handler(RetryConfig(max_retries=0, base_delay=0, max_delay=0))
    def mock_api_call_success(self):
        mock_response = Mock()
        mock_response.status_code = 200
        return mock_response

    @rate_limit_handler(RetryConfig(max_retries=0, base_delay=0, max_delay=0))
    def mock_api_call_rate_limited(self):
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '0'} # Immediate retry for test speed
        return mock_response

    @rate_limit_handler(RetryConfig(max_retries=0, base_delay=0, max_delay=0))
    def mock_api_call_raises_rate_limit(self):
        exc = RateLimitError("Test", 0)
        exc.status_code = 429
        exc.headers = {}
        raise exc

    def test_decorator_success_response(self):
        result = self.mock_api_call_success()
        assert result.status_code == 200

    def test_decorator_exhausts_retries_on_429(self):
        with pytest.raises(RateLimitError):
            self.mock_api_call_rate_limited()

    def test_decorator_handles_exception_429(self):
        with pytest.raises(RateLimitError):
            self.mock_api_call_raises_rate_limit()


class TestSafeApiCall:
    def test_safe_api_call_wraps_correctly(self):
        config = RetryConfig(max_retries=1)
        
        @safe_api_call(config)
        def my_func():
            mock_resp = Mock()
            mock_resp.status_code = 200
            return mock_resp
        
        result = my_func()
        assert result.status_code == 200

    def test_safe_api_call_default_config(self):
        @safe_api_call()
        def my_func():
            mock_resp = Mock()
            mock_resp.status_code = 200
            return mock_resp
        
        result = my_func()
        assert result.status_code == 200