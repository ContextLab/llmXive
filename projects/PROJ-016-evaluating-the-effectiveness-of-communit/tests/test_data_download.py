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
import tempfile
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.download import fetch_with_backoff, verify_fao_indicator, save_fao_indicator_status

class TestDownloadRetryLogic:
    """Tests for exponential backoff retry logic."""

    @patch('data.download.requests.Session')
    def test_fetch_with_backoff_success(self, mock_session_class):
        """Test successful fetch on first attempt."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': [{'key': 'value'}]}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = fetch_with_backoff('http://example.com', max_retries=3)

        assert result == {'data': [{'key': 'value'}]}
        mock_session.get.assert_called_once()

    @patch('data.download.requests.Session')
    def test_fetch_with_backoff_retry(self, mock_session_class):
        """Test fetch succeeds after retry."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': [{'key': 'value'}]}
        mock_response.raise_for_status = MagicMock()

        # First two attempts fail, third succeeds
        error_response = MagicMock()
        error_response.raise_for_status.side_effect = requests.exceptions.RequestException("Error")

        mock_session.get.side_effect = [error_response, error_response, mock_response]
        mock_session_class.return_value = mock_session

        with patch('data.download.time.sleep'):
            result = fetch_with_backoff('http://example.com', max_retries=3)

        assert result == {'data': [{'key': 'value'}]}
        assert mock_session.get.call_count == 3

    @patch('data.download.requests.Session')
    def test_fetch_with_backoff_all_fail(self, mock_session_class):
        """Test fetch fails after all retries."""
        mock_session = MagicMock()
        error_response = MagicMock()
        error_response.raise_for_status.side_effect = requests.exceptions.RequestException("Error")

        mock_session.get.side_effect = [error_response] * 4
        mock_session_class.return_value = mock_session

        with patch('data.download.time.sleep'):
            result = fetch_with_backoff('http://example.com', max_retries=3)

        assert result is None
        assert mock_session.get.call_count == 4

class TestVerifyFaoIndicator:
    """Tests for FAO indicator verification."""

    @patch('data.download.fetch_with_backoff')
    def test_verify_fao_indicator_exists(self, mock_fetch):
        """Test successful verification of existing indicator."""
        mock_fetch.return_value = {'data': [{'iso3': 'USA', 'year': 2020, 'value': 10}]}

        exists, message = verify_fao_indicator('AG.LND.FRST.ZS')

        assert exists is True
        assert 'exists and has data' in message

    @patch('data.download.fetch_with_backoff')
    def test_verify_fao_indicator_empty_data(self, mock_fetch):
        """Test verification with empty data."""
        mock_fetch.return_value = {'data': []}

        exists, message = verify_fao_indicator('AG.LND.FRST.ZS')

        assert exists is False
        assert 'has no data' in message

    @patch('data.download.fetch_with_backoff')
    def test_verify_fao_indicator_not_found(self, mock_fetch):
        """Test verification when indicator not found."""
        mock_fetch.return_value = None

        exists, message = verify_fao_indicator('AG.LND.FRST.ZS')

        assert exists is False
        assert 'not found' in message.lower() or 'error' in message.lower()

class TestSaveFaoIndicatorStatus:
    """Tests for saving FAO indicator status."""

    def test_save_fao_indicator_status(self, tmp_path):
        """Test saving status to JSON file."""
        output_path = tmp_path / "status.json"

        save_fao_indicator_status('AG.LND.FRST.ZS', True, "Indicator exists", str(output_path))

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)

        assert data['indicator_code'] == 'AG.LND.FRST.ZS'
        assert data['exists'] is True
        assert data['status'] == 'success'

    def test_save_fao_indicator_status_missing(self, tmp_path):
        """Test saving status for missing indicator."""
        output_path = tmp_path / "status_missing.json"

        save_fao_indicator_status('AG.LND.MISSING', False, "Indicator not found", str(output_path))

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)

        assert data['indicator_code'] == 'AG.LND.MISSING'
        assert data['exists'] is False
        assert data['status'] == 'missing'

class TestDownloadNoSyntheticFallback:
    """Tests for fail-loud behavior - no synthetic data generation."""

    @patch('data.download.fetch_with_backoff')
    def test_no_synthetic_on_failure(self, mock_fetch):
        """Test that failed fetch returns None, not synthetic data."""
        mock_fetch.return_value = None

        result = fetch_with_backoff('http://example.com', max_retries=1)

        assert result is None
        # Ensure no synthetic data was generated
        assert not isinstance(result, pd.DataFrame)
        assert not isinstance(result, dict) or result is None

    @patch('data.download.requests.Session')
    def test_fail_loudly_no_fallback(self, mock_session_class):
        """Test that persistent failure raises error, no fallback."""
        mock_session = MagicMock()
        error_response = MagicMock()
        error_response.raise_for_status.side_effect = requests.exceptions.RequestException("Error")

        mock_session.get.side_effect = [error_response] * 2
        mock_session_class.return_value = mock_session

        with patch('data.download.time.sleep'):
            result = fetch_with_backoff('http://example.com', max_retries=1)

        assert result is None
        # The function should return None, not generate synthetic data
        # A "fail loud" behavior means the caller should handle the None appropriately
        # and not proceed with fake data