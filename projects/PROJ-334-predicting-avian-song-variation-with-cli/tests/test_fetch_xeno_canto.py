import os
import csv
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

# Import the module under test
# Note: We assume the tests are run with the project root in sys.path
# or the module is installed in editable mode.
from fetch_xeno_canto import (
    fetch_xeno_canto_data, 
    write_to_csv, 
    calculate_sha256, 
    fetch_page
)

@pytest.fixture
def temp_csv_path():
    """Create a temporary CSV file path for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def mock_api_response():
    """Mock response data for Xeno-Canto API."""
    return {
        "recordings": [
            {"sp": "Turdus merula", "lat": "51.5", "lon": "-0.1", "id": "1"},
            {"sp": "Accipiter nisus", "lat": "48.8", "lon": "2.3", "id": "2"},
            {"sp": "Pica pica", "lat": "52.0", "lon": "0.1", "id": "3"},
            {"sp": "Corvus corone", "lat": "invalid", "lon": "1.0", "id": "4"}, # Invalid lat
            {"sp": None, "lat": "50.0", "lon": "1.0", "id": "5"}, # No species
        ]
    }

def test_fetch_page_success(mock_api_response):
    """Test that fetch_page returns the correct JSON structure."""
    with patch('fetch_xeno_canto.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_page(page=1, limit=10)
        
        assert result is not None
        assert 'recordings' in result
        assert len(result['recordings']) == 5

def test_fetch_page_failure():
    """Test that fetch_page returns None on request failure."""
    with patch('fetch_xeno_canto.requests.get') as mock_get:
        mock_get.side_effect = Exception("Network error")
        
        result = fetch_page(page=1, limit=10)
        assert result is None

def test_fetch_xeno_canto_data_filters_invalid(mock_api_response):
    """Test that fetch_xeno_canto_data filters out invalid records."""
    with patch('fetch_xeno_canto.fetch_page') as mock_fetch:
        # Simulate one page fetch
        mock_fetch.return_value = mock_api_response
        
        records = fetch_xeno_canto_data(limit=100)
        
        # Should have 3 valid records (indices 0, 1, 2)
        # Index 3 has invalid lat, Index 4 has no species
        assert len(records) == 3
        
        # Check species_id
        species_ids = [r['species_id'] for r in records]
        assert 'Turdus merula' in species_ids
        assert 'Accipiter nisus' in species_ids
        assert 'Pica pica' in species_ids

def test_write_to_csv(temp_csv_path):
    """Test that write_to_csv creates a valid CSV file."""
    data = [
        {'species_id': 'Species A', 'lat': 1.0, 'lon': 2.0},
        {'species_id': 'Species B', 'lat': 3.0, 'lon': 4.0}
    ]
    
    write_to_csv(data, temp_csv_path)
    
    assert os.path.exists(temp_csv_path)
    
    with open(temp_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 2
    assert rows[0]['species_id'] == 'Species A'
    assert rows[0]['lat'] == '1.0'
    assert rows[0]['lon'] == '2.0'

def test_calculate_sha256(temp_csv_path):
    """Test SHA256 calculation."""
    with open(temp_csv_path, 'w') as f:
        f.write("test content")
    
    hash1 = calculate_sha256(temp_csv_path)
    hash2 = calculate_sha256(temp_csv_path)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length
    
    # Change content and verify hash changes
    with open(temp_csv_path, 'w') as f:
        f.write("different content")
    
    hash3 = calculate_sha256(temp_csv_path)
    assert hash1 != hash3

def test_fetch_xeno_canto_data_empty_response():
    """Test handling of empty API response."""
    with patch('fetch_xeno_canto.fetch_page') as mock_fetch:
        mock_fetch.return_value = {"recordings": []}
        
        with pytest.raises(RuntimeError, match="Failed to fetch any valid records"):
            fetch_xeno_canto_data(limit=10)

def test_fetch_xeno_canto_data_no_valid_records(mock_api_response):
    """Test handling of response with no valid records (all filtered)."""
    bad_response = {
        "recordings": [
            {"sp": None, "lat": "invalid", "lon": "1.0"},
            {"sp": "Species", "lat": "invalid", "lon": "1.0"}
        ]
    }
    with patch('fetch_xeno_canto.fetch_page') as mock_fetch:
        mock_fetch.return_value = bad_response
        
        with pytest.raises(RuntimeError, match="Failed to fetch any valid records"):
            fetch_xeno_canto_data(limit=10)