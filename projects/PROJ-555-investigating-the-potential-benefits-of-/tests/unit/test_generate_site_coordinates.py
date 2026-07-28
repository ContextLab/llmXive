"""
Unit tests for generate_site_coordinates module.
"""
import pytest
import csv
import tempfile
from pathlib import Path

from generate_site_coordinates import generate_site_pairs, write_site_coordinates

def test_generate_site_pairs_count():
    """Test that the correct number of sites are generated."""
    count = 10
    sites = generate_site_pairs(count=count)
    # Each pair generates 2 sites (1 eco, 1 control)
    assert len(sites) == count * 2

def test_generate_site_pairs_structure():
    """Test that each site has the required fields."""
    sites = generate_site_pairs(count=1)
    site = sites[0]
    required_fields = [
        "site_id", "site_type", "latitude", "longitude", 
        "biome", "protection_status", "pair_id"
    ]
    for field in required_fields:
        assert field in site

def test_generate_site_pairs_types():
    """Test that site types are correct."""
    sites = generate_site_pairs(count=5)
    eco_sites = [s for s in sites if s["site_type"] == "ecotourism"]
    ctrl_sites = [s for s in sites if s["site_type"] == "control"]
    assert len(eco_sites) == 5
    assert len(ctrl_sites) == 5

def test_generate_site_pairs_coordinates():
    """Test that coordinates are within the defined bounding box."""
    MIN_LAT, MAX_LAT = 8.0, 12.0
    MIN_LON, MAX_LON = -86.0, -82.0
    
    sites = generate_site_pairs(count=50)
    for site in sites:
        assert MIN_LAT <= site["latitude"] <= MAX_LAT
        assert MIN_LON <= site["longitude"] <= MAX_LON

def test_write_site_coordinates(tmp_path):
    """Test writing sites to a CSV file."""
    sites = generate_site_pairs(count=5)
    output_file = tmp_path / "test_sites.csv"
    
    write_site_coordinates(sites, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 10
    assert rows[0]["site_id"].startswith("ECO-") or rows[0]["site_id"].startswith("CTRL-")
    
    # Check header
    expected_header = [
        "site_id", "site_type", "latitude", "longitude", 
        "biome", "protection_status", "pair_id"
    ]
    assert reader.fieldnames == expected_header

def test_write_site_coordinates_empty():
    """Test that writing empty list raises error."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / "empty.csv"
        with pytest.raises(ValueError, match="No sites to write"):
            write_site_coordinates([], output_file)