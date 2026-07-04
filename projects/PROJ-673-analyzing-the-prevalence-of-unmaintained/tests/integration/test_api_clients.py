"""
Integration tests for mocked NPM and GitHub API responses.

This module tests the API clients (NpmClient, GithubClient, AuditClient)
using mocked responses to verify correct behavior without hitting
external APIs.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Import clients - assuming they will be implemented in Phase 3
# Using try/except to handle case where clients aren't implemented yet
try:
    from src.services.npm_client import NpmClient
    from src.services.github_client import GithubClient
    from src.services.audit_client import AuditClient
except ImportError:
    # Clients not yet implemented - tests will be skipped
    NpmClient = None
    GithubClient = None
    AuditClient = None


@pytest.fixture
def mock_responses():
    """Provide mock API responses for testing."""
    return {
        "npm_top_packages": {
            "packages": [
                {
                    "name": "lodash",
                    "downloads": 100000000,
                    "date": "2024-01-01"
                },
                {
                    "name": "express",
                    "downloads": 50000000,
                    "date": "2024-01-01"
                }
            ]
        },
        "npm_package_metadata": {
            "name": "lodash",
            "repository": {
                "type": "git",
                "url": "https://github.com/lodash/lodash.git"
            },
            "version": "4.17.21",
            "time": {
                "created": "2024-01-01T00:00:00.000Z",
                "modified": "2024-06-01T00:00:00.000Z"
            }
        },
        "github_commit": {
            "sha": "abc123",
            "commit": {
                "author": {
                    "date": "2024-06-01T00:00:00.000Z"
                }
            },
            "url": "https://api.github.com/repos/lodash/lodash/commits/abc123"
        },
        "npm_audit": {
            "advisories": {
                "12345": {
                    "id": 12345,
                    "severity": "high",
                    "title": "Prototype Pollution in lodash"
                }
            }
        }
    }


@pytest.mark.skipif(NpmClient is None, reason="NpmClient not yet implemented")
class TestNpmClient:
    """Integration tests for NpmClient with mocked responses."""

    def test_get_top_packages(self, mock_responses):
        """Test fetching top packages by weekly downloads."""
        client = NpmClient()

        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_responses["npm_top_packages"]
            mock_get.return_value = mock_response

            packages = client.get_top_packages(limit=2)

            assert len(packages) == 2
            assert packages[0]["name"] == "lodash"
            assert packages[0]["downloads"] == 100000000
            mock_get.assert_called_once()

    def test_get_package_metadata(self, mock_responses):
        """Test fetching package metadata."""
        client = NpmClient()

        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_responses["npm_package_metadata"]
            mock_get.return_value = mock_response

            metadata = client.get_package_metadata("lodash")

            assert metadata["name"] == "lodash"
            assert metadata["version"] == "4.17.21"
            assert "repository" in metadata

    def test_rate_limit_handling(self, mock_responses):
        """Test that rate limit responses are handled correctly."""
        client = NpmClient()

        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers = {"Retry-After": "60"}
            mock_get.return_value = mock_response

            # Should raise an exception or return None on rate limit
            with pytest.raises(Exception):
                client.get_top_packages(limit=1)


@pytest.mark.skipif(GithubClient is None, reason="GithubClient not yet implemented")
class TestGithubClient:
    """Integration tests for GithubClient with mocked responses."""

    def test_get_last_commit_date(self, mock_responses):
        """Test fetching last commit date for a repository."""
        client = GithubClient()

        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_responses["github_commit"]
            mock_get.return_value = mock_response

            commit_date = client.get_last_commit_date("lodash", "lodash")

            assert commit_date == "2024-06-01T00:00:00.000Z"
            mock_get.assert_called_once()

    def test_get_last_release_date(self, mock_responses):
        """Test fetching last release date for a repository."""
        client = GithubClient()

        with patch.object(client.session, 'get') as mock_get:
            # Mock release endpoint
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    "tag_name": "4.17.21",
                    "published_at": "2024-05-01T00:00:00.000Z"
                }
            ]
            mock_get.return_value = mock_response

            release_date = client.get_last_release_date("lodash", "lodash")

            assert release_date == "2024-05-01T00:00:00.000Z"

    def test_missing_repository(self):
        """Test handling of missing repository (404)."""
        client = GithubClient()

        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            commit_date = client.get_last_commit_date("nonexistent", "nonexistent")

            assert commit_date is None


@pytest.mark.skipif(AuditClient is None, reason="AuditClient not yet implemented")
class TestAuditClient:
    """Integration tests for AuditClient with mocked responses."""

    def test_get_vulnerability_count(self, mock_responses):
        """Test fetching vulnerability count for a package."""
        client = AuditClient()

        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_responses["npm_audit"]
            mock_get.return_value = mock_response

            vulnerabilities = client.get_vulnerabilities("lodash")

            assert len(vulnerabilities) == 1
            assert vulnerabilities[0]["id"] == 12345
            assert vulnerabilities[0]["severity"] == "high"

    def test_no_vulnerabilities(self):
        """Test handling of packages with no vulnerabilities."""
        client = AuditClient()

        with patch.object(client.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"advisories": {}}
            mock_get.return_value = mock_response

            vulnerabilities = client.get_vulnerabilities("safe-package")

            assert len(vulnerabilities) == 0


@pytest.mark.skipif(
    NpmClient is None or GithubClient is None or AuditClient is None,
    reason="Clients not yet implemented"
)
class TestIntegrationPipeline:
    """Integration test for the full data collection pipeline with mocks."""

    def test_end_to_end_data_collection(self, mock_responses):
        """Test complete data collection flow with mocked APIs."""
        npm_client = NpmClient()
        github_client = GithubClient()
        audit_client = AuditClient()

        # Mock all API calls
        with patch.object(npm_client.session, 'get') as mock_npm_get, \
             patch.object(github_client.session, 'get') as mock_github_get, \
             patch.object(audit_client.session, 'get') as mock_audit_get:

            # Setup mock responses
            npm_response = MagicMock()
            npm_response.status_code = 200
            npm_response.json.return_value = mock_responses["npm_top_packages"]
            mock_npm_get.return_value = npm_response

            github_response = MagicMock()
            github_response.status_code = 200
            github_response.json.return_value = mock_responses["github_commit"]
            mock_github_get.return_value = github_response

            audit_response = MagicMock()
            audit_response.status_code = 200
            audit_response.json.return_value = mock_responses["npm_audit"]
            mock_audit_get.return_value = audit_response

            # Collect data for top package
            packages = npm_client.get_top_packages(limit=1)
            package_name = packages[0]["name"]

            metadata = npm_client.get_package_metadata(package_name)
            commit_date = github_client.get_last_commit_date("lodash", "lodash")
            vulnerabilities = audit_client.get_vulnerabilities(package_name)

            # Verify data collection
            assert package_name == "lodash"
            assert commit_date is not None
            assert len(vulnerabilities) == 1

            # Verify all API calls were made
            assert mock_npm_get.call_count >= 2  # top packages + metadata
            assert mock_github_get.call_count >= 1
            assert mock_audit_get.call_count >= 1

def test_mock_responses_structure(self, mock_responses):
    """Verify that mock responses have the expected structure."""
    assert "packages" in mock_responses["npm_top_packages"]
    assert "name" in mock_responses["npm_package_metadata"]
    assert "sha" in mock_responses["github_commit"]
    assert "advisories" in mock_responses["npm_audit"]