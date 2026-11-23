"""
Contract test for USDA climate data loader (T024).
Verifies schema matches expected structure for downstream processing.
"""
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_loader import fetch_usda_climate_data
from config import load_config

def test_climate_data_schema():
    """
    Test that fetched climate data matches the expected schema:
    Dict[str, Dict[str, float]]
    Keys: species_name
    Values: {"avg_min_temp": float, "avg_max_temp": float, "avg_precip": float, "zone_id": int}
    """
    # Use a small, known set of species that exist in USDA PLANTS
    test_species = [
        "Zea mays",
        "Glycine max",
        "Triticum aestivum"
    ]
    
    try:
        result = fetch_usda_climate_data(test_species)
    except ValueError as e:
        pytest.fail(f"Data fetch failed: {e}")
    
    assert isinstance(result, dict), "Result must be a dictionary"
    assert len(result) > 0, "Result must contain data for at least one species"
    
    for species, data in result.items():
        assert isinstance(species, str), f"Species key must be string, got {type(species)}"
        assert isinstance(data, dict), f"Data for {species} must be a dictionary"
        
        # Check required fields
        required_fields = ["avg_min_temp", "avg_max_temp", "avg_precip"]
        for field in required_fields:
            assert field in data, f"Missing field '{field}' for {species}"
            assert isinstance(data[field], (int, float)), f"Field '{field}' must be numeric for {species}"
        
        # Check optional but expected field
        if "zone_id" in data:
            assert isinstance(data["zone_id"], int), f"zone_id must be int for {species}"
    
    # Verify that we got data for at least some of the input species
    # (Some might fail if not in USDA DB, but we expect most to succeed)
    assert len(result) >= 1, "Expected at least one successful fetch"

def test_climate_data_values_realistic():
    """
    Test that fetched values are within realistic physical bounds.
    """
    test_species = ["Zea mays"]
    
    try:
        result = fetch_usda_climate_data(test_species)
    except ValueError:
        pytest.skip("Could not fetch data for validation")
    
    for species, data in result.items():
        # Temperature in Celsius: -50 to 60 is reasonable for global plants
        assert -50 <= data["avg_min_temp"] <= 60, f"Min temp out of range for {species}"
        assert -50 <= data["avg_max_temp"] <= 60, f"Max temp out of range for {species}"
        
        # Precipitation in mm: 0 to 5000 is reasonable
        assert 0 <= data["avg_precip"] <= 5000, f"Precip out of range for {species}"
