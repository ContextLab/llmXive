"""
Unit tests for verify_moral_machine_source.py
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import requests
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from verify_moral_machine_source import verify_source_access, validate_schema, REQUIRED_COLUMNS

class TestVerifySourceAccess:
    def test_successful_head_request(self):
        """Test successful HEAD request with 200 status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/csv'}
        
        with patch('verify_moral_machine_source.requests.head', return_value=mock_response):
            is_accessible, msg = verify_source_access("http://example.com/data.csv")
            assert is_accessible is True
            assert "HTTP 200" in msg

    def test_unsuccessful_request(self):
        """Test unsuccessful request with 404 status."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch('verify_moral_machine_source.requests.head', return_value=mock_response):
            is_accessible, msg = verify_source_access("http://example.com/missing.csv")
            assert is_accessible is False
            assert "404" in msg

    def test_network_error(self):
        """Test handling of network errors."""
        with patch('verify_moral_machine_source.requests.head', side_effect=requests.exceptions.Timeout):
            is_accessible, msg = verify_source_access("http://slow-or-down.com")
            assert is_accessible is False
            assert "Network error" in msg

class TestValidateSchema:
    def test_all_columns_present_correct_types(self):
        """Test dataframe with all required columns and correct types."""
        df = pd.DataFrame({
            'latitude': [1.0, 2.0],
            'longitude': [1.0, 2.0],
            'timestamp': pd.to_datetime(['2020-01-01', '2020-01-02']),
            'response_time': [100.0, 200.0],
            'country': ['US', 'UK'],
            'dilemma_id': ['D1', 'D2']
        })
        
        is_valid, errors = validate_schema(df, REQUIRED_COLUMNS)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_column(self):
        """Test dataframe missing a required column."""
        df = pd.DataFrame({
            'latitude': [1.0],
            'longitude': [1.0],
            # Missing timestamp, response_time, country, dilemma_id
        })
        
        is_valid, errors = validate_schema(df, REQUIRED_COLUMNS)
        assert is_valid is False
        assert "Missing required columns" in errors[0]

    def test_wrong_dtype_float(self):
        """Test dataframe with wrong dtype for a float column."""
        df = pd.DataFrame({
            'latitude': ['1.0', '2.0'], # String instead of float
            'longitude': [1.0, 2.0],
            'timestamp': pd.to_datetime(['2020-01-01', '2020-01-02']),
            'response_time': [100.0, 200.0],
            'country': ['US', 'UK'],
            'dilemma_id': ['D1', 'D2']
        })
        
        is_valid, errors = validate_schema(df, REQUIRED_COLUMNS)
        # latitude is string, expected float
        assert is_valid is False
        assert "latitude" in errors[0] or "dtype" in errors[0]

    def test_datetime_dtype(self):
        """Test dataframe with datetime column."""
        df = pd.DataFrame({
            'latitude': [1.0, 2.0],
            'longitude': [1.0, 2.0],
            'timestamp': ['2020-01-01', '2020-01-02'], # String representation is allowed per logic
            'response_time': [100.0, 200.0],
            'country': ['US', 'UK'],
            'dilemma_id': ['D1', 'D2']
        })
        
        is_valid, errors = validate_schema(df, REQUIRED_COLUMNS)
        # Our logic allows string for datetime if it's object/string dtype
        assert is_valid is True