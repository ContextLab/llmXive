"""
Unit tests for traits_fallback module (T025b)
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.traits_fallback import (
    load_fallback_input,
    fetch_traits_from_phenoscape,
    fetch_traits_from_gbif,
    fetch_traits_for_species,
    save_trait_fallback_summary
)

@pytest.fixture
def temp_species_file(tmp_path):
    """Create a temporary post_qc_species_list.json file"""
    species_data = [
        {"species": "Arabidopsis thaliana"},
        {"species": "Solanum lycopersicum"},
        {"species": "Zea mays"}
    ]
    file_path = tmp_path / "post_qc_species_list.json"
    with open(file_path, 'w') as f:
        json.dump(species_data, f)
    return file_path

@pytest.fixture
def temp_fallback_summary(tmp_path):
    """Create a temporary trait_fallback_summary.json file"""
    summary_data = {
        "target_species": ["Arabidopsis thaliana", "Solanum lycopersicum", "Zea mays"],
        "primary_source_results": {
            "Arabidopsis thaliana": {"traits": {"chemical": 0.5}}
        },
        "missing_from_try": ["Solanum lycopersicum", "Zea mays"],
        "missing_from_all_sources": []
    }
    file_path = tmp_path / "trait_fallback_summary.json"
    with open(file_path, 'w') as f:
        json.dump(summary_data, f)
    return file_path

def test_load_fallback_input_valid(temp_species_file, temp_fallback_summary, tmp_path):
    """Test loading fallback input with valid files"""
    # Mock get_data_path to return tmp_path
    with patch('src.data.traits_fallback.get_data_path', return_value=str(tmp_path.parent)):
        # Create the expected directory structure
        processed_dir = tmp_path
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy test files to expected location
        import shutil
        shutil.copy(temp_species_file, processed_dir / "post_qc_species_list.json")
        shutil.copy(temp_fallback_summary, processed_dir / "trait_fallback_summary.json")
        
        result = load_fallback_input()
        
        assert 'target_species' in result
        assert 'missing_from_try' in result
        assert 'processed_path' in result
        assert len(result['target_species']) == 3
        assert len(result['missing_from_try']) == 2
        assert "Solanum lycopersicum" in result['missing_from_try']

@patch('src.data.traits_fallback.requests.get')
def test_fetch_traits_from_phenoscape_mocked(mock_get, tmp_path):
    """Test fetching traits from Phenoscape with mocked API response"""
    # Mock successful search response
    mock_search_response = MagicMock()
    mock_search_response.status_code = 200
    mock_search_response.json.return_value = {
        'results': [{'id': 'taxon_123'}]
    }
    
    # Mock successful traits response
    mock_traits_response = MagicMock()
    mock_traits_response.status_code = 200
    mock_traits_response.json.return_value = {
        'traits': [
            {'label': 'Chemical Defense', 'value': 'high', 'evidence': []},
            {'label': 'Physical Defense', 'value': 'moderate', 'evidence': []}
        ]
    }
    
    # Configure mock to return different responses based on URL
    def mock_response(url, *args, **kwargs):
        if 'search' in url:
            return mock_search_response
        else:
            return mock_traits_response
    
    mock_get.side_effect = mock_response
    
    result = fetch_traits_from_phenoscape("Arabidopsis thaliana")
    
    assert result is not None
    assert result['source'] == 'phenoscape'
    assert result['species'] == "Arabidopsis thaliana"
    assert result['found'] is True
    assert 'chemical_defense' in result['traits'] or 'chemical defense' in result['traits']

@patch('src.data.traits_fallback.requests.get')
def test_fetch_traits_from_gbif_mocked(mock_get, tmp_path):
    """Test fetching traits from GBIF with mocked API response"""
    # Mock successful search response
    mock_search_response = MagicMock()
    mock_search_response.status_code = 200
    mock_search_response.json.return_value = {
        'results': [{'key': 'species_456'}]
    }
    
    # Mock successful occurrence response
    mock_occurrence_response = MagicMock()
    mock_occurrence_response.status_code = 200
    mock_occurrence_response.json.return_value = {
        'count': 150,
        'results': []
    }
    
    def mock_response(url, *args, **kwargs):
        if 'search' in url and 'species' in url:
            return mock_search_response
        else:
            return mock_occurrence_response
    
    mock_get.side_effect = mock_response
    
    result = fetch_traits_from_gbif("Solanum lycopersicum")
    
    assert result is not None
    assert result['source'] == 'gbif'
    assert result['species'] == "Solanum lycopersicum"
    assert result['found'] is True
    assert result['traits']['occurrence_count'] == 150

@patch('src.data.traits_fallback.fetch_traits_from_phenoscape')
@patch('src.data.traits_fallback.fetch_traits_from_gbif')
def test_fetch_traits_for_species_integration(mock_gbif, mock_phenoscape, tmp_path):
    """Test integrated fetching from both sources"""
    # Mock Phenoscape to return data
    mock_phenoscape.return_value = {
        'source': 'phenoscape',
        'species': 'Test species',
        'traits': {'chemical': 'high'},
        'found': True
    }
    
    # Mock GBIF to return None
    mock_gbif.return_value = None
    
    result = fetch_traits_for_species("Test species")
    
    assert result['species'] == "Test species"
    assert result['found_any'] is True
    assert result['phenoscape'] is not None
    assert result['gbif'] is None

def test_save_trait_fallback_summary(tmp_path):
    """Test saving trait fallback summary to JSON"""
    summary_data = {
        'target_species': ['Species A'],
        'fallback_results': {
            'Species A': {'source': 'phenoscape', 'found': True}
        },
        'missing_from_try': [],
        'missing_from_all_sources': []
    }
    
    output_path = tmp_path / "test_summary.json"
    
    # Patch get_data_path to return tmp_path
    with patch('src.data.traits_fallback.get_data_path', return_value=str(tmp_path)):
        save_trait_fallback_summary(summary_data, tmp_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data == summary_data

@patch('src.data.traits_fallback.requests.get')
def test_fetch_traits_from_phenoscape_api_error(mock_get):
    """Test handling of Phenoscape API error"""
    mock_get.side_effect = Exception("API Error")
    
    result = fetch_traits_from_phenoscape("Test species")
    
    assert result is None

@patch('src.data.traits_fallback.requests.get')
def test_fetch_traits_from_gbif_no_species(mock_get):
    """Test handling of species not found in GBIF"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'results': []}
    mock_get.return_value = mock_response
    
    result = fetch_traits_from_gbif("Nonexistent species")
    
    assert result is None