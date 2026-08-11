"""
Tests for ingestion fetch functions.
"""
import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import (
    fetch_materials_project_data,
    fetch_nist_data,
    fetch_arxiv_data,
    fetch_curated_literature_data,
    RAW_DATA_DIR
)

def test_fetch_materials_project_no_api_key():
    """Test that RuntimeError is raised if MP_API_KEY is missing."""
    # Ensure key is not set
    if 'MP_API_KEY' in os.environ:
        del os.environ['MP_API_KEY']
    
    with pytest.raises(RuntimeError) as exc_info:
        fetch_materials_project_data()
    
    assert "MP_API_KEY not found" in str(exc_info.value)

@patch('ingestion.MPRestClient')
def test_fetch_materials_project_success(mock_client):
    """Test successful fetch from Materials Project."""
    # Mock the client
    mock_instance = MagicMock()
    mock_client.return_value = mock_instance
    
    # Mock entries
    mock_entry = MagicMock()
    mock_entry.as_dict.return_value = {
        'material_id': 'mp-123',
        'formula_pretty': 'Al2O3',
        'properties': {'weibull_modulus': 15.5}
    }
    mock_instance.get_entries.return_value = [mock_entry]
    
    # Run fetch
    result = fetch_materials_project_data()
    
    # Verify
    assert result['count'] == 1
    assert result['data'][0]['weibull_modulus'] == 15.5
    assert Path(RAW_DATA_DIR / "materials_project_raw.json").exists()

@patch('ingestion.requests.get')
def test_fetch_nist_data_success(mock_get):
    """Test successful fetch from NIST."""
    # Mock response
    mock_response = MagicMock()
    mock_response.text = "composition,weibull_modulus,sample_count\nAl2O3,12.5,50\nSiC,10.0,30"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    result = fetch_nist_data()
    
    assert result['count'] == 2
    assert Path(RAW_DATA_DIR / "nist_raw.json").exists()

@patch('ingestion.requests.get')
def test_fetch_curated_literature_success(mock_get):
    """Test successful fetch from Curated Literature."""
    mock_response = MagicMock()
    mock_response.text = "composition,weibull_modulus\nZrO2,8.5\nMgO,9.0"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    result = fetch_curated_literature_data()
    
    assert result['count'] == 2
    assert Path(RAW_DATA_DIR / "curated_literature_raw.json").exists()

@patch('ingestion.arxiv.Search')
@patch('ingestion.arxiv.Client')
@patch('ingestion.pdfplumber.open')
def test_fetch_arxiv_data_success(mock_pdf, mock_client, mock_search):
    """Test successful fetch from ArXiv."""
    # Mock search result
    mock_result = MagicMock()
    mock_result.entry_id = "1234.5678"
    mock_result.download_pdf = MagicMock()
    mock_search.return_value.results.return_value = [mock_result]
    mock_client.return_value.results.return_value = [mock_result]
    
    # Mock PDF table
    mock_table = [
        ["composition", "weibull_modulus"],
        ["TiO2", "11.0"]
    ]
    mock_page = MagicMock()
    mock_page.extract_tables.return_value = [mock_table]
    mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
    
    result = fetch_arxiv_data()
    
    assert result['count'] == 1
    assert Path(RAW_DATA_DIR / "arxiv_raw.json").exists()

def test_derive_primary_anion_cation_group():
    """Test primary anion/cation derivation."""
    from ingestion import derive_primary_anion_cation_group
    
    # Test Al2O3
    result = derive_primary_anion_cation_group("Al2O3")
    assert result == "O-Al"
    
    # Test SiC
    result = derive_primary_anion_cation_group("SiC")
    assert result == "C-Si"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
