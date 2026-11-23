import os
import json
import hashlib
import pytest
from pathlib import Path
from code.data_ingestion import (
    fetch_all_nist_data, 
    load_nist_materials, 
    compute_file_checksum, 
    MATERIAL_CONFIG,
    ProjectError
)
from code.utils import get_project_root, get_data_dir, ensure_dir

def test_fetch_all_nist_data_creates_files(tmp_path):
    """Test that fetch_all_nist_data creates the JSON and checksum files."""
    output_dir = tmp_path / "raw"
    output_dir.mkdir()
    output_path = str(output_dir / "nist_materials.json")
    
    # Mock logger
    class MockLogger:
        def info(self, msg): pass
        def error(self, msg): pass
    
    logger = MockLogger()
    
    # Call the function
    checksum = fetch_all_nist_data(output_path, logger)
    
    # Check files exist
    assert os.path.exists(output_path)
    assert os.path.exists(output_path + ".sha256")
    
    # Check checksum file content
    with open(output_path + ".sha256", "r") as f:
        stored_checksum = f.read().strip()
    assert stored_checksum == checksum
    
    # Check JSON content structure
    with open(output_path, "r") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 4 # Aluminum, Copper, Iron, Polyethylene
    
    # Check material properties
    for item in data:
        assert "material_id" in item
        assert "cas" in item
        assert "properties" in item
        props = item["properties"]
        assert "thermal_conductivity" in props
        assert "emissivity" in props
        assert "specific_heat" in props
        assert "density" in props
        # Check values are positive
        assert props["thermal_conductivity"] > 0
        assert props["emissivity"] > 0
        assert props["specific_heat"] > 0
        assert props["density"] > 0

def test_load_nist_materials(tmp_path):
    """Test that load_nist_materials correctly loads the JSON file."""
    output_dir = tmp_path / "raw"
    output_dir.mkdir()
    output_path = str(output_dir / "nist_materials.json")
    
    # Mock logger
    class MockLogger:
        def info(self, msg): pass
        def error(self, msg): pass
    
    logger = MockLogger()
    
    # Fetch data first
    fetch_all_nist_data(output_path, logger)
    
    # Load data
    materials = load_nist_materials(output_path)
    
    assert len(materials) == 4
    # Check types
    from code.data_ingestion import MaterialProfile
    assert isinstance(materials[0], MaterialProfile)
    
    # Check material_id
    material_ids = [m.material_id for m in materials]
    assert "Aluminum" in material_ids
    assert "Copper" in material_ids
    assert "Carbon_Steel_1018" in material_ids
    assert "Polyethylene" in material_ids

def test_compute_file_checksum(tmp_path):
    """Test that compute_file_checksum returns a valid SHA256 hash."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = compute_file_checksum(str(test_file))
    assert len(checksum) == 64 # SHA256 hex length
    assert all(c in "0123456789abcdef" for c in checksum)

def test_material_config_valid():
    """Test that MATERIAL_CONFIG contains the required materials and properties."""
    required_materials = ["Aluminum", "Copper", "Carbon_Steel_1018", "Polyethylene"]
    required_properties = ["thermal_conductivity", "emissivity", "specific_heat", "density"]
    
    for mat in required_materials:
        assert mat in MATERIAL_CONFIG
        assert "cas" in MATERIAL_CONFIG[mat]
        assert "properties" in MATERIAL_CONFIG[mat]
        for prop in required_properties:
            assert prop in MATERIAL_CONFIG[mat]["properties"]
