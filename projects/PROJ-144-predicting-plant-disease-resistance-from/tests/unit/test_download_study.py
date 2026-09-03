"""
Unit tests for T012b: download_study.py
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import zipfile
import io

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.download_study import (
    get_study_download_url,
    download_study_data,
    extract_and_save_files,
    identify_phenotype_and_intensity_files,
    download_study,
    DataFetchError
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@patch('data.download_study.requests.get')
def test_get_study_download_url_success(mock_get):
    """Test successful URL retrieval."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"download_url": "https://example.com/download.zip"}
    mock_get.return_value = mock_response
    
    url = get_study_download_url("STUDY001")
    assert url == "https://example.com/download.zip"
    mock_get.assert_called_once()

@patch('data.download_study.requests.get')
def test_get_study_download_url_failure(mock_get):
    """Test URL retrieval failure."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    
    url = get_study_download_url("STUDY001")
    assert url is None

@patch('data.download_study.requests.get')
def test_download_study_data_success(mock_get, temp_dir):
    """Test successful data download."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = [b"fake zip content"]
    mock_get.return_value = mock_response
    
    result = download_study_data("https://example.com/download.zip", "STUDY001", temp_dir)
    
    assert 'zip' in result
    assert os.path.exists(result['zip'])
    assert os.path.getsize(result['zip']) > 0

@patch('data.download_study.requests.get')
def test_download_study_data_failure(mock_get, temp_dir):
    """Test download failure."""
    mock_get.side_effect = Exception("Network error")
    
    with pytest.raises(DataFetchError):
        download_study_data("https://example.com/download.zip", "STUDY001", temp_dir)

def test_extract_and_save_files(temp_dir):
    """Test extraction of files from a zip."""
    # Create a fake zip file
    zip_path = temp_dir / "test.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("phenotype_data.csv", "sample,metabolite,value\n1,M1,100\n")
        zf.writestr("intensity_data.csv", "sample,metabolite,value\n1,M1,50\n")
    
    saved_files = extract_and_save_files("STUDY001", str(zip_path), temp_dir)
    
    assert len(saved_files) == 2
    assert any("phenotype_data.csv" in f for f in saved_files)
    assert any("intensity_data.csv" in f for f in saved_files)

def test_identify_phenotype_and_intensity_files(temp_dir):
    """Test identification of file types."""
    # Create fake files
    phenotype_file = temp_dir / "phenotype_data.csv"
    intensity_file = temp_dir / "intensity_data.csv"
    other_file = temp_dir / "other.txt"
    
    phenotype_file.touch()
    intensity_file.touch()
    other_file.touch()
    
    files = [str(phenotype_file), str(intensity_file), str(other_file)]
    identified = identify_phenotype_and_intensity_files(files)
    
    assert identified['phenotype'] is not None
    assert identified['intensity'] is not None

@patch('data.download_study.get_study_download_url')
@patch('data.download_study.download_study_data')
@patch('data.download_study.extract_and_save_files')
@patch('data.download_study.identify_phenotype_and_intensity_files')
def test_download_study_full_flow(mock_identify, mock_extract, mock_download, mock_get_url, temp_dir):
    """Test the full download flow."""
    mock_get_url.return_value = "https://example.com/download.zip"
    mock_download.return_value = {"zip": str(temp_dir / "test.zip")}
    mock_extract.return_value = [str(temp_dir / "phenotype_data.csv"), str(temp_dir / "intensity_data.csv")]
    mock_identify.return_value = {
        'phenotype': str(temp_dir / "phenotype_data.csv"),
        'intensity': str(temp_dir / "intensity_data.csv")
    }
    
    result = download_study("STUDY001", temp_dir)
    
    assert 'phenotype' in result
    assert 'intensity' in result
    assert result['phenotype'] == str(temp_dir / "STUDY001_phenotype.csv")
    assert result['intensity'] == str(temp_dir / "STUDY001_raw_intensity.csv")

@patch('data.download_study.get_study_download_url')
def test_download_study_url_failure(mock_get_url, temp_dir):
    """Test download failure when URL retrieval fails."""
    mock_get_url.return_value = None
    
    with pytest.raises(DataFetchError):
        download_study("STUDY001", temp_dir)