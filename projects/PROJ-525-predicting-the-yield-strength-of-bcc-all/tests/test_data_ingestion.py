"""
Unit tests for the data ingestion module.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import BytesIO

# Add code directory to path if running from tests
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from data_ingestion import download_mpea_database, MPEA_URL
from utils import PipelineError

@pytest.fixture
def temp_download_path(tmp_path):
    """Create a temporary directory for download tests."""
    return tmp_path / "mpea_raw.xlsx"

@patch('data_ingestion.requests.get')
def test_successful_download(mock_get, temp_download_path, tmp_path):
    """Test that a successful download saves the file correctly."""
    # Mock response
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"fake_excel_content"]
    mock_response.headers = {'content-length': '20'}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    # Mock compute_sha256 to avoid actual file hashing during test
    with patch('data_ingestion.compute_sha256', return_value="dummy_hash"):
        result = download_mpea_database(MPEA_URL, temp_download_path)

    assert result is True
    assert temp_download_path.exists()
    assert temp_download_path.read_bytes() == b"fake_excel_content"

@patch('data_ingestion.requests.get')
def test_download_network_error(mock_get, temp_download_path):
    """Test that network errors raise PipelineError."""
    import requests
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    with patch('data_ingestion.compute_sha256', return_value="dummy_hash"):
        with pytest.raises(PipelineError, match="Failed to download"):
            download_mpea_database(MPEA_URL, temp_download_path)

@patch('data_ingestion.requests.get')
def test_download_checksum_mismatch(mock_get, temp_download_path):
    """Test that checksum mismatch raises PipelineError."""
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"fake_excel_content"]
    mock_response.headers = {'content-length': '20'}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    # Mock compute_sha256 to return a mismatched hash
    with patch('data_ingestion.compute_sha256', return_value="wrong_hash"):
        with pytest.raises(PipelineError, match="checksum verification failed"):
            download_mpea_database(
                MPEA_URL, 
                temp_download_path, 
                expected_sha256="correct_hash"
            )
