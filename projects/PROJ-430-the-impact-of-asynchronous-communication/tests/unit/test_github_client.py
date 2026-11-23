"""
Unit tests for GitHubClient rate limit handling.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import HTTPError, RequestException

from utils.github_client import GitHubClient, GitHubRateLimitError

class TestGitHubClient:
    @pytest.fixture
    def client(self):
        return GitHubClient(token="fake_token")

    def test_init_with_token(self, client):
        assert client.token == "fake_token"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer fake_token"

    def test_init_without_token(self):
        client = GitHubClient()
        assert client.token is None
        assert "Authorization" not in client.session.headers

    @patch('utils.github_client.requests.Session.get')
    def test_get_success(self, mock_get, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "title": "Test Issue"}]
        mock_get.return_value = mock_response

        result = client.get("/repos/test/test/issues")
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        mock_get.assert_called_once()

    @patch('utils.github_client.requests.Session.get')
    def test_get_404_empty_list(self, mock_get, client):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = client.get("/repos/nonexistent/repo/issues")
        
        assert result == []

    @patch('utils.github_client.requests.Session.get')
    def test_get_rate_limit_retry(self, mock_get, client):
        # First call: Rate limit (403)
        mock_rate_limit = Mock()
        mock_rate_limit.status_code = 403
        mock_rate_limit.text = "rate limit exceeded"
        mock_rate_limit.headers = {"Retry-After": "1"} # Short sleep for test
        
        # Second call: Success
        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = [{"id": 1}]
        
        mock_get.side_effect = [mock_rate_limit, mock_success]

        result = client.get("/repos/test/test/issues", max_retries=2)
        
        assert len(result) == 1
        assert mock_get.call_count == 2

    @patch('utils.github_client.requests.Session.get')
    def test_get_rate_limit_exhausted(self, mock_get, client):
        # Always return rate limit
        mock_rate_limit = Mock()
        mock_rate_limit.status_code = 403
        mock_rate_limit.text = "rate limit exceeded"
        mock_rate_limit.headers = {"Retry-After": "0"} # Immediate retry for test speed
        
        mock_get.return_value = mock_rate_limit

        with pytest.raises(GitHubRateLimitError) as exc_info:
            client.get("/repos/test/test/issues", max_retries=2)
        
        assert "Max retries exceeded" in str(exc_info.value)
        assert mock_get.call_count == 3 # Initial + 2 retries

    @patch('utils.github_client.requests.Session.get')
    def test_get_network_error_retry(self, mock_get, client):
        # First call: Network error
        mock_get.side_effect = RequestException("Network error")
        
        # Second call: Success
        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = [{"id": 1}]
        mock_get.side_effect = [RequestException("Network error"), mock_success]

        result = client.get("/repos/test/test/issues", max_retries=2)
        
        assert len(result) == 1
        assert mock_get.call_count == 2

    @patch('utils.github_client.requests.Session.get')
    def test_get_paginated_single_page(self, mock_get, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1}, {"id": 2}]
        mock_get.return_value = mock_response

        result = client.get_paginated("/repos/test/test/issues")
        
        assert len(result) == 2
        # Should only call once if less than per_page
        assert mock_get.call_count == 1

    @patch('utils.github_client.requests.Session.get')
    def test_get_paginated_multiple_pages(self, mock_get, client):
        # Page 1
        mock_page1 = Mock()
        mock_page1.status_code = 200
        mock_page1.json.return_value = [{"id": i} for i in range(100)]
        
        # Page 2 (less than per_page, signals end)
        mock_page2 = Mock()
        mock_page2.status_code = 200
        mock_page2.json.return_value = [{"id": 100}]
        
        mock_get.side_effect = [mock_page1, mock_page2]

        result = client.get_paginated("/repos/test/test/issues", per_page=100)
        
        assert len(result) == 101
        assert mock_get.call_count == 2