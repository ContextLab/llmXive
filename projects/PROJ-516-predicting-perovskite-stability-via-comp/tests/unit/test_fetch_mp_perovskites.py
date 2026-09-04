"""
Unit tests for fetch_mp_perovskites.py
"""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.fetch_mp_perovskites import (
    fetch_mp_material_data,
    fetch_experimental_tga_data,
    validate_data_checksum,
    save_to_csv,
    create_retry_session
)
from code.utils.data_fetcher import FetchError


class TestFetchMpPerovskites:
    """Test suite for Materials Project perovskite data fetching."""
    
    def test_create_retry_session(self):
        """Test that retry session is created correctly."""
        session = create_retry_session()
        assert session is not None
        assert hasattr(session, 'get')
        assert hasattr(session, 'request')
    
    @patch('code.fetch_mp_perovskites.fetch_with_retry')
    def test_fetch_mp_material_data_success(self, mock_fetch):
        """Test successful fetch of material data."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "material_id": "mp-12345",
                "formula": "CsPbI3",
                "properties": {
                    "decomposition_temp": 450
                }
            }
        }
        mock_fetch.return_value = mock_response
        
        # Call function
        result = fetch_mp_material_data(Mock(), "CsPbI3", "test_api_key")
        
        # Verify
        assert result is not None
        assert result["material_id"] == "mp-12345"
        assert result["formula"] == "CsPbI3"
        mock_fetch.assert_called_once()
    
    @patch('code.fetch_mp_perovskites.fetch_with_retry')
    def test_fetch_mp_material_data_not_found(self, mock_fetch):
        """Test handling of 404 response."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_fetch.return_value = mock_response
        
        result = fetch_mp_material_data(Mock(), "NonExistent", "test_api_key")
        
        assert result is None
    
    @patch('code.fetch_mp_perovskites.fetch_with_retry')
    def test_fetch_mp_material_data_fetch_error(self, mock_fetch):
        """Test handling of FetchError."""
        mock_fetch.side_effect = FetchError("Network error")
        
        result = fetch_mp_material_data(Mock(), "CsPbI3", "test_api_key")
        
        assert result is None
    
    def test_fetch_experimental_tga_data_success(self):
        """Test extraction of TGA data from material data."""
        material_data = {
            "material_id": "mp-12345",
            "experimental": {
                "thermogravimetric": {
                    "decomposition_temp": 450,
                    "instrument_model": "TA Instruments Q500",
                    "manufacturer": "TA Instruments",
                    "temperature_precision": 2
                }
            }
        }
        
        result = fetch_experimental_tga_data(material_data, "CsPbI3")
        
        assert result is not None
        assert result["formula"] == "CsPbI3"
        assert result["T_d"] == 450
        assert result["source"] == "Materials Project"
        assert result["material_id"] == "mp-12345"
        assert result["instrument_model"] == "TA Instruments Q500"
        assert result["manufacturer"] == "TA Instruments"
        assert result["temperature_precision"] == 2
    
    def test_fetch_experimental_tga_data_no_tga(self):
        """Test handling of missing TGA data."""
        material_data = {
            "material_id": "mp-12345",
            "properties": {
                "band_gap": 1.5
            }
        }
        
        result = fetch_experimental_tga_data(material_data, "CsPbI3")
        
        assert result is None
    
    def test_fetch_experimental_tga_data_no_material_data(self):
        """Test handling of None material data."""
        result = fetch_experimental_tga_data(None, "CsPbI3")
        
        assert result is None
    
    @patch('code.fetch_mp_perovskites.compute_sha256')
    @patch('builtins.open')
    def test_validate_data_checksum(self, mock_open, mock_compute):
        """Test checksum validation and manifest generation."""
        mock_compute.return_value = "abc123def456"
        
        data = [{"formula": "CsPbI3", "T_d": 450}]
        checksum_path = Path("/tmp/test_checksums.json")
        
        result = validate_data_checksum(data, checksum_path)
        
        assert result is True
        mock_compute.assert_called_once_with(data)
        mock_open.assert_called_once()
    
    @patch('code.fetch_mp_perovskites.Path')
    def test_save_to_csv(self, mock_path):
        """Test saving data to CSV."""
        mock_path.return_value.parent.mkdir = Mock()
        mock_path.return_value.parent.exists.return_value = False
        
        data = [
            {"formula": "CsPbI3", "T_d": 450, "source": "Materials Project"},
            {"formula": "MAPbI3", "T_d": 350, "source": "Materials Project"}
        ]
        
        with patch('code.fetch_mp_perovskites.pd.DataFrame') as mock_df:
            save_to_csv(data, Path("/tmp/test.csv"))
            
            mock_df.assert_called_once_with(data)
            mock_df.return_value.to_csv.assert_called_once()
    
    @patch('code.fetch_mp_perovskites.load_config')
    @patch('code.fetch_mp_perovskites.get_api_key')
    @patch('code.fetch_mp_perovskites.create_retry_session')
    @patch('code.fetch_mp_perovskites.fetch_mp_material_data')
    @patch('code.fetch_mp_perovskites.fetch_experimental_tga_data')
    @patch('code.fetch_mp_perovskites.validate_data_checksum')
    @patch('code.fetch_mp_perovskites.save_to_csv')
    @patch('code.fetch_mp_perovskites.Path')
    def test_main_success(
        self, mock_path, mock_save, mock_validate, mock_fetch_tga, 
        mock_fetch_material, mock_session, mock_get_key, mock_load_config
    ):
        """Test successful main execution."""
        # Setup mocks
        mock_load_config.return_value = {}
        mock_get_key.return_value = "test_api_key"
        mock_session.return_value = Mock()
        mock_fetch_material.return_value = {
            "material_id": "mp-12345",
            "experimental": {
                "thermogravimetric": {"decomposition_temp": 450}
            }
        }
        mock_fetch_tga.return_value = {
            "formula": "CsPbI3",
            "T_d": 450,
            "source": "Materials Project"
        }
        mock_validate.return_value = True
        mock_path.return_value.exists.return_value = True
        
        # Mock DataFrame for verification
        mock_df = Mock()
        mock_df.columns = ['T_d']
        mock_df['T_d'].isna.return_value = False
        
        with patch('code.fetch_mp_perovskites.pd.read_csv', return_value=mock_df):
            result = __import__('code.fetch_mp_perovskites', fromlist=['main']).main()
            
            assert result == 0
            mock_save.assert_called_once()
            mock_validate.assert_called_once()
    
    @patch('code.fetch_mp_perovskites.get_api_key')
    def test_main_missing_api_key(self, mock_get_key):
        """Test main execution with missing API key."""
        mock_get_key.return_value = None
        
        result = __import__('code.fetch_mp_perovskites', fromlist=['main']).main()
        
        assert result == 1
        mock_get_key.assert_called_once_with("MP_API_KEY")