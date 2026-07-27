"""
Unit tests for T025a: traits_try.py
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.traits_try import (
    load_target_species_list,
    fetch_traits_for_species,
    compile_try_results,
    save_trait_fallback_summary
)

@pytest.fixture
def temp_species_file():
    """Creates a temporary post_qc_species_list.json file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([
            {"species": "Arabidopsis thaliana", "exclusion_reason": None},
            {"species": "Solanum lycopersicum", "exclusion_reason": None}
        ], f)
    path = Path(f.name)
    yield path
    path.unlink()

@patch('src.data.traits_try.INPUT_FILE')
def test_load_target_species_list_valid(mock_input_file, temp_species_file):
    """Test loading a valid species list."""
    mock_input_file.__truediv__.return_value = temp_species_file
    # Override the global constant for the test context
    import src.data.traits_try as module
    original_path = module.INPUT_FILE
    module.INPUT_FILE = temp_species_file
    
    try:
        species = load_target_species_list()
        assert len(species) == 2
        assert "Arabidopsis thaliana" in species
        assert "Solanum lycopersicum" in species
    finally:
        module.INPUT_FILE = original_path

@patch('src.data.traits_try.INPUT_FILE')
def test_load_target_species_list_empty(mock_input_file):
    """Test loading an empty species list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([], f)
        temp_path = Path(f.name)
    
    try:
        import src.data.traits_try as module
        original_path = module.INPUT_FILE
        module.INPUT_FILE = temp_path
        
        species = load_target_species_list()
        assert species == []
    finally:
        temp_path.unlink()
        module.INPUT_FILE = original_path

@patch('src.data.traits_try.requests.post')
def test_fetch_traits_for_species_success(mock_post):
    """Test successful API fetch."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "traits": [
            {"trait_id": 1, "value": 10.5, "unit": "mg/g"}
        ]
    }
    mock_post.return_value = mock_response
    
    result = fetch_traits_for_species("Test Species", "fake_key")
    assert result is not None
    assert "traits" in result
    mock_post.assert_called_once()

@patch('src.data.traits_try.requests.post')
def test_fetch_traits_for_species_not_found(mock_post):
    """Test 404 response handling."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_post.return_value = mock_response
    
    result = fetch_traits_for_species("Unknown Species", "fake_key")
    assert result is None

def test_save_trait_fallback_summary():
    """Test saving the summary to a file."""
    summary_data = {
        "target_species": ["Species A"],
        "primary_source_results": {"Species A": {"traits": []}},
        "missing_from_try": []
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_summary.json"
        save_trait_fallback_summary(summary_data, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        assert loaded["target_species"] == ["Species A"]
        assert "Species A" in loaded["primary_source_results"]
