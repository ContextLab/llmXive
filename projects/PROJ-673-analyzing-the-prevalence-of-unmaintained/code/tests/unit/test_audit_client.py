import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.services.audit_client import AuditClient
from src.config.settings import get_config

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return get_config()

@pytest.fixture
def client():
    """Create an AuditClient instance."""
    return AuditClient(timeout=5)

def test_client_initialization(client):
    """Test that the client initializes correctly."""
    assert client.timeout == 5
    assert client.base_url == "https://registry.npmjs.org/-/npm/v1/security/advisories/bulk"
    assert client.session is not None

@patch('src.services.audit_client.requests.Session.post')
def test_fetch_audit_data_success(mock_post, client):
    """Test successful fetch of audit data."""
    # Mock response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "lodash": [
            {"id": 1, "severity": "high", "title": "Prototype Pollution"},
            {"id": 2, "severity": "medium", "title": "ReDoS"}
        ]
    }
    mock_post.return_value = mock_response

    result = client.fetch_audit_data("lodash", "4.17.21")

    assert result["vulnerability_count"] == 2
    assert len(result["advisories"]) == 2
    assert result["package"] == "lodash"
    assert result["version"] == "4.17.21"
    mock_post.assert_called_once()

@patch('src.services.audit_client.requests.Session.post')
def test_fetch_audit_data_empty_advisories(mock_post, client):
    """Test fetch when no advisories are found."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "lodash": []
    }
    mock_post.return_value = mock_response

    result = client.fetch_audit_data("lodash", "4.17.21")

    assert result["vulnerability_count"] == 0
    assert result["advisories"] == []

@patch('src.services.audit_client.requests.Session.post')
def test_fetch_audit_data_api_error(mock_post, client):
    """Test handling of API errors."""
    mock_post.side_effect = Exception("Network error")

    with pytest.raises(RuntimeError) as exc_info:
        client.fetch_audit_data("lodash", "4.17.21")

    assert "npm audit API failed" in str(exc_info.value)

@patch('src.services.audit_client.requests.Session.post')
def test_fetch_audit_data_http_error(mock_post, client):
    """Test handling of HTTP errors."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("404 Not Found")
    mock_post.return_value = mock_response

    with pytest.raises(RuntimeError):
        client.fetch_audit_data("lodash", "4.17.21")

@patch('src.services.audit_client.requests.Session.post')
def test_batch_fetch_audit_data(mock_post, client):
    """Test batch fetching of audit data."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "lodash": [{"id": 1}],
        "express": [{"id": 2}, {"id": 3}]
    }
    mock_post.return_value = mock_response

    packages = [
        {"package": "lodash", "version": "4.17.21"},
        {"package": "express", "version": "4.18.2"}
    ]

    results = client.batch_fetch_audit_data(packages)

    assert len(results) == 2
    assert results[0]["vulnerability_count"] == 1
    assert results[1]["vulnerability_count"] == 2