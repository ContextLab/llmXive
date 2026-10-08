import pytest
from unittest.mock import Mock, patch, MagicMock
from src.datasets.openneuro_client import (
    OpenNeuroClient,
    OpenNeuroClientError,
    DatasetNotFoundError,
    DatasetAccessError,
    create_client
)
from src.config.env import get_openneuro_api_key
import requests


@pytest.fixture
def mock_response():
    """Mock response object for testing."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "data": {
            "dataset": {
                "id": "ds000001",
                "label": "Test Dataset",
                "description": {
                    "description": "A test dataset",
                    "Name": "Test Dataset"
                },
                "created": "2023-01-01T00:00:00Z",
                "modified": "2023-01-02T00:00:00Z",
                "snapshot": {
                    "id": "ds000001:1.0.0",
                    "created": "2023-01-01T00:00:00Z",
                    "description": "Snapshot 1.0.0",
                    "summary": {
                        "totalSubjects": 20,
                        "totalSessions": 2,
                        "modalities": ["fMRI", "T1w"]
                    }
                },
                "uploader": {
                    "id": "user123",
                    "name": "Test User",
                    "email": "test@example.com"
                },
                "permissions": {
                    "public": True,
                    "users": [],
                    "groups": []
                }
            }
        }
    }
    return response


@pytest.fixture
def client():
    """Create a client with mocked API key."""
    with patch('src.datasets.openneuro_client.get_openneuro_api_key', return_value='test_key'):
        return OpenNeuroClient()


class TestCreateClient:
    def test_create_client_with_api_key(self):
        """Test client creation with explicit API key."""
        client = create_client(api_key="explicit_key")
        assert client.api_key == "explicit_key"
    
    def test_create_client_from_env(self):
        """Test client creation uses environment variable."""
        with patch('src.datasets.openneuro_client.get_openneuro_api_key', return_value="env_key"):
            client = create_client()
            assert client.api_key == "env_key"
    
    def test_create_client_no_key(self):
        """Test client creation fails without API key."""
        with patch('src.datasets.openneuro_client.get_openneuro_api_key', return_value=None):
            with pytest.raises(OpenNeuroClientError, match="API key is required"):
                create_client()


class TestOpenNeuroClient:
    def test_get_dataset_info_success(self, client, mock_response):
        """Test successful dataset info retrieval."""
        with patch.object(client.session, 'post', return_value=mock_response):
            info = client.get_dataset_info("ds000001")
            
            assert info["id"] == "ds000001"
            assert info["label"] == "Test Dataset"
            assert info["description"] == "A test dataset"
            assert info["num_subjects"] == 20
            assert info["modalities"] == ["fMRI", "T1w"]
            assert info["public"] is True
    
    def test_get_dataset_info_not_found(self, client):
        """Test error handling for non-existent dataset."""
        error_response = Mock()
        error_response.status_code = 200
        error_response.json.return_value = {
            "data": {
                "dataset": None
            }
        }
        
        with patch.object(client.session, 'post', return_value=error_response):
            with pytest.raises(DatasetNotFoundError, match="Dataset 'ds999999' not found"):
                client.get_dataset_info("ds999999")
    
    def test_get_dataset_info_invalid_id(self, client):
        """Test error handling for invalid dataset ID."""
        with pytest.raises(OpenNeuroClientError, match="Dataset ID must be a non-empty string"):
            client.get_dataset_info("")
        
        with pytest.raises(OpenNeuroClientError, match="Dataset ID must be a non-empty string"):
            client.get_dataset_info(None)
    
    def test_get_dataset_info_api_error(self, client):
        """Test error handling for API errors."""
        error_response = Mock()
        error_response.status_code = 200
        error_response.json.return_value = {
            "errors": [
                {"message": "Internal server error"}
            ]
        }
        
        with patch.object(client.session, 'post', return_value=error_response):
            with pytest.raises(OpenNeuroClientError, match="API Error: Internal server error"):
                client.get_dataset_info("ds000001")
    
    def test_get_dataset_info_timeout(self, client):
        """Test error handling for request timeout."""
        with patch.object(client.session, 'post', side_effect=requests.exceptions.Timeout):
            with pytest.raises(OpenNeuroClientError, match="timed out"):
                client.get_dataset_info("ds000001")
    
    def test_get_dataset_info_request_exception(self, client):
        """Test error handling for general request exceptions."""
        with patch.object(client.session, 'post', side_effect=requests.exceptions.ConnectionError):
            with pytest.raises(OpenNeuroClientError, match="Request failed"):
                client.get_dataset_info("ds000001")
    
    def test_get_dataset_info_missing_snapshot(self, client):
        """Test handling of datasets without snapshots."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": {
                "dataset": {
                    "id": "ds000001",
                    "label": "Test Dataset",
                    "description": {"description": "Test"},
                    "created": "2023-01-01",
                    "modified": "2023-01-01",
                    "snapshot": None,
                    "uploader": {},
                    "permissions": {}
                }
            }
        }
        
        with patch.object(client.session, 'post', return_value=response):
            info = client.get_dataset_info("ds000001")
            assert info["num_subjects"] == 0
            assert info["modalities"] == []
    
    def test_list_datasets(self, client):
        """Test listing datasets."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": {
                "datasets": [
                    {
                        "id": "ds000001",
                        "label": "Dataset 1",
                        "snapshot": {"id": "snap1", "created": "2023-01-01"}
                    },
                    {
                        "id": "ds000002",
                        "label": "Dataset 2",
                        "snapshot": {"id": "snap2", "created": "2023-01-02"}
                    }
                ]
            }
        }
        
        with patch.object(client.session, 'post', return_value=response):
            datasets = client.list_datasets(limit=10, offset=0)
            
            assert len(datasets) == 2
            assert datasets[0]["id"] == "ds000001"
            assert datasets[0]["label"] == "Dataset 1"
            assert datasets[1]["id"] == "ds000002"