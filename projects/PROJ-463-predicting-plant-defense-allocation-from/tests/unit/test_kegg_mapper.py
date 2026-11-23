"""
Unit tests for KEGG Mapper module.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to mock the imports that might fail or be slow
import sys
from io import StringIO

# Mock bioservices if needed, but the module handles ImportError
# We will test the logic paths.

@pytest.fixture
def temp_fallback_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "AT1G01010": ["path:ath00010", "path:ath00020"],
            "AT1G01020": ["path:ath00030"]
        }, f)
        yield Path(f.name)
    Path(f.name).unlink()

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_local_fallback_mapping(temp_fallback_file):
    from src.data.kegg_mapper import load_local_fallback_mapping
    
    result = load_local_fallback_mapping(temp_fallback_file)
    assert "AT1G01010" in result
    assert result["AT1G01010"] == ["path:ath00010", "path:ath00020"]
    assert len(result) == 2

def test_load_local_fallback_missing_file():
    from src.data.kegg_mapper import load_local_fallback_mapping
    import logging
    
    # Capture log to avoid noise
    with patch('src.data.kegg_mapper.logger') as mock_logger:
        result = load_local_fallback_mapping(Path("/nonexistent/path.json"))
        assert result == {}
        mock_logger.error.assert_called_once()

@patch('src.data.kegg_mapper.requests.get')
def test_fetch_kegg_mappings_via_api_direct(mock_get):
    from src.data.kegg_mapper import fetch_kegg_mappings_via_api
    
    # Mock response for direct API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "path:ath00010\tath00010\npath:ath00020\tath00020"
    mock_get.return_value = mock_response

    gene_ids = ["AT1G01010"]
    result = fetch_kegg_mappings_via_api(gene_ids)
    
    assert "AT1G01010" in result
    assert "path:ath00010" in result["AT1G01010"]
    assert "path:ath00020" in result["AT1G01010"]
    mock_get.assert_called_once()

@patch('src.data.kegg_mapper.requests.get')
def test_fetch_kegg_mappings_via_api_failure(mock_get):
    from src.data.kegg_mapper import fetch_kegg_mappings_via_api
    
    mock_get.side_effect = Exception("Network error")
    
    gene_ids = ["AT1G01010"]
    result = fetch_kegg_mappings_via_api(gene_ids)
    
    assert result == {}

def test_main_integration(temp_output_dir, temp_fallback_file):
    from src.data.kegg_mapper import main
    from src.utils.config import get_data_path
    
    # We need to mock get_data_path to return our temp dir
    # But the module uses get_data_path() internally.
    # We can patch the function in the module.
    
    # Create a fake processed directory with a dummy CSV
    processed_dir = temp_output_dir / "processed"
    processed_dir.mkdir()
    raw_dir = temp_output_dir / "raw"
    raw_dir.mkdir()
    
    # Write fallback to raw
    fallback_dest = raw_dir / "kegg_mapping_local.json"
    with open(fallback_dest, 'w') as f:
        json.dump({
            "AT1G01010": ["path:ath00010"]
        }, f)

    # Create a dummy CSV in processed to trigger gene extraction
    csv_path = processed_dir / "dummy_tpm.csv"
    with open(csv_path, 'w') as f:
        f.write("gene_id,sample1\nAT1G01010,10.5\nAT1G01020,20.0\n")

    with patch('src.data.kegg_mapper.get_data_path', return_value=temp_output_dir):
        with patch('src.data.kegg_mapper.fetch_kegg_mappings_via_api', return_value={}):
            # Force it to use fallback
            result = main()
    
    output_path = processed_dir / "pathway_mappings.json"
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert "AT1G01010" in saved_data
    assert "path:ath00010" in saved_data["AT1G01010"]