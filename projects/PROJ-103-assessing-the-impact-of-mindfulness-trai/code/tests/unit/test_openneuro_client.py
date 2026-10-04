"""
Unit tests for the OpenNeuro API client.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.datasets.openneuro_client import (
    OpenNeuroClient,
    OpenNeuroClientError,
    create_client
)
from src.config.env import get_openneuro_api_key


@pytest.fixture
def mock_response():
    """Mock response object for requests."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "data": {
            "datasets": [
                {
                    "id": "ds000001",
                    "label": "Test Dataset",
                    "description": "A test dataset for mindfulness research",
                    "created": "2023-01-01T00:00:00Z",
                    "uploader": {"id": "1", "name": "Test User", "orcid": "0000-0000-0000-0000"},
                    "permissions": {"users": [], "public": True},
                    "snapshot": {
                        "id": "1.0.0",
                        "created": "2023-01-02T00:00:00Z",
                        "tags": ["1.0.0"],
                        "description": "Initial snapshot",
                        "summary": {
                            "subjects": ["sub-01", "sub-02"],
                            "modalities": ["fMRI"],
                            "totalSubjects": 2,
                            "secondaryModalities": []
                        }
                    }
                }
            ]
        }
    }
    return response


@pytest.fixture
def client():
    """Create a client with a mocked API key."""
    with patch('src.datasets.openneuro_client.get_openneuro_api_key', return_value='test-key'):
        return OpenNeuroClient()


class TestCreateClient:
    def test_create_client_with_key(self):
        """Test creating client with explicit API key."""
        client = create_client(api_key="explicit-key")
        assert client.api_key == "explicit-key"

    def test_create_client_from_env(self):
        """Test creating client loads key from environment."""
        with patch('src.datasets.openneuro_client.get_openneuro_api_key', return_value="env-key"):
            client = create_client()
            assert client.api_key == "env-key"


class TestOpenNeuroClient:
    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_list_datasets_success(self, mock_post, mock_response, client):
        """Test successful dataset listing."""
        mock_post.return_value = mock_response

        datasets = client.list_datasets(limit=10)

        assert len(datasets) == 1
        assert datasets[0]["id"] == "ds000001"
        assert datasets[0]["label"] == "Test Dataset"
        mock_post.assert_called_once()

    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_list_datasets_with_filter(self, mock_post, mock_response, client):
        """Test listing with specific dataset ID filter."""
        mock_post.return_value = mock_response

        datasets = client.list_datasets(dataset_id="ds000001")

        assert len(datasets) == 1
        call_args = mock_post.call_args
        assert call_args[1]["json"]["variables"]["datasetId"] == "ds000001"

    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_get_dataset_info_success(self, mock_post, mock_response, client):
        """Test retrieving specific dataset info."""
        # Modify response for single dataset query
        mock_response.json.return_value = {
            "data": {
                "dataset": mock_response.json.return_value["data"]["datasets"][0]
            }
        }
        mock_post.return_value = mock_response

        info = client.get_dataset_info("ds000001")

        assert info["id"] == "ds000001"
        assert "latestSnapshot" in info

    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_get_dataset_not_found(self, mock_post, client):
        """Test handling of non-existent dataset."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"dataset": None}}
        mock_post.return_value = mock_response

        with pytest.raises(OpenNeuroClientError, match="not found"):
            client.get_dataset_info("nonexistent")

    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_network_error(self, mock_post, client):
        """Test handling of network errors."""
        mock_post.side_effect = Exception("Network failure")

        with pytest.raises(OpenNeuroClientError, match="Network error"):
            client.list_datasets()

    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_api_error(self, mock_post, client):
        """Test handling of GraphQL API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [{"message": "Field 'invalid' doesn't exist"}]
        }
        mock_post.return_value = mock_response

        with pytest.raises(OpenNeuroClientError, match="GraphQL API error"):
            client.list_datasets()

    @patch('src.datasets.openneuro_client.requests.Session.post')
    def test_json_parse_error(self, mock_post, client):
        """Test handling of JSON parsing errors."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        with pytest.raises(OpenNeuroClientError, match="Failed to parse"):
            client.list_datasets()