import pytest
from unittest.mock import patch, MagicMock
from code.utils.api_client import OpenMLClient
from code.utils.exceptions import DataFetchError

def test_api_client_success():
    client = OpenMLClient()
    with patch('requests.Session.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response
        
        result = client.get("test_endpoint")
        assert result == {"data": "test"}

def test_api_client_retry_on_429():
    client = OpenMLClient(max_retries=2, initial_delay=0.01)
    with patch('requests.Session.get') as mock_get:
        # First two calls fail with 429, third succeeds
        resp429 = MagicMock()
        resp429.status_code = 429
        
        resp200 = MagicMock()
        resp200.status_code = 200
        resp200.json.return_value = {"data": "success"}
        
        mock_get.side_effect = [resp429, resp429, resp200]
        
        result = client.get("test_endpoint")
        assert result == {"data": "success"}
        assert mock_get.call_count == 3

def test_api_client_fail_after_max_retries():
    client = OpenMLClient(max_retries=1, initial_delay=0.01)
    with patch('requests.Session.get') as mock_get:
        resp429 = MagicMock()
        resp429.status_code = 429
        mock_get.return_value = resp429
        
        with pytest.raises(DataFetchError):
            client.get("test_endpoint")

def test_fetch_top_classification_datasets():
    client = OpenMLClient()
    with patch.object(OpenMLClient, 'get') as mock_get:
        mock_get.return_value = {
            "datasets": {
                "dataset": [
                    {"dataset_id": 1, "download_count": "10"},
                    {"dataset_id": 2, "download_count": "100"},
                    {"dataset_id": 3, "download_count": "50"},
                ]
            }
        }
        results = client.fetch_top_classification_datasets(limit=2)
        assert len(results) == 2
        assert results[0]["dataset_id"] == 2 # Most downloaded first
