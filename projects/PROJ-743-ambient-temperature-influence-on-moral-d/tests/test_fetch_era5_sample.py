"""
Unit tests for fetch_era5_sample.py
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# We cannot easily test the actual CDS API call in a unit test without credentials,
# so we mock the client.

def test_ensure_directories_exists():
    """Test that ensure_directories creates the output directory."""
    from fetch_era5_sample import ensure_directories
    
    # This function returns the path object, side effect is creating the dir
    result = ensure_directories()
    assert result.exists()
    assert result.is_dir()
    assert result.name == "raw"

def test_fetch_era5_sample_logic():
    """Test the logic of fetch_era5_sample by mocking the CDS client."""
    from fetch_era5_sample import fetch_era5_sample
    
    mock_client = MagicMock()
    
    with patch('fetch_era5_sample.cdsapi.Client', return_value=mock_client):
        # Mock the retrieve method to do nothing (simulate success)
        mock_client.retrieve.return_value = None
        
        # We need to ensure the directory exists first or the mock might fail on path
        # But the function creates it.
        success = fetch_era5_sample()
        
        # Verify the client was called with the correct arguments
        mock_client.retrieve.assert_called_once()
        call_args = mock_client.retrieve.call_args
        
        # Check dataset name
        assert call_args[0][0] == 'reanalysis-era5-single-levels'
        
        # Check request parameters
        request_params = call_args[0][1]
        assert request_params['variable'] == '2m_temperature'
        assert request_params['product_type'] == 'reanalysis'
        assert request_params['date'] == '2016-01-01/to/2016-01-07'
        assert request_params['area'] == [51.5, -0.1, 51.5, -0.1]
        assert request_params['format'] == 'netcdf'
        
        # Check output path
        output_path = call_args[0][2]
        assert output_path.endswith('era5_sample.h5')

def test_main_success_flow():
    """Test the main function success path."""
    from fetch_era5_sample import main
    
    # Mock the fetch function to return True
    with patch('fetch_era5_sample.fetch_era5_sample', return_value=True):
        # This should not raise
        # We also need to ensure the log file path is writable
        with patch('fetch_era5_sample.Path.mkdir'):
            with patch('builtins.open', MagicMock()):
                try:
                    main()
                except SystemExit:
                    pass # Expected if sys.exit(0) is called or similar flow

def test_main_failure_flow():
    """Test the main function failure path."""
    from fetch_era5_sample import main
    
    # Mock the fetch function to raise an exception
    with patch('fetch_era5_sample.fetch_era5_sample', side_effect=Exception("Mock Error")):
        with patch('builtins.open', MagicMock()):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
