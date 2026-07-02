"""
Tests for data download module.

Tests cover:
- Fallback to synthetic generation when real data unavailable
- Proper manifest updates for both REAL and SIMULATED modes
- Error handling for network failures
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Mock the config and manifest modules
@pytest.fixture
def mock_config():
    with patch('data.download.get_path') as mock_get_path, \
         patch('data.download.load_config') as mock_load_config:
        mock_get_path.return_value = Path("/tmp/test_project")
        mock_load_config.return_value = {}
        yield mock_get_path

@pytest.fixture
def mock_manifest():
    with patch('data.download.load_manifest') as mock_load, \
         patch('data.download.get_manifest_source_type') as mock_get_type:
        mock_load.return_value = {
            "version": "1.0",
            "source_type": None,
            "accessions": [],
            "data_type": "both"
        }
        mock_get_type.return_value = None
        yield mock_load, mock_get_type

@pytest.fixture
def mock_synthetic():
    with patch('data.download.generate_synthetic_data') as mock_gen:
        mock_gen.return_value = "/tmp/test_project/data/processed/synthetic_data.csv"
        yield mock_gen

@pytest.fixture
def mock_requests():
    with patch('data.download.requests.get') as mock_get:
        # Simulate 404 for all requests
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        yield mock_get

def test_fallback_to_synthetic(mock_config, mock_manifest, mock_synthetic, mock_requests, tmp_path):
    """Test that synthetic generation is triggered when real data is unavailable."""
    # Setup temporary directory structure
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    
    with patch('data.download.get_path', return_value=tmp_path):
        from data.download import download_or_generate
        
        source_type, manifest_path = download_or_generate()
        
        assert source_type == "SIMULATED"
        assert os.path.exists(manifest_path)
        mock_synthetic.assert_called_once()

def test_real_data_success(mock_config, mock_manifest, mock_requests, tmp_path):
    """Test successful real data fetch."""
    # Setup temporary directory structure
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests.return_value = mock_response
    
    with patch('data.download.get_path', return_value=tmp_path):
        from data.download import download_or_generate
        
        source_type, manifest_path = download_or_generate()
        
        assert source_type == "REAL"
        assert os.path.exists(manifest_path)

def test_manifest_updated_for_simulated(mock_config, mock_manifest, mock_synthetic, mock_requests, tmp_path):
    """Test that manifest is properly updated for simulated mode."""
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    
    with patch('data.download.get_path', return_value=tmp_path):
        from data.download import download_or_generate
        
        source_type, manifest_path = download_or_generate()
        
        # Check manifest content
        import yaml
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        assert manifest["source_type"] == "SIMULATED"
        assert "simulation_note" in manifest