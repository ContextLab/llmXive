"""
Integration tests for mocked NPM and GitHub API responses.

This module validates the interaction between the NpmClient, GithubClient,
and AuditClient with mocked external API responses to ensure the data
collection pipeline handles real-world scenarios correctly without
making actual network calls.

Tests cover:
- Successful data retrieval with valid JSON responses
- Handling of missing repository data (null dates)
- Rate limiting simulation and backoff behavior
- Error handling for HTTP errors and timeouts
"""

import json
import os
import time
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path

import pytest
import requests
from requests.exceptions import HTTPError, Timeout, ConnectionError

# Import clients from the project structure
# Adjust imports based on the actual project root structure
try:
    from src.services.npm_client import NpmClient
    from src.services.github_client import GithubClient
    from src.services.audit_client import AuditClient
    from src.config.settings import get_config
    from src.utils.backoff import exponential_backoff
except ImportError:
    # Fallback for different project root structures during testing
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.services.npm_client import NpmClient
    from src.services.github_client import GithubClient
    from src.services.audit_client import AuditClient
    from src.config.settings import get_config
    from src.utils.backoff import exponential_backoff


# --- Fixtures ---

@pytest.fixture
def mock_config():
    """Provide a mock configuration object."""
    config = MagicMock()
    config.NPM_API_KEY = "test_npm_key"
    config.GITHUB_TOKEN = "test_github_token"
    config.RATE_LIMIT = 60
    return config

@pytest.fixture
def npm_client(mock_config):
    """Initialize NpmClient with mock config."""
    return NpmClient(config=mock_config)

@pytest.fixture
def github_client(mock_config):
    """Initialize GithubClient with mock config."""
    return GithubClient(config=mock_config)

@pytest.fixture
def audit_client(mock_config):
    """Initialize AuditClient with mock config."""
    return AuditClient(config=mock_config)

# --- Mock Data ---

MOCK_NPM_SEARCH_RESPONSE = {
    "objects": [
        {
            "package": {
                "name": "lodash",
                "version": "4.17.21",
                "keywords": ["utility", "functional"],
                "links": {
                    "repository": "https://github.com/lodash/lodash"
                }
            },
            "downloads": 25000000
        },
        {
            "package": {
                "name": "express",
                "version": "4.18.2",
                "keywords": ["web", "framework"],
                "links": {
                    "repository": "https://github.com/expressjs/express"
                }
            },
            "downloads": 18000000
        }
    ]
}

MOCK_GITHUB_COMMIT_RESPONSE = {
    "commit": {
        "author": {
            "date": "2023-10-15T14:30:00Z"
        }
    }
}

MOCK_GITHUB_RELEASE_RESPONSE = {
    "tag_name": "v4.17.21",
    "published_at": "2023-09-10T10:00:00Z"
}

MOCK_AUDIT_RESPONSE = {
    "advisories": {
        "CVE-2021-23337": {
            "severity": "high",
            "vulnerable_versions": "<4.17.20"
        }
    }
}

# --- Test Cases ---

class TestNpmClientIntegration:
    """Integration tests for NpmClient with mocked responses."""

    @patch('src.services.npm_client.requests.get')
    def test_fetch_top_packages_success(self, mock_get, npm_client):
        """Test successful retrieval of top packages."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_NPM_SEARCH_RESPONSE
        mock_get.return_value = mock_response

        packages = npm_client.get_top_packages(limit=2)

        assert len(packages) == 2
        assert packages[0]["name"] == "lodash"
        assert packages[0]["downloads"] == 25000000
        mock_get.assert_called_once()

    @patch('src.services.npm_client.requests.get')
    def test_fetch_top_packages_rate_limit(self, mock_get, npm_client):
        """Test handling of rate limiting (429) with backoff."""
        # First call fails with 429, second succeeds
        error_response = MagicMock()
        error_response.status_code = 429
        error_response.raise_for_status.side_effect = HTTPError(response=error_response)
        
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = MOCK_NPM_SEARCH_RESPONSE

        mock_get.side_effect = [error_response, success_response]

        # Should retry and succeed
        packages = npm_client.get_top_packages(limit=2)

        assert len(packages) == 2
        assert mock_get.call_count == 2  # Initial + 1 retry

    @patch('src.services.npm_client.requests.get')
    def test_fetch_package_metadata_timeout(self, mock_get, npm_client):
        """Test handling of network timeout."""
        mock_get.side_effect = Timeout("Connection timed out")

        with pytest.raises(Timeout):
            npm_client.get_package_metadata("lodash")


class TestGithubClientIntegration:
    """Integration tests for GithubClient with mocked responses."""

    @patch('src.services.github_client.requests.get')
    def test_get_commit_date_success(self, mock_get, github_client):
        """Test successful retrieval of last commit date."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_GITHUB_COMMIT_RESPONSE
        mock_get.return_value = mock_response

        commit_date = github_client.get_last_commit_date("lodash/lodash")

        assert commit_date is not None
        assert isinstance(commit_date, datetime)
        assert commit_date.year == 2023
        assert commit_date.month == 10

    @patch('src.services.github_client.requests.get')
    def test_get_release_date_success(self, mock_get, github_client):
        """Test successful retrieval of last release date."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_GITHUB_RELEASE_RESPONSE
        mock_get.return_value = mock_response

        release_date = github_client.get_last_release_date("lodash/lodash")

        assert release_date is not None
        assert isinstance(release_date, datetime)
        assert release_date.year == 2023
        assert release_date.month == 9

    @patch('src.services.github_client.requests.get')
    def test_get_commit_date_not_found(self, mock_get, github_client):
        """Test handling of repository not found (404)."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        commit_date = github_client.get_last_commit_date("nonexistent/repo")

        assert commit_date is None

    @patch('src.services.github_client.requests.get')
    def test_get_release_date_empty(self, mock_get, github_client):
        """Test handling of empty release list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []  # Empty list
        mock_get.return_value = mock_response

        release_date = github_client.get_last_release_date("lodash/lodash")

        assert release_date is None


class TestAuditClientIntegration:
    """Integration tests for AuditClient with mocked responses."""

    @patch('src.services.audit_client.requests.post')
    def test_fetch_audit_data_success(self, mock_post, audit_client):
        """Test successful retrieval of audit data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_AUDIT_RESPONSE
        mock_post.return_value = mock_response

        vulnerabilities = audit_client.fetch_audit_data("lodash")

        assert len(vulnerabilities) == 1
        assert "CVE-2021-23337" in vulnerabilities
        assert vulnerabilities["CVE-2021-23337"]["severity"] == "high"

    @patch('src.services.audit_client.requests.post')
    def test_fetch_audit_data_empty_advisories(self, mock_post, audit_client):
        """Test handling of package with no vulnerabilities."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"advisories": {}}
        mock_post.return_value = mock_response

        vulnerabilities = audit_client.fetch_audit_data("express")

        assert len(vulnerabilities) == 0

    @patch('src.services.audit_client.requests.post')
    def test_fetch_audit_data_http_error(self, mock_post, audit_client):
        """Test handling of HTTP error from audit API."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        # Should raise HTTPError
        with pytest.raises(HTTPError):
            audit_client.fetch_audit_data("lodash")


class TestBackoffIntegration:
    """Integration tests for backoff logic."""

    def test_exponential_backoff_max_retries(self):
        """Test that exponential backoff respects max retries."""
        call_count = 0
        max_calls = 3

        @exponential_backoff(max_retries=max_calls, initial_delay=0.01, multiplier=1.0, max_delay=0.1)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Simulated connection error")

        with pytest.raises(ConnectionError):
            failing_function()

        # Should have been called initial + max_retries times
        assert call_count == max_calls + 1

    def test_exponential_backoff_success_on_retry(self):
        """Test that backoff stops on success."""
        call_count = 0

        @exponential_backoff(max_retries=3, initial_delay=0.01, multiplier=1.0, max_delay=0.1)
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Simulated connection error")
            return "Success"

        result = eventually_succeeds()
        assert result == "Success"
        assert call_count == 2


class TestEndToEndMockedPipeline:
    """Integration test simulating the full data collection flow with mocks."""

    @patch('src.services.npm_client.requests.get')
    @patch('src.services.github_client.requests.get')
    @patch('src.services.audit_client.requests.post')
    def test_full_data_collection_flow(self, mock_audit_post, mock_github_get, mock_npm_get):
        """Simulate collecting data for a single package end-to-end."""
        # Setup NPM response
        npm_resp = MagicMock()
        npm_resp.status_code = 200
        npm_resp.json.return_value = MOCK_NPM_SEARCH_RESPONSE
        mock_npm_get.return_value = npm_resp

        # Setup GitHub responses
        github_commit_resp = MagicMock()
        github_commit_resp.status_code = 200
        github_commit_resp.json.return_value = MOCK_GITHUB_COMMIT_RESPONSE
        
        github_release_resp = MagicMock()
        github_release_resp.status_code = 200
        github_release_resp.json.return_value = MOCK_GITHUB_RELEASE_RESPONSE
        
        # Mock side effect for two calls (commit then release)
        mock_github_get.side_effect = [github_commit_resp, github_release_resp]

        # Setup Audit response
        audit_resp = MagicMock()
        audit_resp.status_code = 200
        audit_resp.json.return_value = MOCK_AUDIT_RESPONSE
        mock_audit_post.return_value = audit_resp

        # Initialize clients
        config = get_config()
        npm = NpmClient(config)
        github = GithubClient(config)
        audit = AuditClient(config)

        # 1. Get top package
        packages = npm.get_top_packages(limit=1)
        assert len(packages) == 1
        pkg_name = packages[0]["name"]

        # 2. Get GitHub metadata
        commit_date = github.get_last_commit_date("lodash/lodash")
        release_date = github.get_last_release_date("lodash/lodash")

        assert commit_date is not None
        assert release_date is not None

        # 3. Get Audit data
        vulns = audit.fetch_audit_data(pkg_name)
        assert len(vulns) > 0

        # Verify data consistency
        assert commit_date > release_date or commit_date == release_date