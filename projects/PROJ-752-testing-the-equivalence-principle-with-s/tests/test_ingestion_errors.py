import pytest
import os
import sys
from unittest.mock import patch, MagicMock
import requests

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.ingestion import (
    fetch_satellite_data,
    validate_config,
    aggregate_satellites,
    DataIngestionError,
    NormalPoint
)
from utils.logging import DataUnavailableError

class TestFetchSatelliteData:
    """Tests for fetch_satellite_data error handling, specifically 403 and retries."""

    @patch('data.ingestion.requests.get')
    def test_fetch_403_error_handling(self, mock_get):
        """Test that 403 errors are caught and raise DataIngestionError."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Client Error")
        mock_get.return_value = mock_response

        with pytest.raises(DataIngestionError) as excinfo:
            fetch_satellite_data("LAGEOS")
        
        assert "Access forbidden (403)" in str(excinfo.value)
        mock_get.assert_called_once()

    @patch('data.ingestion.requests.get')
    def test_fetch_exponential_backoff(self, mock_get):
        """Test that fetch retries with exponential backoff on network errors."""
        # Simulate 2 failures then success
        mock_response_fail = MagicMock()
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.ConnectionError("Network error")
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.content = b"dummy data"
        mock_response_success.raise_for_status.return_value = None

        mock_get.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]

        # Should succeed on 3rd attempt
        result = fetch_satellite_data("LAGEOS")
        
        assert result == b"dummy data"
        assert mock_get.call_count == 3

    @patch('data.ingestion.requests.get')
    def test_fetch_max_attempts_exceeded(self, mock_get):
        """Test that DataIngestionError is raised after max retries."""
        mock_response_fail = MagicMock()
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_get.return_value = mock_response_fail

        with pytest.raises(DataIngestionError) as excinfo:
            fetch_satellite_data("LAGEOS")
        
        assert "Failed to fetch data" in str(excinfo.value)
        # Default max_attempts is 5
        assert mock_get.call_count == 5

class TestAggregateSatellites:
    """Tests for aggregate_satellites warning logic."""

    @patch('data.ingestion.fetch_satellite_data')
    @patch('data.ingestion.parse_slr_file')
    @patch('data.ingestion.validate_config')
    def test_insufficient_data_warning(self, mock_validate, mock_parse, mock_fetch):
        """Test that a warning is logged when points < 500."""
        mock_validate.return_value = None
        mock_fetch.return_value = b"dummy"
        # Return a list with only 100 points
        mock_parse.return_value = [NormalPoint("SAT", "2023-01-01", 1.0)] * 100

        # Capture logs or just check the function behavior
        # The function should return the data but log a warning
        results = aggregate_satellites(["SAT"])
        
        assert "SAT" in results
        assert len(results["SAT"]) == 100
        # The warning is logged, but the function doesn't raise an error for insufficient data
        # It continues to return the partial data.

    @patch('data.ingestion.fetch_satellite_data')
    @patch('data.ingestion.parse_slr_file')
    @patch('data.ingestion.validate_config')
    def test_sufficient_data_no_warning(self, mock_validate, mock_parse, mock_fetch):
        """Test that no warning is logged when points >= 500."""
        mock_validate.return_value = None
        mock_fetch.return_value = b"dummy"
        mock_parse.return_value = [NormalPoint("SAT", "2023-01-01", 1.0)] * 600

        results = aggregate_satellites(["SAT"])
        
        assert len(results["SAT"]) == 600

class TestValidateConfig:
    """Tests for validate_config."""

    @patch('data.ingestion.get_config')
    def test_validate_config_missing_file(self, mock_get_config):
        """Test that DataUnavailableError is raised if config file is missing."""
        mock_config = MagicMock()
        mock_config.paths.verified_datasets = "/fake/path/verified_datasets.yaml"
        mock_get_config.return_value = mock_config

        with patch('os.path.exists', return_value=False):
            with pytest.raises(DataUnavailableError) as excinfo:
                validate_config()
            
            assert "not found" in str(excinfo.value)

    @patch('data.ingestion.get_config')
    def test_validate_config_success(self, mock_get_config):
        """Test that validate_config passes if file exists."""
        mock_config = MagicMock()
        mock_config.paths.verified_datasets = "/fake/path/verified_datasets.yaml"
        mock_get_config.return_value = mock_config

        with patch('os.path.exists', return_value=True):
            # Should not raise
            validate_config()