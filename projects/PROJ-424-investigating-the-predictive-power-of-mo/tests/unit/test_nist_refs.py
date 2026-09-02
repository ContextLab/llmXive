"""
Unit tests for the NIST references data integrity and structure.
"""
import json
import os
from pathlib import Path
import pytest

# Path to the NIST refs file
# Assuming tests run from project root
NIST_REFS_PATH = Path("code/data/raw/nist_refs.json")

@pytest.fixture
def nist_data():
    if not NIST_REFS_PATH.exists():
        pytest.skip(f"NIST refs file not found at {NIST_REFS_PATH}")
    with open(NIST_REFS_PATH, "r") as f:
        return json.load(f)

def test_nist_refs_file_exists():
    """Test that the NIST references file exists."""
    assert NIST_REFS_PATH.exists(), f"File {NIST_REFS_PATH} does not exist."

def test_nist_refs_structure(nist_data):
    """Test the structure of the NIST references JSON."""
    assert "metadata" in nist_data, "Missing 'metadata' key."
    assert "data" in nist_data, "Missing 'data' key."
    
    # Check metadata fields
    assert "sources" in nist_data["metadata"], "Missing 'sources' in metadata."
    assert len(nist_data["metadata"]["sources"]) == 3, "Expected 3 sources in metadata."
    
    # Check data fields
    expected_solvents = {"water", "ethanol", "acetone"}
    actual_solvents = set(nist_data["data"].keys())
    assert actual_solvents == expected_solvents, f"Expected solvents {expected_solvents}, got {actual_solvents}"

def test_nist_refs_values(nist_data):
    """Test that diffusion coefficients are positive and within reasonable ranges."""
    data = nist_data["data"]
    
    # Water: ~2.3e-9 m2/s
    assert 1.0e-9 < data["water"]["D_exp_m2_s"] < 5.0e-9, "Water diffusion coefficient out of range."
    
    # Ethanol: ~1.0e-9 m2/s
    assert 0.5e-9 < data["ethanol"]["D_exp_m2_s"] < 3.0e-9, "Ethanol diffusion coefficient out of range."
    
    # Acetone: ~4.5e-9 m2/s
    assert 2.0e-9 < data["acetone"]["D_exp_m2_s"] < 10.0e-9, "Acetone diffusion coefficient out of range."

def test_nist_refs_temperatures(nist_data):
    """Test that all temperatures are 298.15K."""
    data = nist_data["data"]
    for solvent in data:
        assert data[solvent]["temperature_K"] == 298.15, f"Temperature for {solvent} is not 298.15K."

def test_nist_refs_source_citations(nist_data):
    """Test that all sources have valid citations."""
    sources = nist_data["metadata"]["sources"]
    for source in sources:
        assert "id" in source, "Source missing 'id'."
        assert "title" in source, "Source missing 'title'."
        assert "url" in source, "Source missing 'url'."
        assert "substance" in source, "Source missing 'substance'."
        assert "value_m2_s" in source, "Source missing 'value_m2_s'."