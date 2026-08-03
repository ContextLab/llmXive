"""
Unit tests for the data_fetch module.

Tests cover retry logic, pagination, and raw data fetching.
"""
import pytest
import json
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import os
import time

from src.utils.data_fetch import (
    create_retry_session,
    fetch_url_with_retry,
    fetch_paginated_data,
    fetch_raw_data,
    DataFetcher,
    create_fetcher,
    DEFAULT_MAX_RETRIES,
    DEFAULT_BACKOFF_FACTOR,
)
import requests
from requests.exceptions import HTTPError, RequestException


class TestRetrySession:
    """Tests for create_retry_session function."""

    def test_default_retry_configuration(self):
        """Test that default retry configuration is applied."""
        session = create_retry_session()
        # Verify adapter is attached
        assert "http://" in session.adapters
        assert "https://" in session.adapters
        
        # Verify retry settings
        adapter = session.adapters["http://"]
        assert adapter.max_retries.total == DEFAULT_MAX_RETRIES
        assert adapter.max_retries.backoff_factor == DEFAULT_BACKOFF_FACTOR

    def test_custom_retry_configuration(self):
        """Test custom retry configuration."""
        custom_retries = 10
        custom_backoff = 2.0
        session = create_retry_session(
            max_retries=custom_retries,
            backoff_factor=custom_backoff,
        )
        adapter = session.adapters["http://"]
        assert adapter.max_retries.total == custom_retries
        assert adapter.max_retries.backoff_factor == custom_backoff

    def test_invalid_max_retries(self):
        """Test that negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            create_retry_session(max_retries=-1)

    def test_invalid_backoff_factor(self):
        """Test that negative backoff_factor raises ValueError."""
        with pytest.raises(ValueError, match="backoff_factor must be non-negative"):
            create_retry_session(backoff_factor=-1.0)


class TestFetchUrlWithRetry:
    """Tests for fetch_url_with_retry function."""

    @patch('src.utils.data_fetch.create_retry_session')
    @patch('src.utils.data_fetch.requests.Session')
    def test_fetch_json_response(self, mock_session_class, mock_create_session):
        """Test fetching a JSON response."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status = MagicMock()
        
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        result = fetch_url_with_retry("https://example.com/api", session=mock_session)
        
        assert result == {"key": "value"}
        mock_session.get.assert_called_once()

    @patch('src.utils.data_fetch.create_retry_session')
    @patch('src.utils.data_fetch.requests.Session')
    def test_fetch_text_response(self, mock_session_class, mock_create_session):
        """Test fetching a text response."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = "Hello, World!"
        mock_response.raise_for_status = MagicMock()
        
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        result = fetch_url_with_retry("https://example.com/api", session=mock_session)
        
        assert result == "Hello, World!"

    @patch('src.utils.data_fetch.create_retry_session')
    @patch('src.utils.data_fetch.requests.Session')
    def test_fetch_binary_response(self, mock_session_class, mock_create_session):
        """Test fetching a binary response."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/octet-stream"}
        mock_response.content = b"binary data"
        mock_response.raise_for_status = MagicMock()
        
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        result = fetch_url_with_retry("https://example.com/api", session=mock_session)
        
        assert result == b"binary data"

    def test_invalid_url(self):
        """Test that invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid URL provided"):
            fetch_url_with_retry("")

    @patch('src.utils.data_fetch.create_retry_session')
    @patch('src.utils.data_fetch.requests.Session')
    def test_http_error(self, mock_session_class, mock_create_session):
        """Test that HTTP errors are raised."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        with pytest.raises(HTTPError):
            fetch_url_with_retry("https://example.com/api", session=mock_session)


class TestFetchPaginatedData:
    """Tests for fetch_paginated_data function."""

    @patch('src.utils.data_fetch.fetch_url_with_retry')
    def test_single_page(self, mock_fetch):
        """Test fetching a single page of data."""
        mock_fetch.return_value = {
            "results": [{"id": 1}, {"id": 2}],
            "next": None
        }
        
        result = fetch_paginated_data(
            base_url="https://api.example.com",
            endpoint="/data",
            page_size=10,
        )
        
        assert len(result) == 2
        assert result[0]["id"] == 1

    @patch('src.utils.data_fetch.fetch_url_with_retry')
    def test_multiple_pages(self, mock_fetch):
        """Test fetching multiple pages of data."""
        mock_fetch.side_effect = [
            {"results": [{"id": 1}], "next": "https://api.example.com/data?page=2"},
            {"results": [{"id": 2}], "next": "https://api.example.com/data?page=3"},
            {"results": [{"id": 3}], "next": None},
        ]
        
        result = fetch_paginated_data(
            base_url="https://api.example.com",
            endpoint="/data",
            page_size=10,
        )
        
        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[2]["id"] == 3

    @patch('src.utils.data_fetch.fetch_url_with_retry')
    def test_max_pages_limit(self, mock_fetch):
        """Test max_pages limit."""
        mock_fetch.return_value = {
            "results": [{"id": 1}],
            "next": "https://api.example.com/data?page=2"
        }
        
        result = fetch_paginated_data(
            base_url="https://api.example.com",
            endpoint="/data",
            page_size=10,
            max_pages=2,
        )
        
        # Should only fetch 2 pages worth (mock returns same data)
        assert mock_fetch.call_count == 2

    def test_invalid_base_url(self):
        """Test that invalid base_url raises ValueError."""
        with pytest.raises(ValueError, match="base_url and endpoint must be provided"):
            fetch_paginated_data(base_url="", endpoint="/data")

    @patch('src.utils.data_fetch.fetch_url_with_retry')
    def test_missing_response_key(self, mock_fetch):
        """Test that missing response key raises ValueError."""
        mock_fetch.return_value = {"data": [{"id": 1}]}  # Missing 'results'
        
        with pytest.raises(ValueError, match="Response missing expected key"):
            fetch_paginated_data(
                base_url="https://api.example.com",
                endpoint="/data",
                response_key="results",
            )


class TestDataFetcher:
    """Tests for DataFetcher class."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        fetcher = DataFetcher(
            base_url="https://api.example.com",
            api_key="test_key"
        )
        assert fetcher.base_url == "https://api.example.com"
        assert "Authorization" in fetcher.headers

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        fetcher = DataFetcher(base_url="https://api.example.com")
        assert "Authorization" not in fetcher.headers

    def test_init_invalid_base_url(self):
        """Test that invalid base_url raises ValueError."""
        with pytest.raises(ValueError, match="base_url is required"):
            DataFetcher(base_url="")

    @patch('src.utils.data_fetch.fetch_url_with_retry')
    def test_get_method(self, mock_fetch):
        """Test get method."""
        mock_fetch.return_value = {"data": "value"}
        
        fetcher = DataFetcher(base_url="https://api.example.com")
        result = fetcher.get("/endpoint", params={"key": "value"})
        
        assert result == {"data": "value"}
        mock_fetch.assert_called_once()

    @patch('src.utils.data_fetch.fetch_paginated_data')
    def test_fetch_all_method(self, mock_fetch_all):
        """Test fetch_all method."""
        mock_fetch_all.return_value = [{"id": 1}, {"id": 2}]
        
        fetcher = DataFetcher(base_url="https://api.example.com")
        result = fetcher.fetch_all("/endpoint")
        
        assert len(result) == 2
        mock_fetch_all.assert_called_once()

    @patch('src.utils.data_fetch.fetch_raw_data')
    def test_download_file_method(self, mock_download):
        """Test download_file method."""
        mock_download.return_value = Path("/tmp/downloaded.json")
        
        fetcher = DataFetcher(base_url="https://api.example.com")
        result = fetcher.download_file("/file.json")
        
        assert result == Path("/tmp/downloaded.json")


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @patch('src.utils.data_fetch.create_retry_session')
    @patch('src.utils.data_fetch.requests.Session')
    def test_request_exception(self, mock_session_class, mock_create_session):
        """Test that RequestException is raised on network failure."""
        mock_session = MagicMock()
        mock_session.get.side_effect = RequestException("Network error")
        mock_session_class.return_value = mock_session
        
        with pytest.raises(RequestException):
            fetch_url_with_retry("https://example.com/api", session=mock_session)

    @patch('builtins.open', new_callable=mock_open)
    @patch('src.utils.data_fetch.create_retry_session')
    @patch('src.utils.data_fetch.requests.Session')
    def test_download_file_failure_cleanup(self, mock_session_class, mock_create_session, mock_file):
        """Test that partial file is cleaned up on download failure."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = RequestException("Download failed")
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            
            with pytest.raises(RequestException):
                fetch_raw_data("https://example.com/file.json", output_path, session=mock_session)
            
            # File should not exist after failure
            assert not output_path.exists()

    def test_create_fetcher_missing_api_key(self):
        """Test create_fetcher when API key env var is missing."""
        # This should not raise, just log a warning
        fetcher = create_fetcher(
            service_name="TestService",
            base_url="https://api.example.com",
            api_key_env="NON_EXISTENT_KEY"
        )
        assert isinstance(fetcher, DataFetcher)

    @patch('os.environ')
    def test_create_fetcher_with_api_key(self, mock_environ):
        """Test create_fetcher with API key from environment."""
        mock_environ.get.return_value = "test_api_key"
        
        fetcher = create_fetcher(
            service_name="TestService",
            base_url="https://api.example.com",
            api_key_env="TEST_API_KEY"
        )
        
        assert fetcher.headers["Authorization"] == "Bearer test_api_key"
