"""
Unit Tests for Trait Caching (T025c)
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import sys
from unittest.mock import patch, MagicMock

# Adjust path for imports if running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.traits_cache import cache_raw_response, load_cached_response, CACHE_DIR

@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the get_data_path function to return our temp dir
        temp_traits_dir = Path(tmpdir) / "raw" / "traits"
        temp_traits_dir.mkdir(parents=True, exist_ok=True)
        
        # Patch the module's CACHE_DIR
        original_cache_dir = None
        with patch('src.data.traits_cache.CACHE_DIR', temp_traits_dir):
            yield temp_traits_dir

def test_cache_raw_response_creates_file(temp_cache_dir):
    """Test that cache_raw_response creates a valid JSON file."""
    source = "try"
    species = "Arabidopsis_thaliana"
    raw_data = {"traits": [{"name": "height", "value": 10}]}
    
    file_path = cache_raw_response(source, species, raw_data)
    
    assert file_path.exists()
    assert file_path.name == f"{source}_{species}.json"
    
    with open(file_path, 'r') as f:
        content = json.load(f)
    
    assert content["source"] == source
    assert content["species_name"] == species
    assert content["payload"] == raw_data
    assert "cached_at" in content

def test_cache_raw_response_with_metadata(temp_cache_dir):
    """Test caching with additional metadata."""
    source = "phenoscape"
    species = "Zea_mays"
    raw_data = {"results": []}
    meta = {"request_id": "12345", "params": {"id": "ZEA"}}
    
    file_path = cache_raw_response(source, species, raw_data, metadata=meta)
    
    with open(file_path, 'r') as f:
        content = json.load(f)
    
    assert content["metadata"] == meta

def test_load_cached_response_success(temp_cache_dir):
    """Test loading a cached response."""
    source = "gbif"
    species = "Solanum_lycopersicum"
    raw_data = {"count": 42}
    
    # First cache it
    cache_raw_response(source, species, raw_data)
    
    # Then load it
    loaded = load_cached_response(source, species)
    
    assert loaded is not None
    assert loaded["payload"] == raw_data
    assert loaded["source"] == source

def test_load_cached_response_missing(temp_cache_dir):
    """Test loading a non-existent cache returns None."""
    result = load_cached_response("try", "NonExistentSpecies")
    assert result is None

def test_cache_raw_response_invalid_json(temp_cache_dir):
    """Test that non-serializable objects raise an error."""
    source = "try"
    species = "Test"
    raw_data = {"obj": object()} # Not JSON serializable
    
    with pytest.raises(TypeError):
        cache_raw_response(source, species, raw_data)

def test_special_characters_in_species_name(temp_cache_dir):
    """Test sanitization of species names with spaces/slashes."""
    source = "try"
    species = "Quercus alba / Subsp. virginiana"
    raw_data = {"test": True}
    
    file_path = cache_raw_response(source, species, raw_data)
    
    # Check that spaces and slashes are replaced
    assert " " not in file_path.name
    assert "/" not in file_path.name
    assert "Quercus_alba__Subsp._virginiana" in file_path.name