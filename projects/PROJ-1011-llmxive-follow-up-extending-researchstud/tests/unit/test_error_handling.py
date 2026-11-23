"""
Tests for error handling infrastructure (T008).

Verifies that the system fails loudly on data fetch errors
and does not silently fall back to synthetic data.
"""
import pytest
import requests
from unittest.mock import patch, MagicMock
from requests.exceptions import Timeout, ConnectionError, RequestException
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.error_handling import (
    DataFetchError,
    fetch_with_strict_handling,
    validate_data_response,
    handle_fetch_failure
)


class TestDataFetchError:
    """Tests for the DataFetchError exception class."""

    def test_basic_instantiation(self):
        """Test creating a basic DataFetchError."""
        error = DataFetchError("Test error message")
        assert "Test error message" in str(error)
        assert error.source is None
        assert error.details == {}

    def test_with_source(self):
        """Test creating DataFetchError with source."""
        error = DataFetchError("Test error", source="https://example.com")
        assert "https://example.com" in str(error)
        assert error.source == "https://example.com"

    def test_with_details(self):
        """Test creating DataFetchError with details."""
        details = {"status": 404, "reason": "Not Found"}
        error = DataFetchError("Test error", details=details)
        assert "status" in str(error)
        assert error.details == details


class TestFetchWithStrictHandling:
    """Tests for fetch_with_strict_handling function."""

    @patch('utils.error_handling.requests.get')
    def test_successful_fetch(self, mock_get):
        """Test successful fetch returns response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        response = fetch_with_strict_handling("https://example.com")
        assert response == mock_response
        mock_get.assert_called_once()

    @patch('utils.error_handling.requests.get')
    def test_http_error_raises_data_fetch_error(self, mock_get):
        """Test that HTTP errors raise DataFetchError."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_get.return_value = mock_response

        with pytest.raises(DataFetchError) as exc_info:
            fetch_with_strict_handling("https://example.com")
        
        assert "403" in str(exc_info.value)
        assert "Forbidden" in str(exc_info.value)

    @patch('utils.error_handling.requests.get')
    def test_timeout_retries_then_raises(self, mock_get):
        """Test that timeout errors are retried and then raise DataFetchError."""
        mock_get.side_effect = Timeout("Connection timed out")

        with pytest.raises(DataFetchError) as exc_info:
            fetch_with_strict_handling("https://example.com", max_retries=2)
        
        assert "retries" in str(exc_info.value)
        assert mock_get.call_count == 2  # Retried twice

    @patch('utils.error_handling.requests.get')
    def test_connection_error_raises(self, mock_get):
        """Test that connection errors raise DataFetchError."""
        mock_get.side_effect = ConnectionError("Network unreachable")

        with pytest.raises(DataFetchError) as exc_info:
            fetch_with_strict_handling("https://example.com")
        
        assert "connect" in str(exc_info.value).lower()

    @patch('utils.error_handling.requests.get')
    def test_invalid_json_in_response_raises(self, mock_get):
        """Test that invalid JSON in response raises DataFetchError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.headers = {"Content-Type": "application/json"}
        mock_get.return_value = mock_response

        with pytest.raises(DataFetchError) as exc_info:
            fetch_with_strict_handling("https://example.com")
        
        assert "Invalid JSON" in str(exc_info.value)


class TestValidateDataResponse:
    """Tests for validate_data_response function."""

    def test_valid_json_with_required_fields(self):
        """Test validation passes when required fields are present."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"title": "Test", "abstract": "Test abstract"}
        mock_response.headers = {"Content-Type": "application/json"}

        # Should not raise
        validate_data_response(mock_response, required_fields=["title", "abstract"])

    def test_missing_required_fields_raises(self):
        """Test validation fails when required fields are missing."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"title": "Test"}
        mock_response.headers = {"Content-Type": "application/json"}

        with pytest.raises(DataFetchError) as exc_info:
            validate_data_response(mock_response, required_fields=["title", "abstract"])
        
        assert "missing required fields" in str(exc_info.value).lower()
        assert "abstract" in str(exc_info.value)

    def test_204_no_content_raises(self):
        """Test that 204 No Content raises DataFetchError."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.headers = {}

        with pytest.raises(DataFetchError) as exc_info:
            validate_data_response(mock_response)
        
        assert "204" in str(exc_info.value)


class TestHandleFetchFailure:
    """Tests for handle_fetch_failure function."""

    def test_re_raises_data_fetch_error(self):
        """Test that handle_fetch_failure re-raises DataFetchError."""
        original_error = DataFetchError("Original error", source="test")
        
        with pytest.raises(DataFetchError) as exc_info:
            handle_fetch_failure("test_source", original_error)
        
        assert exc_info.value is original_error

    def test_wraps_other_exception_in_data_fetch_error(self):
        """Test that handle_fetch_failure wraps other exceptions."""
        original_error = ValueError("Something went wrong")
        
        with pytest.raises(DataFetchError) as exc_info:
            handle_fetch_failure("test_source", original_error)
        
        assert "Something went wrong" in str(exc_info.value)
        assert "test_source" in str(exc_info.value)

    def test_wraps_exception_with_cause(self):
        """Test that the original exception is preserved as the cause."""
        original_error = ValueError("Original")
        
        with pytest.raises(DataFetchError) as exc_info:
            handle_fetch_failure("test", original_error)
        
        assert exc_info.value.__cause__ is original_error
