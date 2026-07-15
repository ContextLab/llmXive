"""
Tests for the download module.
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
from download import (
    fetch_with_retry_rate_limit,
    fetch_materials_with_thermal_conductivity,
    fetch_cif_content,
    download_cif_files
)

@pytest.fixture
def mock_config():
    """Mock configuration with API key."""
    return {
        "mp_api_key": "test_api_key_12345"
    }

@patch('download.get_config')
@patch('download.requests.get')
def test_fetch_with_retry_rate_limit_success(mock_get, mock_config, mock_config_fixture):
    """Test successful fetch with retry logic."""
    mock_config.return_value = mock_config_fixture
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [{"material_id": "mp-123"}]}
    mock_get.return_value = mock_response
    
    result = fetch_with_retry_rate_limit("https://api.test.com/test")
    
    assert result is not None
    assert "data" in result
    assert mock_get.called

@patch('download.get_config')
@patch('download.requests.get')
def test_fetch_with_retry_rate_limit_429(mock_get, mock_config, mock_config_fixture):
    """Test rate limiting handling (429)."""
    mock_config.return_value = mock_config_fixture
    
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {"Retry-After": "1"}
    mock_get.return_value = mock_response
    
    result = fetch_with_retry_rate_limit("https://api.test.com/test")
    
    assert result is None
    assert mock_get.call_count > 1  # Should retry

@patch('download.get_config')
@patch('download.requests.get')
def test_fetch_with_retry_rate_limit_500(mock_get, mock_config, mock_config_fixture):
    """Test server error handling (500)."""
    mock_config.return_value = mock_config_fixture
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response
    
    result = fetch_with_retry_rate_limit("https://api.test.com/test")
    
    assert result is None
    assert mock_get.call_count > 1  # Should retry

@patch('download.get_config')
@patch('download.fetch_with_retry_rate_limit')
def test_fetch_materials_with_thermal_conductivity(mock_fetch, mock_config, mock_config_fixture):
    """Test fetching materials with thermal conductivity."""
    mock_config.return_value = mock_config_fixture
    
    mock_fetch.return_value = {
        "data": [
            {"material_id": "mp-123", "thermal_conductivity": 10.5},
            {"material_id": "mp-456", "thermal_conductivity": 5.2},
            {"material_id": "mp-789", "thermal_conductivity": None}  # Should be filtered
        ]
    }
    
    materials = fetch_materials_with_thermal_conductivity(limit=3)
    
    assert len(materials) == 2  # Only valid thermal conductivity values
    assert materials[0]["material_id"] == "mp-123"
    assert materials[1]["material_id"] == "mp-456"

@patch('download.get_config')
@patch('download.fetch_with_retry_rate_limit')
def test_fetch_cif_content(mock_fetch, mock_config, mock_config_fixture):
    """Test fetching CIF content."""
    mock_config.return_value = mock_config_fixture
    
    mock_fetch.return_value = {
        "cif": "data version 1.0\n_cell_length_a 5.0\n_cell_length_b 5.0\n_cell_length_c 5.0"
    }
    
    cif_content = fetch_cif_content("mp-123")
    
    assert cif_content is not None
    assert "data version" in cif_content

@patch('download.fetch_cif_content')
def test_download_cif_files(mock_fetch_cif):
    """Test downloading CIF files to disk."""
    mock_fetch_cif.return_value = "data version 1.0\n_cell_length_a 5.0"
    
    materials = [{"material_id": "mp-123"}]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        successful, failed = download_cif_files(materials, tmpdir, limit=1)
        
        assert successful == 1
        assert failed == 0
        
        # Check file was created
        filepath = Path(tmpdir) / "mp-123.cif"
        assert filepath.exists()
        
        with open(filepath, 'r') as f:
            content = f.read()
        assert "data version" in content

@patch('download.fetch_cif_content')
def test_download_cif_files_with_failures(mock_fetch_cif):
    """Test downloading CIF files with some failures."""
    mock_fetch_cif.side_effect = [
        "data version 1.0\n_cell_length_a 5.0",
        None  # This will fail
    ]
    
    materials = [
        {"material_id": "mp-123"},
        {"material_id": "mp-456"}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        successful, failed = download_cif_files(materials, tmpdir)
        
        assert successful == 1
        assert failed == 1
        
        # Only first file should exist
        assert Path(tmpdir) / "mp-123.cif" .exists()
        assert not (Path(tmpdir) / "mp-456.cif").exists()
