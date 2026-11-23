import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add code directory to path for imports if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download_data import check_openml_dataset, validate_instrument, download_data

class TestDownloadData:
    def test_check_openml_dataset_exists(self):
        """Test that check_openml_dataset returns True for a valid active dataset."""
        # Mock the requests.get to return a 200 OK with active status
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "status": "active",
                "name": "Test Dataset"
            }
        }
        
        with patch('download_data.requests.get', return_value=mock_response):
            assert check_openml_dataset(123) is True

    def test_check_openml_dataset_not_found(self):
        """Test that check_openml_dataset returns False for 404 or inactive."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch('download_data.requests.get', return_value=mock_response):
            assert check_openml_dataset(999) is False

    def test_validate_instrument_returns_false(self):
        """
        Test that validate_instrument returns False in this stress-test context,
        triggering the 'unavailable' status.
        """
        # The implementation currently returns False as no real validated instrument is found.
        assert validate_instrument({"name": "Test"}) is False

    def test_download_data_writes_unavailable_status(self, tmp_path):
        """
        Test that download_data writes 'unavailable' to the status file
        when no real data is found, and does not exit with code 1.
        """
        # Create a temporary directory for the test
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        # Ensure the data/raw directory exists
        (tmp_path / "data" / "raw").mkdir(parents=True)
        
        # Mock the helper functions to ensure they return False/Unavailable
        with patch('download_data.check_openml_dataset', return_value=False), \
             patch('download_data.validate_instrument', return_value=False):
            
            # Run the function
            result = download_data()
            
            # Verify the file was created
            status_file = Path("data/raw/download_status.json")
            assert status_file.exists(), "download_status.json was not created"
            
            # Verify content
            with open(status_file, 'r') as f:
                data = json.load(f)
            
            assert data["status"] == "unavailable"
            assert data["reason"] is not None
            assert result == "unavailable"
        
        os.chdir(original_cwd)

    def test_download_data_exits_on_invalid(self):
        """
        Test that download_data exits with code 1 if status is 'invalid'.
        """
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.chdir(tmp_dir)
            Path("data/raw").mkdir(parents=True)
            
            with patch('download_data.check_openml_dataset', return_value=True), \
                 patch('download_data.validate_instrument', return_value=False):
                
                    # We expect SystemExit
                    with pytest.raises(SystemExit) as exc_info:
                        download_data()
                    
                    assert exc_info.value.code == 1
        
        os.chdir(original_cwd)