"""
Unit tests for the OpenNeuro API client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.datasets.openneuro_client import OpenNeuroClient, OpenNeuroClientError, create_client


@pytest.fixture
def mock_response():
    """Mock response object for requests."""
    mock = Mock()
    mock.status_code = 200
    mock.json.return_value = {
        "data": {
            "datasets": [
                {
                    "id": "ds000001",
                    "label": "ds000001",
                    "name": "Example Dataset",
                    "created": "2020-01-01T00:00:00Z",
                    "snapshot": {
                        "id": "1.0.0",
                        "tag": "1.0.0",
                        "summary": {
                            "modalities": ["fMRI"],
                            "subjects": 10
                        }
                    }
                }
            ]
        }
    }
    return mock


@pytest.fixture
def client(monkeypatch):
    """Create a client with a mocked API key."""
    monkeypatch.setenv("OPENNEURO_API_KEY", "test_key_123")
    return OpenNeuroClient()


class TestCreateClient:
    def test_create_client_with_key(self):
        client = create_client(api_key="my_key")
        assert client.api_key == "my_key"

    def test_create_client_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENNEURO_API_KEY", "env_key")
        client = create_client()
        assert client.api_key == "env_key"

    def test_create_client_no_key_raises(self, monkeypatch):
        monkeypatch.delenv("OPENNEURO_API_KEY", raising=False)
        with pytest.raises(OpenNeuroClientError):
            create_client()


class TestOpenNeuroClient:
    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_list_datasets_success(self, mock_post, client, mock_response):
        mock_post.return_value = mock_response
        
        datasets = client.list_datasets(limit=5)
        
        assert isinstance(datasets, list)
        assert len(datasets) == 1
        assert datasets[0]["id"] == "ds000001"
        assert datasets[0]["name"] == "Example Dataset"
        mock_post.assert_called_once()

    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_list_datasets_with_filter(self, mock_post, client, mock_response):
        mock_post.return_value = mock_response
        
        datasets = client.list_datasets(dataset_id="ds000001")
        
        # Verify the variable was passed correctly
        call_args = mock_post.call_args
        assert call_args[1]["json"]["variables"]["datasetId"] == "ds000001"

    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_get_dataset_info_success(self, mock_post, client):
        mock_response_info = Mock()
        mock_response_info.status_code = 200
        mock_response_info.json.return_value = {
            "data": {
                "dataset": {
                    "id": "ds000001",
                    "name": "Example Dataset",
                    "description": "A test dataset",
                    "license": "MIT",
                    "created": "2020-01-01T00:00:00Z",
                    "modified": "2020-01-02T00:00:00Z",
                    "downloads": 100,
                    "snapshots": [],
                    "analytics": {}
                }
            }
        }
        mock_post.return_value = mock_response_info
        
        info = client.get_dataset_info("ds000001")
        
        assert info["id"] == "ds000001"
        assert info["name"] == "Example Dataset"
        assert info["description"] == "A test dataset"

    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_get_dataset_info_not_found(self, mock_post, client):
        mock_response_error = Mock()
        mock_response_error.status_code = 200
        mock_response_error.json.return_value = {
            "data": {
                "dataset": None
            }
        }
        mock_post.return_value = mock_response_error
        
        with pytest.raises(OpenNeuroClientError, match="not found"):
            client.get_dataset_info("ds999999")

    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_api_error_handling(self, mock_post, client):
        mock_response_error = Mock()
        mock_response_error.status_code = 200
        mock_response_error.json.return_value = {
            "errors": [{"message": "Permission denied"}]
        }
        mock_post.return_value = mock_response_error
        
        with pytest.raises(OpenNeuroClientError, match="Permission denied"):
            client.list_datasets()

    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_network_error_handling(self, mock_post, client):
        mock_post.side_effect = Exception("Network failed")
        
        with pytest.raises(OpenNeuroClientError, match="Network error"):
            client.list_datasets()