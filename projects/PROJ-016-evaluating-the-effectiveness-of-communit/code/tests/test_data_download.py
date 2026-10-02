import pytest
import time
import requests
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys
import pandas as pd
import json

# Add code to path for imports
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.download import (
    fetch_with_backoff,
    load_world_bank_gdp_population,
    load_cbmrm_proxy_data
)

class TestDownloadRetryLogic:
    @patch('data.download.requests.get')
    def test_exponential_backoff_retries(self, mock_get):
        """Test that fetch_with_backoff retries with exponential backoff on failure."""
        # Mock response to raise an exception
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        # Call the function
        result = fetch_with_backoff("http://example.com", {}, max_retries=3)
        
        # Verify requests.get was called 3 times
        assert mock_get.call_count == 3
        
        # Verify result is None (failure)
        assert result is None

    @patch('data.download.requests.get')
    def test_success_on_first_attempt(self, mock_get):
        """Test that fetch_with_backoff returns data on first success."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = [
            {}, 
            [
                {
                    'indicator': {'id': 'NY.GDP.PCAP.CD'},
                    'value': 50000,
                    'date': '2020',
                    'countryiso3code': 'USA',
                    'country': 'United States'
                }
            ]
        ]
        mock_get.return_value = mock_response
        
        result = fetch_with_backoff("http://example.com", {})
        
        # Verify only one call was made
        assert mock_get.call_count == 1
        
        # Verify result is a DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

class TestDownloadNoSyntheticFallback:
    @patch('data.download.requests.get')
    def test_no_synthetic_data_on_failure(self, mock_get):
        """Test that fetch_with_backoff does not generate synthetic data on failure."""
        # Mock response to always fail
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        result = fetch_with_backoff("http://example.com", {}, max_retries=2)
        
        # Verify no synthetic data is returned
        assert result is None

class TestWorldBankDataLoading:
    @patch('data.download.fetch_with_backoff')
    def test_load_world_bank_gdp_population_success(self, mock_fetch):
        """Test loading World Bank GDP and Population Density data."""
        # Mock successful fetch for both indicators
        mock_df = pd.DataFrame([
            {
                'indicator': {'id': 'NY.GDP.PCAP.CD'},
                'value': 50000,
                'date': '2020',
                'countryiso3code': 'USA',
                'country': 'United States'
            },
            {
                'indicator': {'id': 'SP.POP.DENS'},
                'value': 35.6,
                'date': '2020',
                'countryiso3code': 'USA',
                'country': 'United States'
            }
        ])
        mock_fetch.return_value = mock_df
        
        result = load_world_bank_gdp_population(year_start=2020, year_end=2020)
        
        # Verify result is a DataFrame
        assert isinstance(result, pd.DataFrame)
        
        # Verify expected columns exist
        expected_cols = ['country', 'country_code', 'year', 'gdp_per_capita', 'pop_density']
        assert all(col in result.columns for col in expected_cols)
        
        # Verify data is populated
        assert len(result) > 0

    @patch('data.download.fetch_with_backoff')
    def test_load_world_bank_gdp_population_empty(self, mock_fetch):
        """Test loading World Bank data when no data is available."""
        mock_fetch.return_value = None
        
        result = load_world_bank_gdp_population(year_start=2020, year_end=2020)
        
        # Verify result is an empty DataFrame with correct columns
        assert isinstance(result, pd.DataFrame)
        assert 'gdp_per_capita' in result.columns
        assert 'pop_density' in result.columns
        assert len(result) == 0

class TestCBNRMProxyLoading:
    def test_load_cbmrm_proxy_data_missing_file(self, tmp_path):
        """Test loading CBNRM proxy data when file is missing."""
        non_existent_path = tmp_path / "non_existent.csv"
        
        result = load_cbmrm_proxy_data(non_existent_path)
        
        # Verify None is returned
        assert result is None

    def test_load_cbmrm_proxy_data_success(self, tmp_path):
        """Test loading CBNRM proxy data successfully."""
        # Create a temporary CSV file
        csv_path = tmp_path / "cbnrm_proxy.csv"
        csv_path.write_text("country,country_code,year,proxy_value\nUSA,USA,2020,0.5\n")
        
        result = load_cbmrm_proxy_data(csv_path)
        
        # Verify DataFrame is returned
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]['country'] == 'USA'
        assert result.iloc[0]['proxy_value'] == 0.5
