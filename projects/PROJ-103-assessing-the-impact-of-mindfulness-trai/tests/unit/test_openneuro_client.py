"""
Unit tests for the OpenNeuro API client.

These tests verify that the client can successfully connect to the OpenNeuro API,
list datasets, and retrieve dataset information.
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
    """Mock response for successful API calls."""
    return {
        "data": {
            "datasets": [
                {
                    "id": "ds000001",
                    "label": "Test Dataset 1",
                    "name": "Test Dataset 1 Name",
                    "uploaded": "2023-01-01T00:00:00Z",
                    "modified": "2023-01-02T00:00:00Z",
                    "snapshot": {"id": "1", "tag": "1.0.0"}
                },
                {
                    "id": "ds000002",
                    "label": "Test Dataset 2",
                    "name": "Test Dataset 2 Name",
                    "uploaded": "2023-01-03T00:00:00Z",
                    "modified": "2023-01-04T00:00:00Z",
                    "snapshot": {"id": "2", "tag": "1.0.0"}
                }
            ]
        }
    }


@pytest.fixture
def client():
    """Fixture providing a client with mocked API key."""
    with patch("src.datasets.openneuro_client.get_openneuro_api_key", return_value="fake-api-key"):
        return OpenNeuroClient()


class TestCreateClient:
    """Tests for the create_client factory function."""

    def test_create_client_with_key(self):
        """Test creating client with explicit API key."""
        client = create_client(api_key="explicit-key")
        assert client.api_key == "explicit-key"

    def test_create_client_from_env(self):
        """Test creating client using environment variable."""
        with patch("src.datasets.openneuro_client.get_openneuro_api_key", return_value="env-key"):
            client = create_client()
            assert client.api_key == "env-key"

    def test_create_client_without_key_raises(self):
        """Test that creating client without key raises error."""
        with patch("src.datasets.openneuro_client.get_openneuro_api_key", return_value=None):
            with pytest.raises(OpenNeuroClientError, match="API key not provided"):
                create_client()


class TestOpenNeuroClient:
    """Tests for the OpenNeuroClient class."""

    def test_client_initialization(self, client):
        """Test client initializes with API key."""
        assert client.api_key == "fake-api-key"
        assert client.session is not None

    def test_list_datasets_success(self, client, mock_response):
        """Test successful listing of datasets."""
        with patch.object(client.session, "post") as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=Mock(return_value=mock_response)
            )

            datasets = client.list_datasets(limit=10, offset=0)

            assert len(datasets) == 2
            assert datasets[0]["id"] == "ds000001"
            assert datasets[1]["id"] == "ds000002"
            mock_post.assert_called_once()

    def test_list_datasets_empty(self, client):
        """Test listing when no datasets returned."""
        empty_response = {"data": {"datasets": []}}
        with patch.object(client.session, "post") as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=Mock(return_value=empty_response)
            )

            datasets = client.list_datasets()
            assert datasets == []

    def test_list_datasets_api_error(self, client):
        """Test handling of API errors."""
        error_response = {"errors": [{"message": "Invalid query"}]}
        with patch.object(client.session, "post") as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=Mock(return_value=error_response)
            )

            with pytest.raises(OpenNeuroClientError, match="Invalid query"):
                client.list_datasets()

    def test_list_datasets_network_error(self, client):
        """Test handling of network errors."""
        with patch.object(client.session, "post") as mock_post:
            mock_post.side_effect = Exception("Network error")

            with pytest.raises(OpenNeuroClientError, match="Network error"):
                client.list_datasets()

    def test_get_dataset_info_success(self, client):
        """Test successful retrieval of dataset info."""
        dataset_response = {
            "data": {
                "dataset": {
                    "id": "ds000001",
                    "label": "Test Dataset",
                    "name": "Test Dataset Name",
                    "description": {"Name": "Test", "Authors": ["Author1"], "Version": "1.0", "DOI": "10.1234/test"},
                    "uploader": {"id": "u1", "name": "Uploader", "email": "uploader@example.com"},
                    "summary": {"subjectCount": 20, "modalities": ["fMRI"], "sessions": 2, "tasks": ["rest"]},
                    "snapshot": {"id": "1", "tag": "1.0.0", "created": "2023-01-01"}
                }
            }
        }

        with patch.object(client.session, "post") as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=Mock(return_value=dataset_response)
            )

            info = client.get_dataset_info("ds000001")

            assert info["id"] == "ds000001"
            assert info["label"] == "Test Dataset"
            assert info["summary"]["subjectCount"] == 20

    def test_get_dataset_info_not_found(self, client):
        """Test handling of dataset not found."""
        not_found_response = {"data": {"dataset": None}}
        with patch.object(client.session, "post") as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=Mock(return_value=not_found_response)
            )

            with pytest.raises(OpenNeuroClientError, match="not found"):
                client.get_dataset_info("ds999999")

    def test_get_dataset_info_api_error(self, client):
        """Test handling of API error on dataset info."""
        error_response = {"errors": [{"message": "Dataset access denied"}]}
        with patch.object(client.session, "post") as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=Mock(return_value=error_response)
            )

            with pytest.raises(OpenNeuroClientError, match="Dataset access denied"):
                client.get_dataset_info("ds000001")