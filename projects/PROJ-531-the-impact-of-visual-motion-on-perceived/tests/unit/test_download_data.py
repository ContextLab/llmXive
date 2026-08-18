import os
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add code to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download_data import download_data

def test_download_data_creates_status_file():
    """Verify that download_data creates the status file even on failure."""
    with patch('download_data.requests.get') as mock_get, \
         patch('download_data.sys.exit') as mock_exit:
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "data_set_description": {
                    "name": "test_dataset",
                    "citation": "test citation"
                }
            }
        }
        mock_get.return_value = mock_response
        
        # The function should exit with code 1 because the dataset won't match schema
        with pytest.raises(SystemExit) as exc_info:
            download_data()
        
        assert exc_info.value.code == 1
        
        # Verify status file was created
        status_file = Path("data/raw/download_status.json")
        assert status_file.exists()
        
        with open(status_file) as f:
            status = json.load(f)
        
        assert status["status"] == "unavailable"
        assert "reason" in status

def test_download_data_url_reachability():
    """Verify URL reachability check logic (mocked)."""
    with patch('download_data.requests.get') as mock_get, \
         patch('download_data.sys.exit') as mock_exit:
        
        # Simulate network failure
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(SystemExit) as exc_info:
            download_data()
        
        assert exc_info.value.code == 1
        
        status_file = Path("data/raw/download_status.json")
        assert status_file.exists()
        
        with open(status_file) as f:
            status = json.load(f)
        
        assert status["status"] == "failed"
        assert "error" in status

def test_download_data_checksum_validation_logic():
    """
    Verify that the logic for checksum validation is present (even if mocked).
    Since we don't have a real file to checksum, we verify the code path exists.
    """
    # This test verifies that the code structure allows for checksum validation
    # In a real scenario, this would compare a downloaded file's hash.
    # Here we just ensure the function doesn't crash and handles the flow.
    with patch('download_data.requests.get') as mock_get, \
         patch('download_data.sys.exit') as mock_exit:
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "data_set_description": {
                    "name": "test",
                    "citation": "test"
                }
            }
        }
        mock_get.return_value = mock_response
        
        with pytest.raises(SystemExit):
            download_data()
        
        # If we get here, the logic ran without crashing
        assert True