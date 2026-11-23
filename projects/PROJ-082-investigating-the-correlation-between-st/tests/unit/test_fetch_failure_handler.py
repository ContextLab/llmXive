"""
Unit tests for the fetch_failure_handler module.

These tests verify that:
1. Real data fetches succeed normally
2. Network failures raise FetchFailureError
3. No synthetic data fallback occurs
4. Data integrity validation works correctly
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from extraction.fetch_failure_handler import (
    fetch_with_strict_failure,
    validate_data_integrity,
    FetchFailureError
)
from utils.logger import get_logger


class TestFetchFailureHandler(unittest.TestCase):
    """Test cases for fetch_failure_handler module."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = get_logger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def test_successful_fetch_returns_data(self):
        """Test that a successful fetch returns the data."""
        def mock_success_fetch():
            return "real data content"
        
        result = fetch_with_strict_failure(
            mock_success_fetch,
            "Test Source",
            self.logger
        )
        
        self.assertEqual(result, "real data content")

    def test_network_error_raises_fetch_failure_error(self):
        """Test that network errors raise FetchFailureError."""
        def mock_network_error():
            raise ConnectionError("Network is unreachable")
        
        with self.assertRaises(FetchFailureError) as context:
            fetch_with_strict_failure(
                mock_network_error,
                "Test Source",
                self.logger
            )
        
        self.assertIn("Network error", str(context.exception))
        self.assertIn("Network is unreachable", str(context.exception))

    def test_http_error_raises_fetch_failure_error(self):
        """Test that HTTP errors raise FetchFailureError."""
        def mock_http_error():
            from urllib.error import HTTPError
            raise HTTPError("http://example.com", 404, "Not Found", {}, None)
        
        with self.assertRaises(FetchFailureError) as context:
            fetch_with_strict_failure(
                mock_http_error,
                "Test Source",
                self.logger
            )
        
        self.assertIn("404", str(context.exception))
        self.assertIn("Not Found", str(context.exception))

    def test_none_result_raises_fetch_failure_error(self):
        """Test that None results raise FetchFailureError."""
        def mock_none_result():
            return None
        
        with self.assertRaises(FetchFailureError) as context:
            fetch_with_strict_failure(
                mock_none_result,
                "Test Source",
                self.logger
            )
        
        self.assertIn("returned None", str(context.exception))

    def test_synthetic_marker_raises_fetch_failure_error(self):
        """Test that synthetic data markers raise FetchFailureError."""
        synthetic_data = [
            "This is synthetic data",
            "mock data here",
            "fake placeholder content",
            "generated_at: 2024-01-01"
        ]
        
        for data in synthetic_data:
            def mock_synthetic_fetch():
                return data
            
            with self.assertRaises(FetchFailureError) as context:
                fetch_with_strict_failure(
                    mock_synthetic_fetch,
                    "Test Source",
                    self.logger
                )
            
            self.assertIn("synthetic", str(context.exception).lower() or 
                         "mock", str(context.exception).lower() or
                         "fake", str(context.exception).lower())

    def test_data_integrity_validation_passes(self):
        """Test that valid data passes integrity validation."""
        valid_data = "some real data content"
        
        result = validate_data_integrity(
            valid_data,
            expected_min_size=5,
            data_source_name="Test Source"
        )
        
        self.assertTrue(result)

    def test_data_integrity_validation_fails_on_none(self):
        """Test that None data fails integrity validation."""
        with self.assertRaises(FetchFailureError) as context:
            validate_data_integrity(
                None,
                expected_min_size=0,
                data_source_name="Test Source"
            )
        
        self.assertIn("Data is None", str(context.exception))

    def test_data_integrity_validation_fails_on_small_data(self):
        """Test that data smaller than minimum fails validation."""
        small_data = "hi"  # Length 2
        
        with self.assertRaises(FetchFailureError) as context:
            validate_data_integrity(
                small_data,
                expected_min_size=10,
                data_source_name="Test Source"
            )
        
        self.assertIn("less than required minimum", str(context.exception))

    def test_empty_list_fails_integrity_validation(self):
        """Test that empty list fails integrity validation."""
        empty_list = []
        
        with self.assertRaises(FetchFailureError) as context:
            validate_data_integrity(
                empty_list,
                expected_min_size=1,
                data_source_name="Test Source"
            )
        
        self.assertIn("less than required minimum", str(context.exception))

    def test_no_synthetic_fallback_on_failure(self):
        """
        Critical test: Verify that no synthetic data is returned
        when fetch fails. This is the core requirement of T047.
        """
        def mock_fail_then_return_synthetic():
            # This simulates a bad implementation that might try to fallback
            raise ConnectionError("Network failed")
            # The following line should never be reached
            return "synthetic_fallback_data"
        
        with self.assertRaises(FetchFailureError):
            fetch_with_strict_failure(
                mock_fail_then_return_synthetic,
                "Test Source",
                self.logger
            )
        
        # If we reach here, the exception was raised as expected
        # and no synthetic data was returned


class TestFetchFailureHandlerIntegration(unittest.TestCase):
    """Integration tests for fetch_failure_handler."""

    def test_real_url_fetch_failure(self):
        """Test with a real but unreachable URL."""
        def mock_real_unreachable_fetch():
            import requests
            try:
                response = requests.get(
                    "http://this-domain-should-not-exist-12345.com/data.csv",
                    timeout=2
                )
                response.raise_for_status()
                return response.text
            except Exception:
                raise  # Re-raise to be caught by wrapper
        
        with self.assertRaises(FetchFailureError):
            fetch_with_strict_failure(
                mock_real_unreachable_fetch,
                "Real Unreachable URL",
                get_logger(__name__)
            )

    def test_timeout_failure(self):
        """Test that timeout errors are handled correctly."""
        def mock_timeout_fetch():
            import socket
            raise socket.timeout("Connection timed out")
        
        with self.assertRaises(FetchFailureError) as context:
            fetch_with_strict_failure(
                mock_timeout_fetch,
                "Test Timeout",
                get_logger(__name__)
            )
        
        self.assertIn("timeout", str(context.exception).lower())


if __name__ == '__main__':
    unittest.main()