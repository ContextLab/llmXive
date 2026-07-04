"""
Unit tests for the AuditClient.

These tests verify the correct behavior of the AuditClient,
including successful API responses, error handling, and data parsing.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.services.audit_client import AuditClient
from src.config.settings import get_config


@pytest.fixture
def mock_config():
    """Provide a mock configuration for testing."""
    return {
        "NPM_API_KEY": None,
        "GITHUB_TOKEN": None,
        "RATE_LIMIT": 60
    }


@pytest.fixture
def client(mock_config):
    """Create an AuditClient instance."""
    with patch('src.services.audit_client.get_config', return_value=mock_config):
        return AuditClient()


def test_client_initialization(client):
    """Test that the client initializes correctly."""
    assert client is not None
    assert client.base_url == "https://registry.npmjs.org/-/npm/v1/audit"
    assert client.session is not None


@patch('src.services.audit_client.requests.Session.post')
def test_fetch_audit_data_success(mock_post, client):
    """Test successful fetch of audit data."""
    # Mock response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "advisories": {
            "123456": {
                "id": 123456,
                "title": "Test Vulnerability",
                "severity": "high",
                "cves": ["CVE-2023-1234"],
                "url": "https://example.com",
                "patched_versions": ">=1.0.1"
            }
        }
    }
    mock_post.return_value = mock_response

    result = client.fetch_audit_data("test-package")

    assert result["status"] == "success"
    assert result["vulnerability_count"] == 1
    assert len(result["vulnerabilities"]) == 1
    assert result["vulnerabilities"][0]["title"] == "Test Vulnerability"
    assert result["package_name"] == "test-package"


@patch('src.services.audit_client.requests.Session.post')
def test_fetch_audit_data_empty_advisories(mock_post, client):
    """Test fetch when there are no vulnerabilities."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "advisories": {}
    }
    mock_post.return_value = mock_response

    result = client.fetch_audit_data("safe-package")

    assert result["status"] == "success"
    assert result["vulnerability_count"] == 0
    assert len(result["vulnerabilities"]) == 0


@patch('src.services.audit_client.requests.Session.post')
def test_fetch_audit_data_api_error(mock_post, client):
    """Test handling of API errors."""
    mock_post.side_effect = Exception("Network error")

    result = client.fetch_audit_data("test-package")

    assert result["status"] == "error"
    assert "error_message" in result
    assert "Network error" in result["error_message"]
    assert result["vulnerability_count"] == 0


@patch('src.services.audit_client.requests.Session.post')
def test_fetch_audit_data_http_error(mock_post, client):
    """Test handling of HTTP errors."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("404 Not Found")
    mock_post.return_value = mock_response

    result = client.fetch_audit_data("nonexistent-package")

    assert result["status"] == "error"
    assert "error_message" in result
    assert result["vulnerability_count"] == 0


def test_batch_fetch_audit_data(client):
    """Test batch fetching of audit data."""
    # This test would require mocking multiple requests
    # For now, we verify the method exists and returns a list
    with patch.object(client, 'fetch_audit_data') as mock_fetch:
        mock_fetch.return_value = {"status": "success", "vulnerability_count": 0}
        
        results = client.batch_fetch_audit_data(["pkg1", "pkg2"])
        
        assert len(results) == 2
        assert all(isinstance(r, dict) for r in results)
        assert all(r["status"] == "success" for r in results)
