"""
Tests for the configuration management module.
"""
import pytest
from pathlib import Path
import sys
import os

# Ensure the src directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.config import (
    RANDOM_SEED,
    SUPPORTED_SPECIES,
    SPECIES_CONFIG,
    PATHS,
    get_species_accession,
    get_species_info,
    ensure_paths_exist,
    save_config_to_json,
    HYPERPARAMS
)

def test_random_seed_is_42():
    """Verify the random seed is set to 42 as per FR-007."""
    assert RANDOM_SEED == 42

def test_supported_species_list():
    """Verify the list of supported species contains expected values."""
    expected = ["wheat", "rice", "maize", "tomato", "soybean"]
    assert set(SUPPORTED_SPECIES) == set(expected)

def test_species_accession_ids():
    """Verify accession IDs match the specification."""
    assert get_species_accession("wheat") == "GCA_000003205.5"
    assert get_species_accession("rice") == "GCA_001433935.2"
    assert get_species_accession("maize") == "GCA_000005005.4"
    assert get_species_accession("tomato") == "GCA_000188115.5"
    assert get_species_accession("soybean") == "GCA_000004195.3"
    assert get_species_accession("unknown_species") is None

def test_species_info_structure():
    """Verify the structure of species info dictionaries."""
    wheat_info = get_species_info("wheat")
    assert wheat_info is not None
    assert "scientific_name" in wheat_info
    assert "source" in wheat_info
    assert wheat_info["scientific_name"] == "Triticum aestivum"

def test_paths_exist():
    """Verify that ensure_paths_exist creates the required directories."""
    # This should not raise an error
    ensure_paths_exist()
    
    # Verify root paths exist
    for key, path in PATHS.items():
        assert path.exists(), f"Path {key} ({path}) does not exist after ensure_paths_exist"

def test_save_config_to_json():
    """Verify config can be saved to JSON and contains expected keys."""
    output_path = save_config_to_json()
    assert output_path.exists()
    
    import json
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert "random_seed" in data
    assert data["random_seed"] == 42
    assert "supported_species" in data
    assert "species_details" in data
    assert "hyperparameters" in data
    assert "paths" in data

def test_hyperparameters():
    """Verify default hyperparameters are set correctly."""
    assert HYPERPARAMS["knn_neighbors"] == 5
    assert HYPERPARAMS["max_distance_km"] == 50
    assert HYPERPARAMS["ld_threshold"] == 0.8
    assert HYPERPARAMS["permutation_count"] == 1000
    assert HYPERPARAMS["max_retries"] == 3