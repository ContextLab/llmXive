"""
Integration tests for T045b: Fetch APT data from NIST.

These tests verify that the APT data fetch functionality works correctly
with real data sources and handles edge cases appropriately.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.errors import ExperimentalDataError
from code.data.fetch_apt_nist import (
    fetch_apt_data,
    download_apt_datasets,
    save_apt_data,
    main,
    NIST_APT_IDS
)

class TestFetchAptNist:
    """Test suite for APT data fetching functionality."""
    
    def test_fetch_apt_data_success(self):
        """Test successful fetch of APT data."""
        # Mock response
        mock_data = {
            "data": {
                "compositions": [0.1, 0.2, 0.3],
                "temperatures": [300, 400, 500],
                "segregation_energies": [0.1, 0.2, 0.3]
            }
        }
        
        with patch('code.data.fetch_apt_nist.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response
            
            result = fetch_apt_data("NIST-APT-2019-001")
            
            assert result is not None
            assert "data" in result
            assert result["data"]["compositions"] == [0.1, 0.2, 0.3]
            mock_get.assert_called_once()
    
    def test_fetch_apt_data_not_found(self):
        """Test handling of 404 response."""
        with patch('code.data.fetch_apt_nist.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = fetch_apt_data("NON-EXISTENT-ID")
            
            assert result is None
    
    def test_fetch_apt_data_network_error(self):
        """Test handling of network errors."""
        with patch('code.data.fetch_apt_nist.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            with pytest.raises(ExperimentalDataError):
                fetch_apt_data("NIST-APT-2019-001")
    
    def test_download_apt_datasets_binary_only(self):
        """Test download with only binary data (no ternary)."""
        mock_binary_data = {
            "data": {
                "compositions": [0.1, 0.2],
                "temperatures": [300, 400]
            }
        }
        
        with patch('code.data.fetch_apt_nist.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_binary_data
            mock_get.return_value = mock_response
            
            result = download_apt_datasets()
            
            assert len(result["binary_data"]) > 0
            assert result["ternary_flag"] is True  # Ternary not found
            assert len(result["warnings"]) > 0
            assert any("NO_TERNARY_IDS" in warning for warning in result["warnings"])
    
    def test_save_apt_data_creates_file(self):
        """Test that save_apt_data creates the output file."""
        test_data = {
            "binary_data": [{"system": "Fe-Cr", "data": {"test": "value"}}],
            "ternary_flag": True,
            "warnings": ["Test warning"],
            "metadata": {"test": "metadata"}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            
            save_apt_data(test_data, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == test_data
    
    def test_no_binary_data_raises_error(self):
        """Test that missing binary data raises an error."""
        with patch('code.data.fetch_apt_nist.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            with pytest.raises(ExperimentalDataError):
                download_apt_datasets()
    
    def test_main_function_creates_output(self):
        """Test that main function creates the output file."""
        mock_binary_data = {
            "data": {
                "compositions": [0.1, 0.2],
                "temperatures": [300, 400]
            }
        }
        
        with patch('code.data.fetch_apt_nist.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_binary_data
            mock_get.return_value = mock_response
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Temporarily override DATA_DIR
                original_data_dir = None
                try:
                    from code import config
                    original_data_dir = config.DATA_DIR
                    config.DATA_DIR = Path(tmpdir)
                    
                    result = main()
                    
                    assert result == 0
                    
                    output_file = Path(tmpdir) / "apt_nist_binary_data.json"
                    assert output_file.exists()
                    
                    with open(output_file, 'r') as f:
                        saved_data = json.load(f)
                    
                    assert len(saved_data["binary_data"]) > 0
                    assert saved_data["ternary_flag"] is True
                finally:
                    if original_data_dir:
                        config.DATA_DIR = original_data_dir