"""
Unit tests for fetch_dft.py functionality.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.fetch_dft import fetch_elastic_data, fetch_dft_data

@pytest.fixture
def mock_response_success():
    return {
        "data": {
            "elasticity": {
                "G_VRH": 80.5,
                "K_VRH": 170.0,
                "E_VRH": 210.0,
                "nu": 0.30,
                "anisotropy": 1.05,
                "elasticity_tensor": [[10, 0, 0], [0, 10, 0], [0, 0, 10]]
            }
        }
    }

@pytest.fixture
def mock_response_not_found():
    return {"message": "Material not found"}

def test_fetch_elastic_data_success(mock_response_success):
    """Test successful fetch of elastic data."""
    with patch('ingestion.fetch_dft.requests.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_success
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = fetch_elastic_data("mp-13", "fake_key")
        
        assert result is not None
        assert result["mp_id"] == "mp-13"
        assert result["shear_modulus_GPa"] == 80.5
        assert result["bulk_modulus_GPa"] == 170.0
        assert result["status"] == "success"

def test_fetch_elastic_data_not_found(mock_response_not_found):
    """Test handling of 404 response."""
    with patch('ingestion.fetch_dft.requests.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = mock_response_not_found
        mock_response.raise_for_status.side_effect = Exception("404") # Simulate raise
        
        # Mock the session.get to return the 404 response directly
        # We need to handle the exception inside the function logic
        mock_session.get.return_value = mock_response

        # In the actual code, 404 is handled before raise_for_status usually, 
        # but let's test the logic path where it returns None
        with patch.object(mock_response, 'raise_for_status', side_effect=Exception):
            # We simulate the internal check
            # Since the actual function checks status_code == 404 first:
            pass 
        
        # Re-implement the mock to match the exact logic flow in fetch_elastic_data
        mock_session.reset_mock()
        mock_session.get.return_value.status_code = 404
        mock_session.get.return_value.json.return_value = mock_response_not_found
        
        # The function checks status code before raising
        result = fetch_elastic_data("mp-999", "fake_key")
        
        assert result is None

def test_fetch_dft_data_integration():
    """Test the full fetch_dft_data function with mocked API calls."""
    df = pd.DataFrame({
        'mp_id': ['mp-13', 'mp-14'],
        'composition': ['Fe', 'Fe-Cr'],
        'yield_strength_MPa': [250, 300]
    })

    mock_data_1 = {
        "data": {"elasticity": {"G_VRH": 80.0, "K_VRH": 160.0, "E_VRH": 200.0, "nu": 0.3}}
    }
    mock_data_2 = {
        "data": {"elasticity": {"G_VRH": 82.0, "K_VRH": 162.0, "E_VRH": 202.0, "nu": 0.31}}
    }

    def mock_fetch(mp_id, api_key):
        if mp_id == "mp-13":
            return {
                "mp_id": "mp-13",
                "shear_modulus_GPa": 80.0,
                "bulk_modulus_GPa": 160.0,
                "status": "success"
            }
        elif mp_id == "mp-14":
            return {
                "mp_id": "mp-14",
                "shear_modulus_GPa": 82.0,
                "bulk_modulus_GPa": 162.0,
                "status": "success"
            }
        return None

    with patch('ingestion.fetch_dft.fetch_elastic_data', side_effect=mock_fetch):
        result_df = fetch_dft_data(df)

        assert len(result_df) == 2
        assert 'shear_modulus_GPa' in result_df.columns
        assert 'bulk_modulus_GPa' in result_df.columns
        assert result_df.iloc[0]['shear_modulus_GPa'] == 80.0
        assert result_df.iloc[1]['shear_modulus_GPa'] == 82.0

def test_fetch_dft_data_missing_mp_id():
    """Test handling of missing MP IDs."""
    df = pd.DataFrame({
        'mp_id': ['mp-13', None, ''],
        'composition': ['Fe', 'Fe', 'Fe'],
        'yield_strength_MPa': [250, 260, 270]
    })

    def mock_fetch(mp_id, api_key):
        return {"mp_id": mp_id, "shear_modulus_GPa": 80.0, "status": "success"}

    with patch('ingestion.fetch_dft.fetch_elastic_data', side_effect=mock_fetch):
        result_df = fetch_dft_data(df)
        
        # Should only fetch for the one valid ID
        assert len(result_df) == 1
        assert result_df.iloc[0]['mp_id'] == 'mp-13'
