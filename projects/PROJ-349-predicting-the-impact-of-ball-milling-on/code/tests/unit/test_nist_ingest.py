"""
Unit tests for NIST Repository Downloader (T013).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

from src.ingest.nist_repo import (
    calculate_sha256,
    validate_checksum,
    fetch_data,
    parse_csv,
    extract_psd_metrics,
    run_nist_ingestion,
    DataIngestionError,
    SourceConnectionError,
    SourceNotFoundError,
    DataFormatError
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def mock_csv_content():
    return """material_id,d10,d50,d90,material_type,milling_speed
    mat001,5.2,12.5,25.0,Ceramic,500
    mat002,3.1,8.4,15.2,Metal,600
    mat003,10.0,20.0,40.0,Polymer,450
    """

@pytest.fixture
def mock_csv_path(temp_dir, mock_csv_content):
    path = temp_dir / "test_data.csv"
    path.write_text(mock_csv_content)
    return path

def test_calculate_sha256(mock_csv_path):
    """Test SHA256 calculation."""
    checksum = calculate_sha256(mock_csv_path)
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)

def test_validate_checksum_success(mock_csv_path):
    """Test successful checksum validation."""
    checksum = calculate_sha256(mock_csv_path)
    assert validate_checksum(mock_csv_path, checksum) is True

def test_validate_checksum_mismatch(mock_csv_path):
    """Test checksum mismatch detection."""
    assert validate_checksum(mock_csv_path, "wrong_checksum") is False

def test_fetch_data_success(temp_dir):
    """Test successful data fetch."""
    output_path = temp_dir / "downloaded.csv"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"test,data\n1,2"
    
    with patch('src.ingest.nist_repo.requests.get', return_value=mock_response):
        result = fetch_data("http://example.com/data.csv", output_path)
        assert result.exists()
        assert result.read_bytes() == b"test,data\n1,2"

def test_fetch_data_404(temp_dir):
    """Test 404 handling."""
    output_path = temp_dir / "downloaded.csv"
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    with patch('src.ingest.nist_repo.requests.get', return_value=mock_response):
        with pytest.raises(SourceNotFoundError):
            fetch_data("http://example.com/not_found.csv", output_path)

def test_parse_csv(mock_csv_path):
    """Test CSV parsing."""
    df = parse_csv(mock_csv_path)
    assert len(df) == 3
    assert 'd50' in df.columns

def test_extract_psd_metrics():
    """Test PSD metric extraction."""
    data = {
        'material_id': ['m1', 'm2'],
        'd10': [1.0, 2.0],
        'd50': [5.0, 10.0],
        'd90': [10.0, 20.0],
        'extra_col': ['a', 'b']
    }
    df = pd.DataFrame(data)
    result = extract_psd_metrics(df)
    
    assert 'd10' in result.columns
    assert 'd50' in result.columns
    assert 'd90' in result.columns
    assert len(result) == 2
    # Check if extra columns are handled or dropped based on logic
    # The implementation keeps 'material_id' and PSDs, drops others unless mapped
    assert 'material_id' in result.columns

def test_extract_psd_metrics_missing_cols():
    """Test extraction failure on missing columns."""
    data = {
        'material_id': ['m1'],
        'd10': [1.0],
        # Missing d50 and d90
    }
    df = pd.DataFrame(data)
    with pytest.raises(DataFormatError):
        extract_psd_metrics(df)

@patch('src.ingest.nist_repo.fetch_data')
@patch('src.ingest.nist_repo.parse_csv')
@patch('src.ingest.nist_repo.extract_psd_metrics')
def test_download_nist_data_full_flow(mock_extract, mock_parse, mock_fetch, temp_dir):
    """Test full ingestion flow with mocked dependencies."""
    mock_df = pd.DataFrame({'d10': [1], 'd50': [2], 'd90': [3], 'material_id': ['m1']})
    mock_fetch.return_value = temp_dir / "data.csv"
    mock_parse.return_value = pd.DataFrame({'d10': [1], 'd50': [2], 'd90': [3], 'material_id': ['m1']})
    mock_extract.return_value = mock_df
    
    # Mock the directory creation
    with patch('pathlib.Path.mkdir'):
        result = run_nist_ingestion(output_dir=temp_dir)
    
    assert len(result) == 1
    mock_fetch.assert_called_once()
    mock_parse.assert_called_once()
    mock_extract.assert_called_once()

@patch('src.ingest.nist_repo.fetch_data')
def test_download_nist_data_no_data(mock_fetch, temp_dir):
    """Test flow when fetch fails."""
    mock_fetch.side_effect = SourceConnectionError("Connection failed")
    
    with patch('pathlib.Path.mkdir'):
        with pytest.raises(SourceConnectionError):
            run_nist_ingestion(output_dir=temp_dir)