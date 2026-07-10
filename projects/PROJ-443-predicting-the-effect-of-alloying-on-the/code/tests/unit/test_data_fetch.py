"""
Unit tests for data fetching utilities.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

from src.utils.data_fetch import (
    create_retry_session,
    fetch_url_with_retry,
    fetch_paginated_data,
    DataFetcher,
    create_fetcher
)
from utils.logging_config import setup_logging

# Initialize logging for tests
setup_logging()


class TestRetrySession:
    def test_create_retry_session(self):
        session = create_retry_session()
        assert session is not None
        assert "http://" in session.adapters
        assert "https://" in session.adapters

class TestFetchUrlWithRetry:
    @patch('src.utils.data_fetch.create_retry_session')
    def test_successful_fetch(self, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [1, 2, 3]}
        mock_response.raise_for_status = MagicMock()
        
        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_response
        mock_session.return_value = mock_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            result = fetch_url_with_retry(
                "http://example.com/api",
                output_path=output_path
            )

            assert result == {"data": [1, 2, 3]}
            assert output_path.exists()
            with open(output_path) as f:
                saved_data = json.load(f)
            assert saved_data == {"data": [1, 2, 3]}

    @patch('src.utils.data_fetch.create_retry_session')
    def test_invalid_json_raises_error(self, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
        mock_response.raise_for_status = MagicMock()
        
        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_response
        mock_session.return_value = mock_instance

        with pytest.raises(ValueError, match="Invalid JSON response"):
            fetch_url_with_retry("http://example.com/api")

class TestFetchPaginatedData:
    @patch('src.utils.data_fetch.create_retry_session')
    def test_pagination_logic(self, mock_session):
        # Mock response for page 1
        mock_response_1 = MagicMock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = {"results": [{"id": 1}], "total": 2}
        
        # Mock response for page 2
        mock_response_2 = MagicMock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {"results": [{"id": 2}], "total": 2}

        # Mock response for page 3 (empty or stop condition)
        mock_response_3 = MagicMock()
        mock_response_3.status_code = 200
        mock_response_3.json.return_value = {"results": [], "total": 2}

        def get_side_effect(*args, **kwargs):
            # Simple logic to return different mocks based on page param
            params = args[1] if len(args) > 1 else kwargs.get('params', {})
            page = params.get('page', 1)
            if page == 1:
                return mock_response_1
            elif page == 2:
                return mock_response_2
            else:
                return mock_response_3

        mock_instance = MagicMock()
        mock_instance.get.side_effect = get_side_effect
        mock_session.return_value = mock_instance

        results = fetch_paginated_data(
            "http://example.com/api",
            {"query": "test"},
            key="results"
        )

        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2

class TestDataFetcher:
    def test_fetcher_initialization(self):
        fetcher = DataFetcher("TestSource", "http://api.test.com", "key123")
        assert fetcher.source_name == "TestSource"
        assert fetcher.base_url == "http://api.test.com"
        assert fetcher.headers == {"X-Api-Key": "key123"}

    def test_create_fetcher_factory(self):
        fetcher = create_fetcher("MP", "https://api.materialsproject.org", "mp-key")
        assert fetcher.source_name == "MP"
        assert "X-Api-Key" in fetcher.headers

class TestErrorHandling:
    @patch('src.utils.data_fetch.create_retry_session')
    def test_request_exception_propagates(self, mock_session):
        import requests
        mock_instance = MagicMock()
        mock_instance.get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_session.return_value = mock_instance

        with pytest.raises(requests.exceptions.ConnectionError):
            fetch_url_with_retry("http://example.com/api")