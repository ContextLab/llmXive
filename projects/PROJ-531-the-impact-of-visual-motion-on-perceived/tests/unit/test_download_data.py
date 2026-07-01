import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test
from code.data.download_data import download_data, check_dataset_validity

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    return str(tmp_path)

def test_check_dataset_validity_with_doi():
    """Test that a dataset with a DOI is considered valid."""
    dataset_info = {"id": "123", "doi": "10.1234/fake.doi"}
    assert check_dataset_validity(dataset_info) is True

def test_check_dataset_validity_with_citation():
    """Test that a dataset with a citation is considered valid."""
    dataset_info = {"id": "123", "citation": "Smith et al., 2023"}
    assert check_dataset_validity(dataset_info) is True

def test_check_dataset_validity_without_metadata():
    """Test that a dataset without DOI or citation is invalid."""
    dataset_info = {"id": "123", "name": "Fake Dataset"}
    assert check_dataset_validity(dataset_info) is False

@patch('code.data.download_data.requests.get')
@patch('code.data.download_data.requests.head')
def test_download_data_success(mock_head, mock_get, temp_output_dir):
    """Test successful download status generation."""
    # Mock the GET request to return a valid dataset
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.json.return_value = [
        {
            "id": "fake-dataset-id",
            "name": "Fake Dataset",
            "doi": "10.1234/fake",
            "source": "huggingface"
        }
    ]
    mock_get.return_value = mock_response_get

    # Mock the HEAD request to return 200
    mock_response_head = MagicMock()
    mock_response_head.status_code = 200
    mock_response_head.headers = {"content-length": "1024"}
    mock_head.return_value = mock_response_head

    # Run the function
    result = download_data(output_dir=temp_output_dir)

    # Assertions
    assert result["status"] == "success"
    assert result["dataset_id"] == "fake-dataset-id"
    assert result["validity_check"] == "passed"
    
    # Check that the file was written
    status_file = Path(temp_output_dir) / "download_status.json"
    assert status_file.exists()
    
    with open(status_file) as f:
        saved_status = json.load(f)
    assert saved_status["status"] == "success"

@patch('code.data.download_data.requests.get')
def test_download_data_no_valid_dataset(mock_get, temp_output_dir):
    """Test that the function exits with code 1 if no valid dataset is found."""
    # Mock the GET request to return an empty list or invalid dataset
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.json.return_value = [
        {"id": "bad-dataset", "name": "No Metadata"} # No DOI or citation
    ]
    mock_get.return_value = mock_response_get

    # Expect SystemExit
    with pytest.raises(SystemExit) as excinfo:
        download_data(output_dir=temp_output_dir)
    
    assert excinfo.value.code == 1

@patch('code.data.download_data.requests.get')
def test_download_data_api_failure(mock_get, temp_output_dir):
    """Test behavior when API request fails."""
    mock_get.side_effect = Exception("Network error")

    with pytest.raises(SystemExit) as excinfo:
        download_data(output_dir=temp_output_dir)
    
    assert excinfo.value.code == 1