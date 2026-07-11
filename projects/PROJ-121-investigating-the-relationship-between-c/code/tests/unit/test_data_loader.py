"""
Unit tests for data_loader module.
"""
import os
import tempfile
import hashlib
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
import pandas as pd

from src.data_loader import (
    calculate_sha256,
    download_file,
    load_icecube_data,
    load_auger_data,
    load_all_data,
    verify_local_checksum,
    DataDownloadError,
    ChecksumVerificationError
)

@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("test content")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.csv') as f:
        f.write("timestamp,ra,dec,energy,zenith,azimuth\n")
        f.write("2020-01-01 00:00:00,0.0,0.0,1e19,45.0,90.0\n")
        f.write("2020-01-02 00:00:00,180.0,0.0,2e19,60.0,270.0\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_calculate_sha256(temp_file):
    """Test SHA-256 calculation."""
    # Calculate expected hash
    expected = hashlib.sha256(b"test content").hexdigest()
    actual = calculate_sha256(temp_file)
    assert actual == expected

def test_calculate_sha256_file_not_found():
    """Test SHA-256 calculation with non-existent file."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256("/nonexistent/file.txt")

@patch('src.data_loader.requests.get')
def test_download_file_success(mock_get, temp_file):
    """Test successful file download."""
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"test content"]
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    success, msg = download_file(
        "http://example.com/file.txt",
        temp_file,
        expected_checksum=hashlib.sha256(b"test content").hexdigest()
    )

    assert success is True
    assert "Success" in msg
    assert os.path.exists(temp_file)

@patch('src.data_loader.requests.get')
def test_download_file_checksum_mismatch(mock_get, temp_file):
    """Test download with checksum mismatch."""
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"wrong content"]
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    success, msg = download_file(
        "http://example.com/file.txt",
        temp_file,
        expected_checksum=hashlib.sha256(b"correct content").hexdigest()
    )

    assert success is False
    assert "Checksum mismatch" in msg
    assert not os.path.exists(temp_file)  # File should be deleted on mismatch

@patch('src.data_loader.requests.get')
def test_download_file_network_error(mock_get, temp_file):
    """Test download with network error."""
    import requests
    mock_get.side_effect = requests.exceptions.RequestException("Network error")

    success, msg = download_file(
        "http://example.com/file.txt",
        temp_file,
        retries=1
    )

    assert success is False
    assert "Download failed" in msg

@patch('src.data_loader.download_file')
@patch('src.data_loader.Path.exists')
@patch('src.data_loader.pd.read_csv')
def test_load_icecube_data(mock_read_csv, mock_exists, mock_download, temp_csv_file):
    """Test IceCube data loading."""
    mock_exists.return_value = True
    mock_read_csv.return_value = pd.read_csv(temp_csv_file)

    dataset = load_icecube_data(2020, 2020, output_dir=os.path.dirname(temp_csv_file))

    assert dataset.source == "IceCube"
    assert len(dataset.data) == 2
    assert dataset.metadata["record_count"] == 2

@patch('src.data_loader.download_file')
@patch('src.data_loader.Path.exists')
@patch('src.data_loader.pd.read_csv')
def test_load_auger_data(mock_read_csv, mock_exists, mock_download, temp_csv_file):
    """Test Auger data loading."""
    mock_exists.return_value = True
    mock_read_csv.return_value = pd.read_csv(temp_csv_file)

    dataset = load_auger_data(2020, 2020, output_dir=os.path.dirname(temp_csv_file))

    assert dataset.source == "Auger"
    assert len(dataset.data) == 2
    assert dataset.metadata["record_count"] == 2

@patch('src.data_loader.load_icecube_data')
@patch('src.data_loader.load_auger_data')
def test_load_all_data(mock_auger, mock_icecube, temp_csv_file):
    """Test loading all data sources."""
    # Mock datasets
    icecube_ds = MagicMock()
    icecube_ds.source = "IceCube"
    icecube_ds.data = pd.read_csv(temp_csv_file)

    auger_ds = MagicMock()
    auger_ds.source = "Auger"
    auger_ds.data = pd.read_csv(temp_csv_file)

    mock_icecube.return_value = icecube_ds
    mock_auger.return_value = auger_ds

    datasets = load_all_data(2020, 2020)

    assert len(datasets) == 2
    assert datasets[0].source == "IceCube"
    assert datasets[1].source == "Auger"

@patch('src.data_loader.load_icecube_data')
def test_load_all_data_icecube_fails(mock_icecube, temp_csv_file):
    """Test load_all_data when IceCube fails but Auger succeeds."""
    mock_icecube.side_effect = DataDownloadError("IceCube failed")

    auger_ds = MagicMock()
    auger_ds.source = "Auger"
    auger_ds.data = pd.read_csv(temp_csv_file)

    with patch('src.data_loader.load_auger_data', return_value=auger_ds):
        datasets = load_all_data(2020, 2020)

    assert len(datasets) == 1
    assert datasets[0].source == "Auger"

@patch('src.data_loader.load_icecube_data')
@patch('src.data_loader.load_auger_data')
def test_load_all_data_both_fail(mock_auger, mock_icecube):
    """Test load_all_data when both sources fail."""
    mock_icecube.side_effect = DataDownloadError("IceCube failed")
    mock_auger.side_effect = DataDownloadError("Auger failed")

    with pytest.raises(DataDownloadError):
        load_all_data(2020, 2020)

def test_verify_local_checksum(temp_file):
    """Test local checksum verification."""
    expected = hashlib.sha256(b"test content").hexdigest()
    assert verify_local_checksum(temp_file, expected) is True
    assert verify_local_checksum(temp_file, "wrong_hash") is False
