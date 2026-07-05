import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

# Import the module under test
import code.download as download_module
from code.config import reset_config

@pytest.fixture(autouse=True)
def setup_env():
    """Ensure a clean config state for each test."""
    reset_config()
    yield
    reset_config()

def test_fetch_with_retry_rate_limit_success():
    """Test that a successful request returns data immediately."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [{"material_id": "mp-123", "kappa": 10.5}]}
    
    with patch('code.download.requests.get', return_value=mock_response) as mock_get:
        result = download_module.fetch_with_retry_rate_limit("http://test.com")
        assert result == {"data": [{"material_id": "mp-123", "kappa": 10.5}]}
        mock_get.assert_called_once()

def test_fetch_with_retry_rate_limit_429():
    """Test that 429 triggers a retry with backoff."""
    mock_429 = MagicMock()
    mock_429.status_code = 429
    
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"data": []}
    
    # First call returns 429, second returns 200
    with patch('code.download.requests.get', side_effect=[mock_429, mock_200]) as mock_get:
        with patch('code.download.time.sleep') as mock_sleep:
            result = download_module.fetch_with_retry_rate_limit("http://test.com")
            assert result == {"data": []}
            assert mock_get.call_count == 2
            mock_sleep.assert_called_once() # Should sleep once

def test_fetch_materials_with_thermal_conductivity_filters_none():
    """Test that materials without kappa are filtered out."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"material_id": "mp-1", "kappa": 10.0},
            {"material_id": "mp-2", "kappa": None},
            {"material_id": "mp-3", "kappa": {"x": 5.0, "y": 5.0, "z": 5.0}},
            {"material_id": "mp-4", "kappa": {"x": None, "y": None, "z": None}}
        ]
    }
    
    with patch('code.download.fetch_with_retry_rate_limit', return_value=mock_response.json.return_value):
        result = download_module.fetch_materials_with_thermal_conductivity("fake_key")
        assert len(result) == 2
        assert result[0]["material_id"] == "mp-1"
        assert result[1]["material_id"] == "mp-3"

def test_download_cif_files_saves_correctly(tmp_path):
    """Test that CIF files are saved to the correct directory."""
    test_dir = tmp_path / "cif"
    test_dir.mkdir()
    
    materials = [{"material_id": "mp-test-1", "kappa": 10.0}]
    cif_content = "data_global\n_data_test\nloop_\n_atom_site_label C\n_atom_site_type_symbol C"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = cif_content
    
    # Mock the config to provide an API key
    with patch.object(download_module, 'get_config') as mock_config:
        mock_config.return_value.get.return_value = "fake_api_key"
        with patch('code.download.requests.get', return_value=mock_response):
            count = download_module.download_cif_files(materials, str(test_dir), target_count=1)
            
            assert count == 1
            assert (test_dir / "mp-test-1.cif").exists()
            
            with open(test_dir / "mp-test-1.cif", 'r') as f:
                assert f.read() == cif_content

def test_download_cif_files_respects_target_count(tmp_path):
    """Test that download stops after reaching target count."""
    test_dir = tmp_path / "cif"
    test_dir.mkdir()
    
    materials = [
        {"material_id": f"mp-{i}", "kappa": 10.0} for i in range(10)
    ]
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "data\n"
    
    with patch.object(download_module, 'get_config') as mock_config:
        mock_config.return_value.get.return_value = "fake_api_key"
        with patch('code.download.requests.get', return_value=mock_response):
            # Request only 3 files
            count = download_module.download_cif_files(materials, str(test_dir), target_count=3)
            
            assert count == 3
            files = list(test_dir.glob("*.cif"))
            assert len(files) == 3

def test_main_integration(tmp_path, caplog):
    """Test the main function end-to-end with mocked API."""
    # Setup temp directory for output
    output_dir = tmp_path / "data" / "raw" / "cif"
    output_dir.mkdir(parents=True)
    
    mock_materials = [
        {"material_id": "mp-main-1", "kappa": 5.0},
        {"material_id": "mp-main-2", "kappa": 6.0}
    ]
    
    mock_cif_response = MagicMock()
    mock_cif_response.status_code = 200
    mock_cif_response.text = "data\n"
    
    with patch.object(download_module, 'get_config') as mock_config:
        mock_config.return_value.get.return_value = "fake_api_key"
        with patch.object(download_module, 'fetch_materials_with_thermal_conductivity', return_value=mock_materials):
            with patch('code.download.requests.get', return_value=mock_cif_response):
                # Temporarily override output dir in main logic if needed, 
                # but main() hardcodes "data/raw/cif". 
                # We need to patch the path or move the temp dir.
                # Let's patch the output_dir variable inside main or just verify the logic.
                # Since main() is hardcoded, we'll mock the Path operations or change dir.
                # Better: patch the specific function call that uses the path.
                
                # Actually, let's just verify the logic flow by mocking the download function
                # to see if it gets called with the right args.
                
                with patch('code.download.download_cif_files', return_value=2) as mock_dl:
                    with patch('code.download.fetch_materials_with_thermal_conductivity', return_value=mock_materials):
                        result = download_module.main()
                        
                        # main() returns 0 if >= 50, else 1. Here we have 2.
                        assert result == 1
                        mock_dl.assert_called_once()
