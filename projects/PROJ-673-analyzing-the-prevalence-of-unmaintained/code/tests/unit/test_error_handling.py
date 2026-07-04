import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError, ConnectionError, Timeout
from src.services.npm_client import NpmClient
from src.services.github_client import GithubClient
from src.services.audit_client import AuditClient

class TestNpmClientErrorHandling:
    """Test error handling in NpmClient."""

    def test_http_error_handling(self):
        """Test handling of HTTP errors in get_package_metadata."""
        client = NpmClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
            mock_get.return_value = mock_response
            
            result = client.get_package_metadata("nonexistent-package")
            assert result is None

    def test_connection_error_handling(self):
        """Test handling of connection errors."""
        client = NpmClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = ConnectionError("Network error")
            
            result = client.get_package_metadata("test-package")
            assert result is None

    def test_timeout_error_handling(self):
        """Test handling of timeout errors."""
        client = NpmClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = Timeout("Request timed out")
            
            result = client.get_package_metadata("test-package")
            assert result is None

class TestGithubClientErrorHandling:
    """Test error handling in GithubClient."""

    def test_repo_not_found(self):
        """Test handling of 404 for repository not found."""
        client = GithubClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
            mock_get.return_value = mock_response
            
            result = client.get_repository_info("nonexistent/repo")
            assert result is None

    def test_commit_date_parsing_error(self):
        """Test handling of invalid date format."""
        client = GithubClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"commit": {"committer": {"date": "invalid-date"}}}]
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = client.get_last_commit_date("owner/repo")
            assert result is None

    def test_rate_limit_handling(self):
        """Test handling of rate limit errors."""
        client = GithubClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.headers = {"X-RateLimit-Remaining": "0"}
            mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
            mock_get.return_value = mock_response
            
            result = client.get_repository_info("owner/repo")
            assert result is None

class TestAuditClientErrorHandling:
    """Test error handling in AuditClient."""

    def test_audit_not_found(self):
        """Test handling of 404 for audit data not found."""
        client = AuditClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
            mock_get.return_value = mock_response
            
            result = client.fetch_audit_data("nonexistent-package")
            assert result is None

    def test_batch_fetch_partial_failure(self):
        """Test that batch fetch continues on individual failures."""
        client = AuditClient()
        
        packages = [
            {"name": "valid-package", "version": "1.0.0"},
            {"name": "invalid-package", "version": "1.0.0"}
        ]
        
        # Mock success for first, failure for second
        with patch.object(client, 'fetch_audit_data') as mock_fetch:
            mock_fetch.side_effect = [
                {"package": "valid-package", "vulnerability_count": 0, "advisories": []},
                None
            ]
            
            results = client.batch_fetch_audit_data(packages)
            
            # Should have one valid result and one with zero vulnerabilities
            assert len(results) == 2
            assert results[0]["package"] == "valid-package"
            assert results[1]["package"] == "invalid-package"
            assert results[1]["vulnerability_count"] == 0