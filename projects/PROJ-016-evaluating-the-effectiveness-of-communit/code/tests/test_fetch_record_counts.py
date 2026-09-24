"""
Tests for fetch_record_counts.py
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import sys
import os

# Add code directory to path
code_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_path))

from data.fetch_record_counts import get_fao_stream_url, fetch_fao_records_count, save_outputs

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@patch('data.fetch_record_counts.requests.get')
def test_fetch_fao_records_count_success(mock_get, temp_data_dir):
    """Test successful counting of FAO records."""
    # Mock response with CSV content
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_lines = MagicMock(return_value=[
        b'"Item Code","Item","Area","Year","Value"',  # Header
        b'"123","Forest Area","USA","2000","100"',
        b'"123","Forest Area","USA","2001","101"',
        b'"123","Forest Area","CAN","2000","200"',
    ])
    mock_get.return_value = mock_response

    count = fetch_fao_records_count('AG.LND.FRST.ZS')
    
    assert count == 3  # 3 data rows, header excluded
    mock_get.assert_called_once()

@patch('data.fetch_record_counts.requests.get')
def test_fetch_fao_records_count_empty(mock_get, temp_data_dir):
    """Test handling of empty response."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_lines = MagicMock(return_value=[
        b'"Item Code","Item","Area","Year","Value"'  # Only header
    ])
    mock_get.return_value = mock_response

    count = fetch_fao_records_count('AG.LND.FRST.ZS')
    
    assert count == 0

@patch('data.fetch_record_counts.requests.get')
def test_fetch_fao_records_count_retry_logic(mock_get):
    """Test retry logic on API failure."""
    # First two attempts fail, third succeeds
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_lines = MagicMock(return_value=[
        b'"Item Code","Item","Area","Year","Value"',
        b'"123","Forest Area","USA","2000","100"',
    ])
    
    # Configure side effect: raise on first two calls, return mock on third
    mock_get.side_effect = [
        Exception("Connection error"),
        Exception("Connection error"),
        mock_response
    ]

    count = fetch_fao_records_count('AG.LND.FRST.ZS')
    
    assert count == 1
    assert mock_get.call_count == 3

def test_save_outputs(temp_data_dir):
    """Test saving counts to JSON files."""
    counts = {'fao': 150, 'wb': 200}
    save_outputs(counts, temp_data_dir)
    
    fao_file = temp_data_dir / "counts_fao.json"
    wb_file = temp_data_dir / "counts_wb.json"
    
    assert fao_file.exists()
    assert wb_file.exists()
    
    with open(fao_file) as f:
        fao_data = json.load(f)
    assert fao_data == {"total_fao_available": 150}
    
    with open(wb_file) as f:
        wb_data = json.load(f)
    assert wb_data == {"total_wb_available": 200}

def test_get_fao_stream_url():
    """Test URL construction."""
    url = get_fao_stream_url('AG.LND.FRST.ZS')
    assert 'AG.LND.FRST.ZS' in url
    assert 'CSV' in url
    assert 'data/export' in url
