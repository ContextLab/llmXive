import os
import pytest
import json
from unittest.mock import patch, MagicMock
from code.ingest import fetch_kp_indices, validate_kp_schema, write_kp_data

@pytest.fixture
def mock_kp_response():
    """Mock response data for Kp indices."""
    return [
        {
            "time_tag": "2023-01-01 00:00:00",
            "kp_index": 2.33,
            "ap_index": 7,
            "date": "2023-01-01",
            "time": "00:00"
        },
        {
            "time_tag": "2023-01-01 03:00:00",
            "kp_index": 1.67,
            "ap_index": 4,
            "date": "2023-01-01",
            "time": "03:00"
        }
    ]

@patch('code.ingest.requests.get')
def test_fetch_kp_indices_success(mock_get, mock_kp_response):
    """Test successful fetch of Kp indices."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_kp_response
    mock_get.return_value = mock_response

    result = fetch_kp_indices()

    assert len(result) == 2
    assert result[0]['kp_index'] == 2.33
    mock_get.assert_called_once()

@patch('code.ingest.requests.get')
def test_fetch_kp_indices_empty_list(mock_get):
    """Test fetch with empty list response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_get.return_value = mock_response

    result = fetch_kp_indices()
    assert result == []

@patch('code.ingest.requests.get')
def test_fetch_kp_indices_request_error(mock_get):
    """Test fetch handles network errors."""
    mock_get.side_effect = Exception("Network error")

    with pytest.raises(RuntimeError):
        fetch_kp_indices()

def test_validate_kp_schema_valid(mock_kp_response):
    """Test validation of valid Kp data."""
    assert validate_kp_schema(mock_kp_response) is True

def test_validate_kp_schema_missing_field(mock_kp_response):
    """Test validation fails with missing required field."""
    invalid_data = [mock_kp_response[0].copy()]
    del invalid_data[0]['kp_index']
    
    assert validate_kp_schema(invalid_data) is False

def test_validate_kp_schema_empty_list():
    """Test validation fails with empty data."""
    assert validate_kp_schema([]) is False

def test_validate_kp_schema_invalid_type(mock_kp_response):
    """Test validation fails with invalid types."""
    invalid_data = [mock_kp_response[0].copy()]
    invalid_data[0]['kp_index'] = "not_a_number"
    
    assert validate_kp_schema(invalid_data) is False

@patch('code.ingest.ensure_directories')
@patch('code.ingest.open', new_callable=MagicMock)
def test_write_kp_data(mock_open, mock_ensure, mock_kp_response, tmp_path):
    """Test writing Kp data to CSV."""
    # Setup mock file
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file

    output_path = str(tmp_path / "kp_indices.csv")
    write_kp_data(mock_kp_response, output_path)

    # Verify file operations
    mock_open.assert_called_once()
    # Check that writeheader and writerow were called
    writer = mock_open.return_value.__enter__.return_value
    assert writer.writeheader.called
    assert writer.writerow.called
