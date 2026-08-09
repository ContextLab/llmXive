"""
Unit tests for T012d: Schema Verification.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import json
import tempfile
import os
from pathlib import Path

from src.ingestion import verify_schema, fetch_sample_headers, write_ingestion_report

class TestSchemaVerification:
    """Tests for schema verification functionality."""

    def test_verify_schema_success(self):
        """Test successful schema verification with all required columns."""
        headers = [
            'sample_id',
            'antibiotic_use_last_3m',
            'sleep_efficiency',
            'sleep_duration_hours',
            'other_column'
        ]
        required = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
        
        result = verify_schema(headers, required)
        
        assert result['status'] == 'success'
        assert result['measurement_status'] == 'measurable'
        assert 'All required columns present' in result['reason']

    def test_verify_schema_missing_columns(self):
        """Test schema verification with missing required columns."""
        headers = ['sample_id', 'antibiotic_use_last_3m']
        required = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
        
        result = verify_schema(headers, required)
        
        assert result['status'] == 'blocked'
        assert result['measurement_status'] == 'unmeasurable'
        assert 'Missing required columns' in result['reason']
        assert 'sleep_efficiency' in result['missing_columns']
        assert 'sleep_duration_hours' in result['missing_columns']

    def test_verify_schema_empty_headers(self):
        """Test schema verification with empty headers."""
        headers = []
        required = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
        
        result = verify_schema(headers, required)
        
        assert result['status'] == 'blocked'
        assert len(result['missing_columns']) == 3

    def test_write_ingestion_report(self):
        """Test writing ingestion report to file."""
        report = {
            'status': 'success',
            'reason': 'All required columns present',
            'measurement_status': 'measurable'
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, 'test_report.json')
            write_ingestion_report(report, report_path)
            
            assert os.path.exists(report_path)
            
            with open(report_path, 'r') as f:
                loaded_report = json.load(f)
            
            assert loaded_report == report

    @patch('src.ingestion.requests.get')
    def test_fetch_sample_headers_success(self, mock_get):
        """Test successful header fetching."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_lines = MagicMock(return_value=[b'sample_id,antibiotic_use_last_3m,sleep_efficiency,sleep_duration_hours'])
        mock_get.return_value = mock_response
        
        headers = fetch_sample_headers('http://example.com/data.csv')
        
        assert headers is not None
        assert 'antibiotic_use_last_3m' in headers
        assert 'sleep_efficiency' in headers
        assert 'sleep_duration_hours' in headers

    @patch('src.ingestion.requests.get')
    def test_fetch_sample_headers_failure(self, mock_get):
        """Test header fetching failure."""
        mock_get.side_effect = Exception("Network error")
        
        headers = fetch_sample_headers('http://example.com/data.csv')
        
        assert headers is None