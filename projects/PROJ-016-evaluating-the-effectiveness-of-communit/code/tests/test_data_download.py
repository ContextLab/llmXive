"""
Tests for data download module.
"""
import pytest
import time
import requests
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys
import json
import pandas as pd
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import fetch_with_backoff, load_world_bank_gdp_population, load_cbmrm_proxy_data

class TestDownloadRetryLogic:
    @patch('data.download.requests.get')
    def test_exponential_backoff(self, mock_get):
        """Test that fetch_with_backoff retries with exponential backoff."""
        # Mock a response that always fails
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
        mock_get.return_value = mock_response

        with patch('time.sleep') as mock_sleep:
            result = fetch_with_backoff("http://example.com")
            assert result is None
            # Check that sleep was called with increasing intervals
            calls = mock_sleep.call_args_list
            assert len(calls) == 2  # MAX_RETRIES=3, so 2 sleeps between 3 attempts
            # First sleep: 2^1 = 2, Second sleep: 2^2 = 4 (approx)
            assert calls[0][0][0] >= 1.0  # At least 1 second
            assert calls[1][0][0] >= 2.0  # At least 2 seconds

    @patch('data.download.requests.get')
    def test_success_on_first_try(self, mock_get):
        """Test successful fetch on first attempt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"key": "value"}]}
        mock_get.return_value = mock_response

        result = fetch_with_backoff("http://example.com")
        assert result == {"data": [{"key": "value"}]}
        mock_get.assert_called_once()

    @patch('data.download.requests.get')
    def test_rate_limit_handling(self, mock_get):
        """Test handling of 429 Rate Limit."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '1'}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Rate Limit")
        
        # First call returns 429, second succeeds
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"data": [{"key": "value"}]}
        
        mock_get.side_effect = [mock_response, success_response]

        with patch('time.sleep') as mock_sleep:
            result = fetch_with_backoff("http://example.com")
            assert result == {"data": [{"key": "value"}]}
            assert mock_get.call_count == 2
            mock_sleep.assert_called()

class TestDownloadNoSyntheticFallback:
    @patch('data.download.requests.get')
    def test_fetch_fails_loudly_no_synthetic(self, mock_get):
        """Test that fetch fails loudly without generating synthetic data."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
        mock_get.return_value = mock_response

        with patch('time.sleep'):
            result = fetch_with_backoff("http://example.com")
            assert result is None
            # Ensure no synthetic data is generated or returned
            assert not isinstance(result, pd.DataFrame)
            assert result is None

    def test_load_world_bank_no_synthetic_on_failure(self):
        """Test that load_world_bank_gdp_population returns empty DF, not synthetic."""
        with patch('data.download.fetch_with_backoff') as mock_fetch:
            mock_fetch.return_value = None  # Simulate failure
            
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "test.csv"
                df = load_world_bank_gdp_population(2000, 2020, output_path)
                
                assert df is not None
                assert df.empty
                assert list(df.columns) == ['Country', 'CountryCode', 'Year', 'GDP', 'Population_Density']
                # Ensure file is created (even if empty)
                assert output_path.exists()

    def test_load_cbmrm_proxy_missing_file(self):
        """Test loading missing proxy file."""
        result = load_cbmrm_proxy_data(Path("non_existent_file.csv"))
        assert result is None