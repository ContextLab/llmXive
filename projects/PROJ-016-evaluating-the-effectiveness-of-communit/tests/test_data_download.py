"""
Unit tests for data download module.
"""
import pytest
import time
import requests
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys
import pandas as pd
import json
import tempfile
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import (
    fetch_with_backoff,
    load_world_bank_gdp_population,
    load_cbmrm_proxy_data,
    save_fao_data_to_csv,
    main
)
from config import get_config

class TestDownloadRetryLogic:
    @patch('data.download.requests.get')
    def test_fetch_with_backoff_success(self, mock_get):
        """Test that fetch_with_backoff succeeds on first try."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': []}
        mock_get.return_value = mock_response
        
        result = fetch_with_backoff('http://test.com')
        assert result.status_code == 200
        mock_get.assert_called_once()

    @patch('data.download.requests.get')
    def test_fetch_with_backoff_retries(self, mock_get):
        """Test that fetch_with_backoff retries on failure."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Error")
        mock_get.return_value = mock_response
        
        with pytest.raises(RuntimeError):
            fetch_with_backoff('http://test.com')
        
        # Should have retried MAX_RETRIES times
        assert mock_get.call_count == 3

class TestDownloadNoSyntheticFallback:
    @patch('data.download.requests.get')
    def test_no_synthetic_on_failure(self, mock_get):
        """Test that no synthetic data is generated on failure."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Error")
        mock_get.return_value = mock_response
        
        with pytest.raises(RuntimeError):
            load_world_bank_gdp_population([2000, 2001])
        
        # Verify no synthetic data was created
        # The function should have raised an exception, not returned synthetic data

class TestFaoDataFetching:
    def test_load_cbmrm_proxy_data_success(self, tmp_path):
        """Test loading CBNRM proxy data from a valid file."""
        # Create a temporary CSV file
        proxy_data = {
            'country_iso3': ['USA', 'CAN', 'MEX'],
            'year': [2000, 2000, 2000],
            'proxy_value': [0.5, 0.6, 0.7]
        }
        df = pd.DataFrame(proxy_data)
        proxy_file = tmp_path / 'cbnrm_proxy.csv'
        df.to_csv(proxy_file, index=False)
        
        # Load the data
        result = load_cbmrm_proxy_data(proxy_file)
        
        assert len(result) == 3
        assert 'country_iso3' in result.columns
        assert 'proxy_value' in result.columns

    def test_load_cbmrm_proxy_data_missing_file(self, tmp_path):
        """Test that loading CBNRM proxy data fails when file is missing."""
        missing_file = tmp_path / 'nonexistent.csv'
        
        with pytest.raises(FileNotFoundError):
            load_cbmrm_proxy_data(missing_file)

class TestMain:
    @patch('data.download.load_world_bank_gdp_population')
    @patch('data.download.load_cbmrm_proxy_data')
    def test_main_execution(self, mock_load_cbnrm, mock_load_wb, tmp_path):
        """Test that main() executes correctly."""
        # Mock the data loading functions
        mock_wb_df = pd.DataFrame({
            'country_iso3': ['USA', 'CAN'],
            'year': [2000, 2000],
            'gdp_per_capita': [50000, 45000],
            'population_density': [35, 4]
        })
        mock_wb_df.to_csv(tmp_path / 'world_bank_gdp_pop.csv', index=False)
        mock_load_wb.return_value = mock_wb_df
        
        mock_cbnrm_df = pd.DataFrame({
            'country_iso3': ['USA', 'CAN'],
            'year': [2000, 2000],
            'proxy_value': [0.5, 0.6]
        })
        mock_cbnrm_df.to_csv(tmp_path / 'cbnrm_proxy.csv', index=False)
        mock_load_cbnrm.return_value = mock_cbnrm_df
        
        # Change to temp directory to avoid writing to real data dirs
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create necessary directories
            (tmp_path / 'data' / 'raw').mkdir(parents=True, exist_ok=True)
            
            # Run main
            main()
            
            # Verify output files were created
            assert (tmp_path / 'data' / 'raw' / 'world_bank_gdp_pop.csv').exists()
            assert (tmp_path / 'data' / 'raw' / 'cbnrm_proxy_loaded.csv').exists()
        finally:
            os.chdir(original_cwd)