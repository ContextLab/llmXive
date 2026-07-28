"""
Integration tests for mocked NPM and GitHub API responses.

This module verifies that the NpmClient, GithubClient, and AuditClient
correctly handle mocked API responses, including success cases, error
handling, and edge cases like missing repositories or empty responses.

Tests use pytest and unittest.mock to simulate API behavior without
making real network requests.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timezone
from typing import Dict, Any, List

# Import clients from the project
from src.services.npm_client import NpmClient
from src.services.github_client import GithubClient
from src.services.audit_client import AuditClient
from src.config.settings import get_config

# Test fixtures and constants
MOCK_NPM_PACKAGE = {
    "name": "lodash",
    "version": "4.17.21",
    "description": "Lodash modular utilities",
    "repository": {
        "type": "git",
        "url": "https://github.com/lodash/lodash.git"
    },
    "downloads": 15000000,
    "maintainers": [
        {"email": "john@lodash.com", "name": "John"}
    ],
    "keywords": ["utilities", "functional", "data"]
}

MOCK_NPM_TOP_PACKAGES = [
    {"package": "lodash", "downloads": 15000000},
    {"package": "express", "downloads": 12000000},
    {"package": "react", "downloads": 10000000},
    {"package": "axios", "downloads": 8000000},
    {"package": "moment", "downloads": 7000000}
]

MOCK_GITHUB_COMMIT = {
    "commit": {
        "author": {
            "date": "2024-01-15T10:30:00Z"
        }
    },
    "url": "https://api.github.com/repos/lodash/lodash/commits/abc123"
}

MOCK_GITHUB_RELEASE = {
    "tag_name": "v4.17.21",
    "published_at": "2021-02-16T20:30:43Z",
    "html_url": "https://github.com/lodash/lodash/releases/tag/v4.17.21"
}

MOCK_GITHUB_EMPTY_RELEASE = []

MOCK_AUDIT_ADVISORIES = {
    "advisories": {
        "CVE-2021-23337": {
            "severity": "high",
            "vulnerable_versions": "<4.17.21",
            "patched_versions": ">=4.17.21",
            "title": "Command Injection in Lodash"
        },
        "CVE-2020-8203": {
            "severity": "critical",
            "vulnerable_versions": "<4.17.19",
            "patched_versions": ">=4.17.19",
            "title": "Prototype Pollution in Lodash"
        }
    }
}

MOCK_AUDIT_EMPTY = {"advisories": {}}

@pytest.fixture
def mock_config():
    """Provide a mock configuration for testing."""
    config = get_config()
    # Override with test values
    config.npm_api_key = "test_npm_key"
    config.github_token = "test_github_token"
    config.rate_limit = 100
    return config

@pytest.fixture
def npm_client(mock_config):
    """Create an NpmClient instance for testing."""
    return NpmClient()

@pytest.fixture
def github_client(mock_config):
    """Create a GithubClient instance for testing."""
    return GithubClient()

@pytest.fixture
def audit_client(mock_config):
    """Create an AuditClient instance for testing."""
    return AuditClient()

class TestNpmClientIntegration:
    """Integration tests for NpmClient with mocked responses."""

    def test_fetch_top_packages_success(self, npm_client):
        """Test fetching top packages with mocked successful response."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "objects": [{"package": p} for p in MOCK_NPM_TOP_PACKAGES]
            }
            mock_get.return_value = mock_response
            
            packages = npm_client.fetch_top_packages(limit=5)
            
            assert len(packages) == 5
            assert packages[0]["package"] == "lodash"
            assert packages[0]["downloads"] == 15000000
            mock_get.assert_called_once()

    def test_fetch_package_metadata_success(self, npm_client):
        """Test fetching package metadata with mocked response."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_NPM_PACKAGE
            mock_get.return_value = mock_response
            
            metadata = npm_client.fetch_package_metadata("lodash")
            
            assert metadata["name"] == "lodash"
            assert metadata["version"] == "4.17.21"
            assert "repository" in metadata
            mock_get.assert_called_once()

    def test_fetch_package_metadata_not_found(self, npm_client):
        """Test handling of 404 response for non-existent package."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = Exception("Not Found")
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception):
                npm_client.fetch_package_metadata("non-existent-package")

    def test_fetch_top_packages_rate_limit(self, npm_client):
        """Test handling of rate limit response."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.json.return_value = {"message": "Rate limit exceeded"}
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception):
                npm_client.fetch_top_packages(limit=5)

class TestGithubClientIntegration:
    """Integration tests for GithubClient with mocked responses."""

    def test_get_commit_date_success(self, github_client):
        """Test fetching commit date with mocked successful response."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [MOCK_GITHUB_COMMIT]
            mock_get.return_value = mock_response
            
            commit_date = github_client.get_commit_date("lodash", "lodash")
            
            assert commit_date is not None
            assert isinstance(commit_date, datetime)
            mock_get.assert_called_once()

    def test_get_commit_date_not_found(self, github_client):
        """Test handling of empty commit list."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response
            
            commit_date = github_client.get_commit_date("lodash", "lodash")
            
            assert commit_date is None

    def test_get_release_date_success(self, github_client):
        """Test fetching release date with mocked successful response."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_GITHUB_RELEASE
            mock_get.return_value = mock_response
            
            release_date = github_client.get_release_date("lodash", "lodash")
            
            assert release_date is not None
            assert isinstance(release_date, datetime)
            mock_get.assert_called_once()

    def test_get_release_date_empty(self, github_client):
        """Test handling of empty release list."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_GITHUB_EMPTY_RELEASE
            mock_get.return_value = mock_response
            
            release_date = github_client.get_release_date("lodash", "lodash")
            
            assert release_date is None

    def test_fetch_repository_metadata_success(self, github_client):
        """Test fetching repository metadata."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "name": "lodash",
                "full_name": "lodash/lodash",
                "html_url": "https://github.com/lodash/lodash",
                "created_at": "2012-01-01T00:00:00Z",
                "updated_at": "2024-01-15T00:00:00Z"
            }
            mock_get.return_value = mock_response
            
            metadata = github_client.fetch_repository_metadata("lodash", "lodash")
            
            assert metadata["name"] == "lodash"
            assert metadata["full_name"] == "lodash/lodash"
            mock_get.assert_called_once()

    def test_fetch_repository_metadata_not_found(self, github_client):
        """Test handling of 404 for repository."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = Exception("Not Found")
            mock_get.return_value = mock_response
            
            metadata = github_client.fetch_repository_metadata("nonexistent", "repo")
            
            assert metadata is None

class TestAuditClientIntegration:
    """Integration tests for AuditClient with mocked responses."""

    def test_fetch_audit_data_success(self, audit_client):
        """Test fetching audit data with mocked successful response."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_AUDIT_ADVISORIES
            mock_get.return_value = mock_response
            
            advisories = audit_client.fetch_audit_data("lodash")
            
            assert len(advisories) == 2
            assert "CVE-2021-23337" in advisories
            assert "CVE-2020-8203" in advisories
            mock_get.assert_called_once()

    def test_fetch_audit_data_empty_advisories(self, audit_client):
        """Test handling of empty advisories response."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_AUDIT_EMPTY
            mock_get.return_value = mock_response
            
            advisories = audit_client.fetch_audit_data("lodash")
            
            assert len(advisories) == 0

    def test_fetch_audit_data_api_error(self, audit_client):
        """Test handling of API error response."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = Exception("Server Error")
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception):
                audit_client.fetch_audit_data("lodash")

    def test_batch_fetch_audit_data(self, audit_client):
        """Test batch fetching of audit data for multiple packages."""
        packages = ["lodash", "express", "react"]
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_AUDIT_ADVISORIES
            mock_get.return_value = mock_response
            
            results = audit_client.batch_fetch_audit_data(packages)
            
            assert len(results) == 3
            assert "lodash" in results
            assert "express" in results
            assert "react" in results
            assert mock_get.call_count == 3

class TestBackoffIntegration:
    """Integration tests for backoff logic with mocked API responses."""

    def test_retry_on_failure(self, npm_client):
        """Test that client retries on failure before giving up."""
        call_count = 0
        
        def mock_get_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                mock_response = MagicMock()
                mock_response.status_code = 503
                mock_response.raise_for_status.side_effect = Exception("Service Unavailable")
                return mock_response
            else:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"objects": []}
                return mock_response
        
        with patch('requests.get', side_effect=mock_get_side_effect):
            # Should succeed after retries
            packages = npm_client.fetch_top_packages(limit=5)
            assert call_count == 3
            assert packages == []

    def test_max_retries_exceeded(self, npm_client):
        """Test that client fails after max retries."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_response.raise_for_status.side_effect = Exception("Service Unavailable")
            mock_get.return_value = mock_response
            
            # Should raise after max retries
            with pytest.raises(Exception):
                npm_client.fetch_top_packages(limit=5)

class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_invalid_package_name(self, npm_client):
        """Test handling of invalid package names."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"error": "Invalid package name"}
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception):
                npm_client.fetch_package_metadata("invalid@package@name")

    def test_invalid_github_repo_format(self, github_client):
        """Test handling of invalid GitHub repo format."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = Exception("Not Found")
            mock_get.return_value = mock_response
            
            result = github_client.get_commit_date("invalid-repo", "")
            assert result is None

    def test_null_date_parsing(self, github_client):
        """Test handling of null or missing date fields."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{
                "commit": {
                    "author": {
                        "date": None
                    }
                }
            }]
            mock_get.return_value = mock_response
            
            result = github_client.get_commit_date("lodash", "lodash")
            assert result is None

    def test_empty_response_handling(self, audit_client):
        """Test handling of completely empty API response."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response
            
            advisories = audit_client.fetch_audit_data("lodash")
            assert len(advisories) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])