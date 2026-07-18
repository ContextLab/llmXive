"""
Unit tests for NIST Repository Downloader (T013).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

import pandas as pd
import requests

from src.ingest.nist_repo import (
    calculate_sha256,
    validate_checksum,
    fetch_data,
    parse_csv,
    extract_psd_metrics,
    run_nist_ingestion,
    DataIngestionError,
    SourceConnectionError,
    DataFormatError
)
from src.config.env_config import get_config

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def mock_csv_content():
    return """experiment_id,source,material_type,milling_speed,milling_time,ball_to_powder_ratio,youngs_modulus,density,d10,d50,d90,process_duration
    NIST-001,NIST,Ceramic,500,60,2.0,150.0,2.5,1.2,5.5,12.3,60.0
    NIST-002,NIST,Metal,600,90,3.0,200.0,7.8,2.1,8.2,18.5,90.0
    """

@pytest.fixture
def mock_csv_path(temp_dir, mock_csv_content):
    path = temp_dir / "test_data.csv"
    path.write_text(mock_csv_content)
    return path

def test_calculate_sha256(temp_dir):
    test_file = temp_dir / "test.txt"
    test_file.write_text("hello world")
    hash_val = calculate_sha256(test_file)
    assert len(hash_val) == 64  # SHA256 hex length
    assert isinstance(hash_val, str)

def test_validate_checksum_success(temp_dir, mock_csv_path):
    # Calculate real checksum
    real_checksum = calculate_sha256(mock_csv_path)
    assert validate_checksum(mock_csv_path, expected_checksum=real_checksum) is True

def test_validate_checksum_mismatch(temp_dir, mock_csv_path):
    with pytest.raises(DataIngestionError, match="Checksum mismatch"):
        validate_checksum(mock_csv_path, expected_checksum="wrong_checksum")

@patch('src.ingest.nist_repo.requests.get')
def test_fetch_data_success(mock_get, temp_dir):
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"mock data"]
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    url = "http://example.com/data.csv"
    output_path = temp_dir / "data.csv"

    result = fetch_data(url, output_path)

    assert result.exists()
    assert result.read_bytes() == b"mock data"
    mock_get.assert_called_once_with(url, timeout=30, stream=True)

@patch('src.ingest.nist_repo.requests.get')
def test_fetch_data_404(mock_get, temp_dir):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
    mock_get.return_value = mock_response

    url = "http://example.com/missing.csv"
    output_path = temp_dir / "missing.csv"

    with pytest.raises(SourceConnectionError):
        fetch_data(url, output_path)

def test_parse_csv(mock_csv_path):
    df = parse_csv(mock_csv_path)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert 'experiment_id' in df.columns

def test_extract_psd_metrics():
    data = {
        'experiment_id': ['1'],
        'source': ['NIST'],
        'material_type': ['Ceramic'],
        'milling_speed': [500],
        'milling_time': [60],
        'ball_to_powder_ratio': [2.0],
        'youngs_modulus': [150.0],
        'density': [2.5],
        'd10': [1.2],
        'd50': [5.5],
        'd90': [12.3],
        'process_duration': [60.0]
    }
    df = pd.DataFrame(data)
    result = extract_psd_metrics(df)
    assert 'd10' in result.columns
    assert 'd50' in result.columns
    assert 'd90' in result.columns
    assert result['source'].iloc[0] == 'NIST'

def test_extract_psd_metrics_missing_cols():
    data = {
        'experiment_id': ['1'],
        'source': ['NIST'],
        'material_type': ['Ceramic'],
        'milling_speed': [500],
        'milling_time': [60],
        'ball_to_powder_ratio': [2.0],
        'youngs_modulus': [150.0],
        'density': [2.5],
        # Missing d10, d50, d90
    }
    df = pd.DataFrame(data)
    with pytest.raises(DataFormatError, match="Missing required PSD metrics columns"):
        extract_psd_metrics(df)

@patch('src.ingest.nist_repo.fetch_data')
@patch('src.ingest.nist_repo.validate_checksum')
@patch('src.ingest.nist_repo.parse_csv')
@patch('src.ingest.nist_repo.extract_psd_metrics')
@patch('src.ingest.nist_repo.get_config')
def test_download_nist_data_full_flow(
    mock_get_config, mock_extract, mock_parse, mock_validate, mock_fetch, temp_dir
):
    mock_config = {'nist': {'url': 'http://example.com/data.csv'}}
    mock_get_config.return_value = mock_config

    mock_fetch.return_value = temp_dir / "data.csv"
    mock_parse.return_value = pd.DataFrame({'col': [1]})
    mock_extract.return_value = pd.DataFrame({'d10': [1], 'd50': [2], 'd90': [3], 'source': ['NIST']})

    result = run_nist_ingestion(output_dir=temp_dir)

    assert isinstance(result, pd.DataFrame)
    assert mock_fetch.called
    assert mock_validate.called
    assert mock_parse.called
    assert mock_extract.called

@patch('src.ingest.nist_repo.get_config')
def test_download_nist_data_no_data(mock_get_config):
    mock_get_config.return_value = {'nist': {}} # No URL

    with pytest.raises(DataIngestionError, match="NIST URL not configured"):
        run_nist_ingestion()