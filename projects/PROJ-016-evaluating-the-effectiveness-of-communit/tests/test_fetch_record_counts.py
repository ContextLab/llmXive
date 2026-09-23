"""
Tests for fetch_record_counts module.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.fetch_record_counts import get_fao_stream_url, fetch_fao_records_count, save_outputs

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def mock_fao_response():
    """Mock response for FAO API that simulates CSV data."""
    # Simulate a CSV response with a header and some data rows
    csv_data = """Domain Code,Item Code,Area Code,Area,Year,Unit,Value
    AG,AG.LND.FRST.ZS,1,Country A,2000,Percent,10.5
    AG,AG.LND.FRST.ZS,1,Country A,2001,Percent,10.2
    AG,AG.LND.FRST.ZS,2,Country B,2000,Percent,20.1
    AG,AG.LND.FRST.ZS,2,Country B,2001,Percent,19.8
    """
    mock_response = MagicMock()
    mock_response.headers = {'Content-Type': 'text/csv'}
    mock_response.iter_lines.return_value = [line.encode('utf-8') for line in csv_data.strip().split('\n')]
    mock_response.raise_for_status = MagicMock()
    return mock_response

def test_get_fao_stream_url():
    url = get_fao_stream_url("AG.LND.FRST.ZS", 2000, 2020)
    assert "AG.LND.FRST.ZS" in url
    assert "fao.org" in url

@patch('data.fetch_record_counts.requests.Session')
def test_fetch_fao_records_count(mock_session, temp_data_dir):
    mock_response = mock_fao_response()
    mock_session.return_value.get.return_value = mock_response
    
    count = fetch_fao_records_count("AG.LND.FRST.ZS", 2000, 2020)
    
    # We expect 4 data rows (excluding header)
    assert count == 4
    mock_session.return_value.get.assert_called_once()

@patch('data.fetch_record_counts.requests.Session')
def test_fetch_fao_records_count_empty(mock_session, temp_data_dir):
    mock_response = MagicMock()
    mock_response.headers = {'Content-Type': 'text/csv'}
    mock_response.iter_lines.return_value = []
    mock_response.raise_for_status = MagicMock()
    
    mock_session.return_value.get.return_value = mock_response
    
    count = fetch_fao_records_count("AG.LND.FRST.ZS", 2000, 2020)
    assert count == 0

def test_save_outputs(temp_data_dir):
    output_path = temp_data_dir / "counts_fao.json"
    save_outputs(100, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data["total_fao_available"] == 100
    assert data["indicator_code"] == "AG.LND.FRST.ZS"