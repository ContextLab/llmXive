import pytest
import time
import requests
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys
import pandas as pd
import json

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import fetch_with_backoff, fetch_fao_fra_data, save_fao_data_to_csv
from logging_config import get_logger

logger = get_logger(__name__)

class TestDownloadRetryLogic:
    @patch('data.download.requests.get')
    def test_download_exponential_backoff(self, mock_get):
        """
        Test that fetch_with_backoff retries 3 times with exponential backoff 
        on server errors (500, 503, etc.) and then raises an exception.
        """
        # Setup mock to fail 3 times then succeed
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Internal Server Error"
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"data": "ok"}
        
        # Sequence: Fail, Fail, Fail, Success (or Fail all 3)
        # We want to test the retry logic, so we fail 3 times and then raise an error
        # or we fail 3 times and succeed on 4th? The function has max_retries=3.
        # It tries 3 times. If all fail, it raises.
        
        mock_get.side_effect = [
            mock_response_fail, # Attempt 1
            mock_response_fail, # Attempt 2
            mock_response_fail, # Attempt 3
        ]
        
        with pytest.raises(Exception) as exc_info:
            fetch_with_backoff("http://test.com", {}, max_retries=3)
        
        assert "Failed to fetch" in str(exc_info.value)
        assert mock_get.call_count == 3

    @patch('data.download.requests.get')
    def test_download_success_on_first_try(self, mock_get):
        """Test success on first attempt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "ok"}
        mock_get.return_value = mock_response
        
        result = fetch_with_backoff("http://test.com", {}, max_retries=3)
        assert result.status_code == 200
        assert mock_get.call_count == 1

    @patch('data.download.requests.get')
    def test_download_no_synthetic_fallback(self, mock_get):
        """
        Test that if the fetch fails, the function raises an exception 
        and does NOT generate synthetic data.
        """
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_get.return_value = mock_response_fail
        
        with pytest.raises(Exception):
            fetch_with_backoff("http://test.com", {}, max_retries=1)
        
        # Ensure no synthetic data generation logic was triggered
        # (Implicitly tested by the fact that we got an exception and not a dataframe)

class TestFAODataFetch:
    @patch('data.download.fetch_with_backoff')
    def test_fetch_fao_fra_data_success(self, mock_fetch):
        """Test successful fetch of FAO data."""
        # Mock response structure for World Bank API (used as FAO source)
        mock_response = Mock()
        mock_response.json.return_value = [
            {"page": 1, "pages": 1, "per_page": 50, "total": 2},
            [
                {"countryiso3code": "USA", "date": "2000", "value": 30.5, "country": {"value": "United States"}},
                {"countryiso3code": "USA", "date": "2001", "value": 30.6, "country": {"value": "United States"}}
            ]
        ]
        mock_fetch.return_value = mock_response
        
        df = fetch_fao_fra_data()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'country_code' in df.columns
        assert 'year' in df.columns
        assert 'value' in df.columns
        assert df.iloc[0]['country_code'] == 'USA'
        assert df.iloc[0]['year'] == 2000

    @patch('data.download.fetch_with_backoff')
    def test_fetch_fao_fra_data_empty(self, mock_fetch):
        """Test handling of empty data."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"page": 1, "pages": 1, "per_page": 50, "total": 0},
            []
        ]
        mock_fetch.return_value = mock_response
        
        with pytest.raises(ValueError, match="No data found"):
            fetch_fao_fra_data()

    @patch('data.download.fetch_with_backoff')
    def test_fetch_fao_fra_data_invalid_response(self, mock_fetch):
        """Test handling of invalid API response."""
        mock_response = Mock()
        mock_response.json.return_value = [{"error": "bad"}]
        mock_fetch.return_value = mock_response
        
        with pytest.raises(ValueError):
            fetch_fao_fra_data()

class TestSaveFaoData:
    def test_save_fao_data_to_csv(self, tmp_path):
        """Test saving data to CSV."""
        df = pd.DataFrame({
            'country_code': ['USA', 'CAN'],
            'year': [2000, 2000],
            'value': [30.5, 35.0]
        })
        
        output_file = tmp_path / "test_fao.csv"
        save_fao_data_to_csv(df, str(output_file))
        
        assert output_file.exists()
        loaded_df = pd.read_csv(output_file)
        assert len(loaded_df) == 2
        assert loaded_df.iloc[0]['country_code'] == 'USA'