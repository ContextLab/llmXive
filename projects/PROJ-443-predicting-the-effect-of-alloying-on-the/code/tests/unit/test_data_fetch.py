"""
Unit tests for data_fetch module.
"""
import pytest
import json
from unittest.mock import patch, MagicMock, mock_open, call
from pathlib import Path
import tempfile
import os
import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.data_fetch import (
    create_retry_session,
    fetch_url_with_retry,
    fetch_paginated_data,
    fetch_raw_data,
    DataFetcher,
    create_fetcher,
    DEFAULT_MAX_RETRIES,
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_TIMEOUT
)


class TestRetrySession:
    """Tests for create_retry_session function."""

    def test_creates_session_with_retries(self):
        session = create_retry_session()
        assert session is not None
        # Check that adapters are mounted
        assert "http://" in session.adapters
        assert "https://" in session.adapters

    def test_custom_max_retries(self):
        session = create_retry_session(max_retries=5)
        adapter = session.adapters["http://"]
        assert adapter.max_retries.total == 5

    def test_custom_backoff_factor(self):
        session = create_retry_session(backoff_factor=2.0)
        adapter = session.adapters["http://"]
        # The retry object holds the backoff factor
        assert adapter.max_retries.backoff_factor == 2.0

    def test_custom_user_agent(self):
        custom_agent = "Test-Agent/1.0"
        session = create_retry_session(user_agent=custom_agent)
        assert session.headers["User-Agent"] == custom_agent

    def test_status_forcelist(self):
        custom_list = [404, 500]
        session = create_retry_session(status_forcelist=custom_list)
        adapter = session.adapters["http://"]
        assert adapter.max_retries.status_forcelist == set(custom_list)


class TestFetchUrlWithRetry:
    """Tests for fetch_url_with_retry function."""

    @patch('src.utils.data_fetch.requests.Session')
    def test_success(self, mock_session_class):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = fetch_url_with_retry("http://test.com/api", session=mock_session)
        
        assert result == {"key": "value"}
        mock_session.get.assert_called_once_with("http://test.com/api", params=None, timeout=DEFAULT_TIMEOUT)

    @patch('src.utils.data_fetch.requests.Session')
    def test_json_decode_error(self, mock_session_class):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "not json"
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = fetch_url_with_retry("http://test.com/api", session=mock_session)
        
        assert "raw_text" in result
        assert "_parse_error" in result
        assert result["raw_text"] == "not json"

    @patch('src.utils.data_fetch.requests.Session')
    def test_request_exception(self, mock_session_class):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.exceptions.RequestException("Network error")
        mock_session_class.return_value = mock_session

        with pytest.raises(requests.exceptions.RequestException):
            fetch_url_with_retry("http://test.com/api", session=mock_session)

    @patch('src.utils.data_fetch.create_retry_session')
    def test_creates_session_if_none(self, mock_create):
        mock_session = MagicMock()
        mock_create.return_value = mock_session
        
        fetch_url_with_retry("http://test.com/api")
        
        mock_create.assert_called_once()


class TestFetchPaginatedData:
    """Tests for fetch_paginated_data function."""

    @patch('src.utils.data_fetch.requests.Session')
    def test_single_page(self, mock_session_class):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1}, {"id": 2}]
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = fetch_paginated_data("http://test.com/api", session=mock_session, per_page_size=10)
        
        assert len(result) == 2
        assert result[0]["id"] == 1

    @patch('src.utils.data_fetch.requests.Session')
    def test_multiple_pages(self, mock_session_class):
        mock_session = MagicMock()
        
        # Mock responses for 2 pages
        resp1 = MagicMock()
        resp1.status_code = 200
        resp1.json.return_value = [{"id": 1}, {"id": 2}]
        
        resp2 = MagicMock()
        resp2.status_code = 200
        resp2.json.return_value = [{"id": 3}] # Fewer items, end of data
        
        mock_session.get.side_effect = [resp1, resp2]
        mock_session_class.return_value = mock_session

        result = fetch_paginated_data("http://test.com/api", session=mock_session, per_page_size=10)
        
        assert len(result) == 3
        assert mock_session.get.call_count == 2

    @patch('src.utils.data_fetch.requests.Session')
    def test_max_pages_limit(self, mock_session_class):
        mock_session = MagicMock()
        
        # Mock responses for 3 pages
        for i in range(3):
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = [{"id": i}]
            resp.raise_for_status = MagicMock()
            
        mock_session.get.side_effect = [MagicMock(json=lambda: [{"id": 1}]), 
                                        MagicMock(json=lambda: [{"id": 2}]), 
                                        MagicMock(json=lambda: [{"id": 3}])]
        mock_session_class.return_value = mock_session

        result = fetch_paginated_data("http://test.com/api", session=mock_session, max_pages=2, per_page_size=10)
        
        # Should only fetch 2 pages
        assert mock_session.get.call_count == 2
        assert len(result) == 2

    @patch('src.utils.data_fetch.requests.Session')
    def test_data_key_extraction(self, mock_session_class):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"id": 1}, {"id": 2}], "total": 2}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = fetch_paginated_data("http://test.com/api", session=mock_session, data_key="results")
        
        assert len(result) == 2
        assert result[0]["id"] == 1


class TestDataFetcher:
    """Tests for DataFetcher class."""

    def test_init_without_api_key(self):
        fetcher = DataFetcher("http://test.com")
        assert fetcher.base_url == "http://test.com"
        assert fetcher.api_key is None
        assert fetcher.session is not None

    def test_init_with_api_key(self):
        fetcher = DataFetcher("http://test.com", api_key="secret123")
        assert fetcher.api_key == "secret123"
        assert "Authorization" in fetcher.session.headers

    @patch('src.utils.data_fetch.fetch_url_with_retry')
    def test_get_method(self, mock_fetch):
        mock_fetch.return_value = {"data": "value"}
        fetcher = DataFetcher("http://test.com")
        
        result = fetcher.get("/endpoint", params={"q": "test"})
        
        mock_fetch.assert_called_once()
        assert result == {"data": "value"}

    @patch('src.utils.data_fetch.fetch_paginated_data')
    def test_fetch_all_paginated_method(self, mock_fetch):
        mock_fetch.return_value = [{"id": 1}, {"id": 2}]
        fetcher = DataFetcher("http://test.com")
        
        result = fetcher.fetch_all_paginated("/endpoint", per_page_size=10)
        
        mock_fetch.assert_called_once()
        assert len(result) == 2

    @patch('src.utils.data_fetch.fetch_raw_data')
    def test_download_raw_method(self, mock_fetch):
        mock_fetch.return_value = Path("/tmp/test.json")
        fetcher = DataFetcher("http://test.com")
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            result = fetcher.download_raw("/endpoint", tmp_path)
            assert result == Path(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestCreateFetcher:
    """Tests for create_fetcher factory function."""

    @patch('src.utils.data_fetch.DataFetcher')
    def test_creates_fetcher(self, mock_fetcher_class):
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        
        fetcher = create_fetcher("test", "http://test.com")
        
        mock_fetcher_class.assert_called_once_with(base_url="http://test.com", api_key=None)
        assert fetcher == mock_fetcher

    @patch('src.utils.data_fetch.os.getenv')
    @patch('src.utils.data_fetch.DataFetcher')
    def test_creates_fetcher_with_env_api_key(self, mock_fetcher_class, mock_getenv):
        mock_getenv.return_value = "env_key_123"
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        
        fetcher = create_fetcher("test", "http://test.com", api_key_env_var="TEST_API_KEY")
        
        mock_fetcher_class.assert_called_once_with(base_url="http://test.com", api_key="env_key_123")
        assert fetcher == mock_fetcher


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @patch('src.utils.data_fetch.requests.Session')
    def test_http_error_raises(self, mock_session_class):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        with pytest.raises(requests.exceptions.HTTPError):
            fetch_url_with_retry("http://test.com/api", session=mock_session)

    @patch('src.utils.data_fetch.requests.Session')
    def test_timeout_raises(self, mock_session_class):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.exceptions.Timeout("Request timed out")
        mock_session_class.return_value = mock_session

        with pytest.raises(requests.exceptions.Timeout):
            fetch_url_with_retry("http://test.com/api", session=mock_session)

    def test_invalid_output_path(self):
        # Try to write to a path that doesn't exist and can't be created (e.g., root)
        with pytest.raises((PermissionError, OSError)):
            fetch_raw_data("http://test.com/data", "/root/forbidden/file.json", timeout=1)