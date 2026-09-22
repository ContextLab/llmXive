import os
import sys
import csv
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path for imports if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetch_xeno_canto import (
    fetch_xeno_canto_data,
    extract_metadata,
    save_to_csv,
    calculate_sha256,
    update_checksums_file,
    main
)
from config import Config

@pytest.fixture
def mock_api_response():
    return {
        "numRecordings": 2,
        "numPages": 1,
        "recordings": [
            {
                "id": "654321",
                "species": "XC12345",
                "sp": "Robin",
                "lat": "51.5074",
                "lon": "-0.1278",
                "file": "https://example.com/rec1.mp3",
                "dur": "10.5",
                "freq": "2000",
                "date": "2023-05-01",
                "cnt": "UK",
                "loc": "London"
            },
            {
                "id": "654322",
                "species": "XC67890",
                "sp": "Eagle",
                "lat": "40.7128",
                "lon": "-74.0060",
                "file": "https://example.com/rec2.mp3",
                "dur": "15.2",
                "freq": "1500",
                "date": "2023-06-01",
                "cnt": "USA",
                "loc": "New York"
            }
        ]
    }

@pytest.fixture
def mock_api_response_missing_coords():
    return {
        "numRecordings": 2,
        "numRecordings": 2,
        "recordings": [
            {
                "id": "654323",
                "species": "XC11111",
                "sp": "Bad Bird",
                "lat": "", # Missing lat
                "lon": "-74.0060",
                "file": "https://example.com/rec3.mp3",
                "dur": "10.0",
                "freq": "1000",
                "date": "2023-01-01",
                "cnt": "USA",
                "loc": "Test"
            },
            {
                "id": "654324",
                "species": "XC22222",
                "sp": "Good Bird",
                "lat": "34.0522",
                "lon": "-118.2437",
                "file": "https://example.com/rec4.mp3",
                "dur": "12.0",
                "freq": "1200",
                "date": "2023-02-01",
                "cnt": "USA",
                "loc": "LA"
            }
        ]
    }

def test_fetch_xeno_canto_data_success(mock_api_response):
    with patch('fetch_xeno_canto.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_xeno_canto_data(limit=10)
        
        assert len(result) == 2
        assert result[0]["species"] == "XC12345"
        mock_get.assert_called_once()

def test_fetch_xeno_canto_data_timeout():
    with patch('fetch_xeno_canto.requests.get') as mock_get:
        mock_get.side_effect = Exception("Timeout") # Simulating a generic exception that raises
        
        with pytest.raises(Exception):
            fetch_xeno_canto_data()

def test_extract_metadata_valid(mock_api_response):
    records = mock_api_response["recordings"]
    result = extract_metadata(records)
    
    assert len(result) == 2
    assert result[0]["species_id"] == "XC12345"
    assert result[0]["lat"] == 51.5074
    assert result[0]["lon"] == -0.1278
    assert result[0]["duration_sec"] == 10.5

def test_extract_metadata_invalid_coords(mock_api_response_missing_coords):
    records = mock_api_response_missing_coords["recordings"]
    result = extract_metadata(records)
    
    # Should filter out the one with missing lat
    assert len(result) == 1
    assert result[0]["species_id"] == "XC22222"

def test_extract_metadata_missing_species():
    records = [
        {
            "id": "123",
            "species": "", # Missing species
            "lat": "1.0",
            "lon": "1.0",
            "file": "url",
            "dur": "1.0",
            "freq": "1.0"
        }
    ]
    result = extract_metadata(records)
    assert len(result) == 0

def test_save_to_csv(tmp_path):
    data = [
        {"species_id": "XC1", "lat": 1.0, "lon": 2.0},
        {"species_id": "XC2", "lat": 3.0, "lon": 4.0}
    ]
    output_file = tmp_path / "test.csv"
    
    save_to_csv(data, output_file)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["species_id"] == "XC1"

def test_calculate_sha256(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello World")
    
    checksum = calculate_sha256(file_path)
    expected = hashlib.sha256(b"Hello World").hexdigest()
    
    assert checksum == expected

def test_update_checksums_file(tmp_path):
    # Setup
    checksums_file = tmp_path / "checksums.txt"
    checksums_file.write_text("existing_file.txt  abc123\n")
    
    new_file = tmp_path / "new_file.csv"
    new_file.write_text("data")
    checksum = "def456"
    
    # Mock config
    config = Config()
    # Override checksums file path for test
    config._checksums_file = str(checksums_file)
    
    update_checksums_file(str(new_file), checksum, config)
    
    content = checksums_file.read_text()
    assert "new_file.csv" in content
    assert "def456" in content

@patch('fetch_xeno_canto.fetch_xeno_canto_data')
@patch('fetch_xeno_canto.extract_metadata')
@patch('fetch_xeno_canto.save_to_csv')
@patch('fetch_xeno_canto.calculate_sha256')
@patch('fetch_xeno_canto.update_checksums_file')
@patch('fetch_xeno_canto.ensure_directory')
@patch('fetch_xeno_canto.initialize_checksums_file')
def test_main_success(
    mock_init_checksums, mock_ensure_dir, mock_update, mock_calc, mock_save, mock_extract, mock_fetch, tmp_path
):
    # Setup mocks
    mock_fetch.return_value = [{"id": "1", "species": "XC1", "lat": "1.0", "lon": "1.0", "file": "u", "dur": "1", "freq": "1"}]
    mock_extract.return_value = [{"species_id": "XC1", "lat": 1.0, "lon": 1.0}]
    mock_calc.return_value = "abc123"
    
    # Mock Config to use tmp_path
    with patch('fetch_xeno_canto.Config') as MockConfig:
        mock_config = MagicMock()
        mock_config.RAW_DATA_DIR = tmp_path
        mock_config.CHECKSUMS_FILE = str(tmp_path / "checksums.txt")
        MockConfig.return_value = mock_config
        
        # Run main
        main()
        
        mock_fetch.assert_called_once()
        mock_extract.assert_called_once()
        mock_save.assert_called_once()
        mock_calc.assert_called_once()
        mock_update.assert_called_once()
        mock_init_checksums.assert_called_once()

@patch('fetch_xeno_canto.fetch_xeno_canto_data')
def test_main_fetch_failure(mock_fetch):
    mock_fetch.side_effect = Exception("Network Error")
    
    with patch('fetch_xeno_canto.Config') as MockConfig:
        mock_config = MagicMock()
        MockConfig.return_value = mock_config
        
        # Should raise SystemExit
        with pytest.raises(SystemExit):
            main()