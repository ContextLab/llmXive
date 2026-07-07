"""
Tests for T009: Fetch CBNRM Proxy.

These tests verify:
1. The indicator code validation logic.
2. The data fetching function (mocked).
3. The output file generation (mocked).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.fetch_cbmrm_proxy import (
    fetch_world_bank_indicator,
    validate_indicator_code,
    save_outputs,
    CBNRM_PROXY_INDICATOR
)

class TestFetchCbNrmProxy:
    
    @patch('data.fetch_cbmrm_proxy.requests.get')
    def test_fetch_world_bank_indicator_success(self, mock_get):
        """Test successful data fetching with mock response."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"page": 1, "pages": 1, "per_page": 50, "total": 2},
            [
                {"country": {"id": "USA", "value": "United States"}, "date": "2020", "value": 33.0},
                {"country": {"id": "USA", "value": "United States"}, "date": "2019", "value": 33.1}
            ]
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        data = fetch_world_bank_indicator("AG.LND.FRST.ZS", 2019, 2020)
        
        assert len(data) == 2
        assert data[0]['country']['id'] == 'USA'
        assert data[0]['date'] == '2020'
        mock_get.assert_called_once()
    
    @patch('data.fetch_cbmrm_proxy.requests.get')
    def test_validate_indicator_code_true(self, mock_get):
        """Test validation returns True when data exists."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"page": 1, "pages": 1, "per_page": 1, "total": 1},
            [
                {"country": {"id": "USA", "value": "United States"}, "date": "2020", "value": 33.0}
            ]
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        assert validate_indicator_code("AG.LND.FRST.ZS") is True
    
    @patch('data.fetch_cbmrm_proxy.requests.get')
    def test_validate_indicator_code_false(self, mock_get):
        """Test validation returns False when no data exists."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"page": 1, "pages": 1, "per_page": 1, "total": 0},
            []
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        assert validate_indicator_code("INVALID.CODE") is False
    
    def test_save_outputs_creates_files(self):
        """Test that save_outputs creates the expected CSV and JSON files."""
        sample_data = [
            {"country": {"id": "USA", "value": "United States"}, "date": "2020", "value": 33.0},
            {"country": {"id": "USA", "value": "United States"}, "date": "2019", "value": 33.1}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            csv_path = tmp_path / "test_data.csv"
            meta_path = tmp_path / "test_meta.json"
            
            save_outputs(
                data=sample_data,
                indicator_code="TEST.001",
                indicator_name="Test Indicator",
                source_url="http://example.com",
                output_csv=csv_path,
                output_metadata=meta_path
            )
            
            assert csv_path.exists()
            assert meta_path.exists()
            
            # Verify CSV content
            df = pd.read_csv(csv_path)
            assert len(df) == 2
            assert 'country_code' in df.columns
            assert 'value' in df.columns
            
            # Verify JSON content
            with open(meta_path) as f:
                meta = json.load(f)
            assert meta['indicator_code'] == "TEST.001"
            assert meta['record_count'] == 2
            assert meta['source_url'] == "http://example.com"
    
    def test_save_outputs_empty_data(self):
        """Test handling of empty data list."""
        sample_data = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            csv_path = tmp_path / "test_data.csv"
            meta_path = tmp_path / "test_meta.json"
            
            save_outputs(
                data=sample_data,
                indicator_code="TEST.001",
                indicator_name="Test Indicator",
                source_url="http://example.com",
                output_csv=csv_path,
                output_metadata=meta_path
            )
            
            assert csv_path.exists()
            assert meta_path.exists()
            
            df = pd.read_csv(csv_path)
            assert len(df) == 0
            
            with open(meta_path) as f:
                meta = json.load(f)
            assert meta['record_count'] == 0