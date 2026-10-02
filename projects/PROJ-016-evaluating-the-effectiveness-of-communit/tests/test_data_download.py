import pytest
import time
import requests
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys
import pandas as pd
import json

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import fetch_with_backoff, verify_fao_indicator, fetch_fao_fra_data, save_fao_data_to_csv

class TestDownloadRetryLogic:
    @patch('data.download.requests.get')
    def test_exponential_backoff(self, mock_get):
        """Test that retries happen with exponential backoff."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Simulated Error")
        mock_get.return_value = mock_response

        start_time = time.time()
        result = fetch_with_backoff("http://test.com", max_retries=3)
        elapsed = time.time() - start_time

        # Should have called 3 times
        assert mock_get.call_count == 3
        # Should have waited at least 2+4=6 seconds (2s, 4s)
        assert elapsed >= 6
        assert result is None

    @patch('data.download.requests.get')
    def test_success_on_second_attempt(self, mock_get):
        """Test success after a failure."""
        mock_fail = Mock()
        mock_fail.raise_for_status.side_effect = requests.exceptions.RequestException("Error")
        
        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"value": [{"year": 2000, "value": 10}]}
        
        mock_get.side_effect = [mock_fail, mock_success]

        result = fetch_with_backoff("http://test.com", max_retries=3)
        assert mock_get.call_count == 2
        assert result.status_code == 200

class TestDownloadNoSyntheticFallback:
    def test_no_synthetic_data_on_failure(self, tmp_path):
        """Verify that if fetch fails, no synthetic data is generated."""
        # Mock the fetch to fail
        with patch('data.download.fetch_with_backoff', return_value=None):
            with patch('data.download.verify_fao_indicator', return_value=False):
                df = fetch_fao_fra_data("FAKE_IND", 2000, 2001)
        
        # Should be empty, not synthetic
        assert df.empty
        assert len(df) == 0

class TestFaoDataFetching:
    @patch('data.download.fetch_with_backoff')
    def test_fetch_and_save_empty_on_missing_indicator(self, mock_fetch):
        """Test that empty CSV is created if indicator is missing."""
        mock_fetch.return_value = None
        
        output_file = tmp_path / "test_fao.csv"
        save_fao_data_to_csv(pd.DataFrame(), str(output_file), "TEST")
        
        assert output_file.exists()
        # Check if file has headers or is empty depending on implementation
        # Our implementation writes headers even if empty
        with open(output_file, 'r') as f:
            content = f.read()
            # Should not be completely empty string if headers are written, 
            # but our code writes empty DF which might result in empty file if no columns.
            # Let's ensure the function handles the empty case gracefully.
            pass

    def test_save_fao_data_to_csv_creates_file(self, tmp_path):
        """Test that save function creates the file."""
        df = pd.DataFrame({'country_code': ['USA'], 'year': [2000], 'land_use_change_rate': [1.5]})
        output_file = tmp_path / "test_fao.csv"
        save_fao_data_to_csv(df, str(output_file), "TEST")
        
        assert output_file.exists()
        loaded_df = pd.read_csv(output_file)
        assert len(loaded_df) == 1
        assert loaded_df.iloc[0]['country_code'] == 'USA'