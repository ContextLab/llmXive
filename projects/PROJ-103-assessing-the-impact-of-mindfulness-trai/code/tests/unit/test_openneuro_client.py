"""
Unit tests for OpenNeuro API client.

Tests cover:
- Client creation and API key handling
- list_datasets method
- get_dataset_info method
- Error handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.datasets.openneuro_client import (
    OpenNeuroClient,
    OpenNeuroClientError,
    create_client
)


@pytest.fixture
def mock_response():
    """Mock response object for requests."""
    response = Mock()
    response.raise_for_status = Mock()
    response.json = Mock(return_value={"data": {}})
    return response


@pytest.fixture
def client():
    """Fixture providing an OpenNeuroClient with mocked API key."""
    with patch("src.datasets.openneuro_client.get_openneuro_api_key", return_value="test_key"):
        return OpenNeuroClient(api_key="test_key")


class TestCreateClient:
    """Tests for the create_client factory function."""
    
    def test_create_client_with_key(self):
        """Test client creation with explicit API key."""
        client = create_client(api_key="explicit_key")
        assert client.api_key == "explicit_key"
    
    def test_create_client_from_env(self):
        """Test client creation retrieves key from environment."""
        with patch("src.datasets.openneuro_client.get_openneuro_api_key", return_value="env_key"):
            client = create_client()
            assert client.api_key == "env_key"
    
    def test_create_client_no_key(self):
        """Test client creation fails when no key available."""
        with patch("src.datasets.openneuro_client.get_openneuro_api_key", return_value=None):
            with pytest.raises(OpenNeuroClientError) as exc_info:
                create_client()
            assert "API key is required" in str(exc_info.value)


class TestOpenNeuroClient:
    """Tests for OpenNeuroClient methods."""
    
    def test_client_initialization(self, client):
        """Test client initializes with correct headers."""
        assert client.api_key == "test_key"
        assert client.session.headers["Authorization"] == "Bearer test_key"
        assert client.session.headers["Content-Type"] == "application/json"
    
    def test_list_datasets_success(self, client, mock_response):
        """Test successful list_datasets call."""
        mock_data = {
            "data": {
                "datasets": [
                    {"id": "ds000001", "label": "Dataset 1", "created": "2023-01-01"},
                    {"id": "ds000002", "label": "Dataset 2", "created": "2023-01-02"}
                ]
            }
        }
        mock_response.json = Mock(return_value=mock_data)
        
        with patch.object(client.session, "post", return_value=mock_response):
            result = client.list_datasets(limit=10)
        
        assert "datasets" in result
        assert len(result["datasets"]) == 2
        assert result["datasets"][0]["id"] == "ds000001"
    
    def test_list_datasets_with_filters(self, client, mock_response):
        """Test list_datasets with dataset_id and order filters."""
        mock_data = {"data": {"datasets": []}}
        mock_response.json = Mock(return_value=mock_data)
        
        with patch.object(client.session, "post", return_value=mock_response) as mock_post:
            client.list_datasets(limit=5, dataset_id="ds000001", order="modified")
        
        # Verify query variables were passed correctly
        call_args = mock_post.call_args[1]["json"]
        assert call_args["variables"]["limit"] == 5
        assert call_args["variables"]["datasetId"] == "ds000001"
        assert call_args["variables"]["order"] == "modified"
    
    def test_list_datasets_api_error(self, client, mock_response):
        """Test list_datasets handles API errors."""
        mock_response.json = Mock(return_value={
            "errors": [{"message": "Invalid query"}]
        })
        
        with patch.object(client.session, "post", return_value=mock_response):
            with pytest.raises(OpenNeuroClientError) as exc_info:
                client.list_datasets()
            assert "API Error" in str(exc_info.value)
    
    def test_list_datasets_request_error(self, client):
        """Test list_datasets handles request exceptions."""
        with patch.object(client.session, "post", side_effect=Exception("Network error")):
            with pytest.raises(OpenNeuroClientError) as exc_info:
                client.list_datasets()
            assert "Request failed" in str(exc_info.value)
    
    def test_get_dataset_info_success(self, client, mock_response):
        """Test successful get_dataset_info call."""
        mock_data = {
            "data": {
                "dataset": {
                    "id": "ds000001",
                    "label": "Test Dataset",
                    "created": "2023-01-01",
                    "description": {
                        "Name": "Test Dataset",
                        "Authors": ["Author 1"]
                    },
                    "summary": {
                        "modalities": ["fMRI"],
                        "subjectCount": 10
                    }
                }
            }
        }
        mock_response.json = Mock(return_value=mock_data)
        
        with patch.object(client.session, "post", return_value=mock_response):
            result = client.get_dataset_info("ds000001")
        
        assert result["id"] == "ds000001"
        assert result["label"] == "Test Dataset"
        assert result["description"]["Name"] == "Test Dataset"
        assert result["summary"]["subjectCount"] == 10
    
    def test_get_dataset_info_not_found(self, client, mock_response):
        """Test get_dataset_info handles missing dataset."""
        mock_response.json = Mock(return_value={"data": {"dataset": None}})
        
        with patch.object(client.session, "post", return_value=mock_response):
            with pytest.raises(OpenNeuroClientError) as exc_info:
                client.get_dataset_info("nonexistent")
            assert "not found" in str(exc_info.value)
    
    def test_get_dataset_info_api_error(self, client, mock_response):
        """Test get_dataset_info handles API errors."""
        mock_response.json = Mock(return_value={
            "errors": [{"message": "Dataset not found"}]
        })
        
        with patch.object(client.session, "post", return_value=mock_response):
            with pytest.raises(OpenNeuroClientError) as exc_info:
                client.get_dataset_info("ds000001")
            assert "API Error" in str(exc_info.value)