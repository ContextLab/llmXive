"""
Unit tests for Web of Life ingestion module.
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import json
import os
import tempfile
import shutil

from ingestion import download_web_of_life_ecosystem, WebOfLifeDownloader, load_interactions_csv
from config import get_data_raw

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@patch('ingestion._fetch_ecosystem_info')
@patch('ingestion.requests.get')
def test_download_success(mock_get, mock_fetch, temp_data_dir):
    """Test successful download of an ecosystem."""
    # Mock ecosystem info
    mock_fetch.return_value = {
        "ecosystem_id": "F1000001",
        "name": "Tropical Rainforest",
        "has_traits": True,
        "data_url": "http://example.com/data.csv"
    }
    
    # Mock response
    mock_response = MagicMock()
    mock_response.content = b"plant,pollinator\nA,B\nC,D"
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    success = download_web_of_life_ecosystem("F1000001", raw_dir=temp_data_dir)
    
    assert success is True
    assert (temp_data_dir / "F1000001" / "interactions.csv").exists()
    assert (temp_data_dir / "F1000001" / "metadata.json").exists()

@patch('ingestion._fetch_ecosystem_info')
def test_download_no_traits(mock_fetch, temp_data_dir):
    """Test download skips ecosystem with no trait data."""
    mock_fetch.return_value = None
    
    success = download_web_of_life_ecosystem("F9999999", raw_dir=temp_data_dir)
    
    assert success is False
    assert not (temp_data_dir / "F9999999").exists()

@patch('ingestion._fetch_ecosystem_info')
@patch('ingestion.requests.get')
def test_download_timeout(mock_get, mock_fetch, temp_data_dir):
    """Test download handles timeout."""
    import requests
    
    mock_fetch.return_value = {
        "ecosystem_id": "F1000001",
        "name": "Tropical Rainforest",
        "has_traits": True,
        "data_url": "http://example.com/data.csv"
    }
    
    mock_get.side_effect = requests.exceptions.Timeout()
    
    success = download_web_of_life_ecosystem("F1000001", raw_dir=temp_data_dir)
    
    assert success is False

@patch('ingestion._fetch_ecosystem_info')
@patch('ingestion.requests.get')
def test_download_empty_file(mock_get, mock_fetch, temp_data_dir):
    """Test download handles empty file."""
    import requests
    
    mock_fetch.return_value = {
        "ecosystem_id": "F1000001",
        "name": "Tropical Rainforest",
        "has_traits": True,
        "data_url": "http://example.com/data.csv"
    }
    
    mock_response = MagicMock()
    mock_response.content = b""
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    success = download_web_of_life_ecosystem("F1000001", raw_dir=temp_data_dir)
    
    assert success is False
    assert not (temp_data_dir / "F1000001" / "interactions.csv").exists()

def test_web_of_life_downloader_valid_count(temp_data_dir):
    """Test WebOfLifeDownloader returns correct valid count."""
    downloader = WebOfLifeDownloader(raw_dir=temp_data_dir)
    # Manually set a known ecosystem ID for testing
    downloader.ecosystem_ids = ["F1000001"]
    
    # We can't easily mock the internal fetch logic without more patching,
    # so we test the state management
    downloader.downloaded_count = 3
    downloader.failed_count = 2
    
    assert downloader.get_valid_count() == 3
    assert downloader.get_failed_count() == 2

@patch('builtins.open', new_callable=mock_open, read_data="plant,pollinator\nA,B\nC,D")
def test_load_interactions_csv(mock_file):
    """Test loading interactions from CSV."""
    result = load_interactions_csv(Path("dummy.csv"))
    
    assert len(result) == 2
    assert result[0] == {"plant": "A", "pollinator": "B"}
    assert result[1] == {"plant": "C", "pollinator": "D"}