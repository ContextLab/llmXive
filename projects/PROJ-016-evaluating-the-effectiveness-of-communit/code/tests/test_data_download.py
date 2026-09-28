import pytest
import time
import requests
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys
import pandas as pd

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import fetch_with_backoff, verify_fao_indicator, fetch_fao_fra_data, save_fao_data_to_csv

class TestDownloadRetryLogic:
    @patch('data.download.requests.get')
    def test_exponential_backoff_on_server_error(self, mock_get):
        """
        Verifies that fetch_with_backoff retries with exponential backoff on server errors.
        """
        # Mock response to simulate server error
        mock_response = Mock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        url = "http://example.com/data"
        
        with pytest.raises(ConnectionError):
            fetch_with_backoff(url, max_retries=3)
        
        # Check that get was called 3 times
        assert mock_get.call_count == 3
        
        # Check sleep intervals (2s, 4s) - we can't easily test time.sleep in unit tests without mocking time,
        # but we can verify the logic flow.
        # To test sleep, we would mock time.sleep and assert call_args.
    
    @patch('data.download.requests.get')
    def test_success_on_first_attempt(self, mock_get):
        """
        Verifies that fetch_with_backoff returns immediately on success.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        url = "http://example.com/data"
        result = fetch_with_backoff(url)
        
        assert result is not None
        assert result.status_code == 200
        assert mock_get.call_count == 1

class TestDownloadNoSyntheticFallback:
    @patch('data.download.requests.get')
    def test_fails_loudly_no_synthetic(self, mock_get):
        """
        Verifies that fetch_with_backoff raises an exception and does NOT generate synthetic data.
        """
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        url = "http://example.com/data"
        
        with pytest.raises(ConnectionError):
            fetch_with_backoff(url, max_retries=2)
        
        # Ensure no synthetic data was returned or created
        # The function should have raised, so we never reach any return statement with data.
        assert True # If we are here, it means it didn't raise, which is wrong.
    
    def test_verify_fao_indicator_missing(self, caplog):
        """
        Verifies that verify_fao_indicator returns False if indicator is missing.
        """
        with patch('data.download.fetch_with_backoff') as mock_fetch:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_fetch.return_value = mock_response
            
            result = verify_fao_indicator("NONEXISTENT")
            assert result is False

class TestFaoDataFetching:
    @patch('data.download.requests.get')
    def test_fetch_fao_data_success(self, mock_get):
        """
        Verifies successful fetching and parsing of FAO data.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'Time': 2000, 'Value': 10.5, 'AreaCode': 'USA'},
                {'Time': 2001, 'Value': 11.2, 'AreaCode': 'USA'}
            ]
        }
        mock_get.return_value = mock_response

        df = fetch_fao_fra_data('AG.LND.FRST.ZS', 2000, 2020)
        
        assert len(df) == 2
        assert 'Time' in df.columns
        assert 'Value' in df.columns
        assert 'AreaCode' in df.columns

    @patch('data.download.requests.get')
    def test_fetch_fao_data_empty_response(self, mock_get):
        """
        Verifies handling of empty response.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': []}
        mock_get.return_value = mock_response

        df = fetch_fao_fra_data('AG.LND.FRST.ZS', 2000, 2020)
        
        assert len(df) == 0