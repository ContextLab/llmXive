"""
Unit tests for zenodo_client.py
"""
import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests

# Import the module under test
from zenodo_client import (
    fetch_from_zenodo, 
    fetch_dataset, 
    DataUnavailableError, 
    DataInsufficientError
)

@patch('zenodo_client.requests.get')
def test_fetch_from_zenodo_success(mock_get, tmp_path):
    """Test successful fetch from Zenodo."""
    # Mock the record metadata response
    mock_record_response = MagicMock()
    mock_record_response.status_code = 200
    mock_record_response.json.return_value = {
        'files': [
            {
                'key': 'data.csv',
                'links': {'self': 'http://zenodo.org/files/123'}
            }
        ]
    }
    
    # Mock the file download response
    mock_file_response = MagicMock()
    mock_file_response.status_code = 200
    mock_file_response.iter_content.return_value = [b"col1,col2\n1,2\n"]
    
    # Sequence of calls: first to metadata, second to file
    mock_get.side_effect = [mock_record_response, mock_file_response]
    
    output_path = tmp_path / "test.csv"
    
    result = fetch_from_zenodo("10.5281/zenodo.123", output_path, max_retries=1)
    
    assert result is True
    assert output_path.exists()
    assert mock_get.call_count == 2

@patch('zenodo_client.requests.get')
def test_fetch_from_zenodo_404(mock_get, tmp_path):
    """Test 404 error handling."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    
    output_path = tmp_path / "test.csv"
    
    with pytest.raises(DataUnavailableError) as exc_info:
        fetch_from_zenodo("10.5281/zenodo.999", output_path, max_retries=0)
    
    assert "404" in str(exc_info.value)

@patch('zenodo_client.requests.get')
def test_fetch_from_zenodo_rate_limit(mock_get, tmp_path):
    """Test rate limit (429) and retry logic."""
    # First call: 429, Second call: 200
    mock_429 = MagicMock()
    mock_429.status_code = 429
    
    mock_200_record = MagicMock()
    mock_200_record.status_code = 200
    mock_200_record.json.return_value = {
        'files': [{'key': 'data.csv', 'links': {'self': 'http://file'}}]
    }
    
    mock_200_file = MagicMock()
    mock_200_file.status_code = 200
    mock_200_file.iter_content.return_value = [b"test"]
    
    mock_get.side_effect = [mock_429, mock_200_record, mock_200_file]
    
    output_path = tmp_path / "test.csv"
    
    # Should succeed on second attempt
    result = fetch_from_zenodo("10.5281/zenodo.123", output_path, max_retries=2, initial_delay=0.01)
    
    assert result is True
    assert mock_get.call_count == 3

@patch('zenodo_client.requests.get')
def test_data_unavailable_error_both_fail(mock_get, tmp_path):
    """Test that DataUnavailableError is raised when both DOIs fail."""
    # Mock 404 for both calls
    mock_404 = MagicMock()
    mock_404.status_code = 404
    mock_get.return_value = mock_404
    
    output_dir = tmp_path / "raw"
    
    with pytest.raises(DataUnavailableError) as exc_info:
        fetch_dataset(
            primary_doi="10.5281/zenodo.10043838",
            fallback_doi="10.5281/zenodo.11023456",
            output_dir=output_dir
        )
    
    assert "Both primary" in str(exc_info.value)
    assert "10043838" in str(exc_info.value)
    assert "11023456" in str(exc_info.value)

@patch('zenodo_client.fetch_from_zenodo')
def test_fetch_dataset_fallback_used(mock_fetch, tmp_path):
    """Test that fallback DOI is used if primary fails."""
    # Primary fails, Fallback succeeds
    mock_fetch.side_effect = [
        False, # Primary returns False
        True   # Fallback returns True
    ]
    
    output_dir = tmp_path / "raw"
    path, doi = fetch_dataset(
        primary_doi="10.5281/zenodo.10043838",
        fallback_doi="10.5281/zenodo.11023456",
        output_dir=output_dir
    )
    
    assert doi == "10.5281/zenodo.11023456"
    assert mock_fetch.call_count == 2
