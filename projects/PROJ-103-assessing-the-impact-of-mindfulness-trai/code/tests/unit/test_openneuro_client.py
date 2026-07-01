"""
Unit tests for the OpenNeuro API client.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.datasets.openneuro_client import OpenNeuroClient, create_client


@pytest.fixture
def mock_response():
    """Mock response object for requests."""
    response = Mock()
    response.json.return_value = {
        "datasets": [
            {"id": "ds000001", "label": "Test Dataset", "description": {"Name": "Test"}}
        ],
        "count": 1
    }
    response.raise_for_status = Mock()
    return response


@pytest.fixture
def client():
    """Create a client instance with a mock API key."""
    return OpenNeuroClient(api_key="test-key")


class TestOpenNeuroClient:
    def test_init_default_api_key(self, monkeypatch):
        """Test initialization with environment variable."""
        monkeypatch.setenv("OPENNEURO_API_KEY", "env-key")
        client = OpenNeuroClient()
        assert client.api_key == "env-key"

    def test_init_custom_api_key(self):
        """Test initialization with custom API key."""
        client = OpenNeuroClient(api_key="custom-key")
        assert client.api_key == "custom-key"

    @patch('src.datasets.openneuro_client.requests.Session')
    def test_list_datasets(self, mock_session_class, client, mock_response):
        """Test listing datasets."""
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = client.list_datasets(limit=10)

        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert "datasets" in call_args[0][0]
        assert call_args[1]["params"]["limit"] == 10
        assert result["count"] == 1

    @patch('src.datasets.openneuro_client.requests.Session')
    def test_get_dataset_info(self, mock_session_class, client, mock_response):
        """Test retrieving dataset info."""
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = client.get_dataset_info("ds000001")

        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert "datasets/ds000001" in call_args[0][0]
        assert result["datasets"][0]["id"] == "ds000001"

    @patch('src.datasets.openneuro_client.requests.Session')
    def test_http_error(self, mock_session_class, client):
        """Test handling of HTTP errors."""
        mock_session = Mock()
        error_response = Mock()
        error_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_session.get.return_value = error_response
        mock_session_class.return_value = mock_session

        with pytest.raises(Exception, match="404 Not Found"):
            client.get_dataset_info("nonexistent")

class TestCreateClient:
    def test_create_client_instance(self, monkeypatch):
        """Test factory function creates client."""
        monkeypatch.setenv("OPENNEURO_API_KEY", "test-key")
        client = create_client()
        assert isinstance(client, OpenNeuroClient)
        assert client.api_key == "test-key"
