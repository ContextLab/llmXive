import pytest
from code.material_db import get_material_conductivity, list_available_materials

def test_nist_defaults():
    """Test that NIST defaults are returned correctly."""
    assert get_material_conductivity("Si") == 149.0
    assert get_material_conductivity("CNT") == 3500.0
    assert get_material_conductivity("Ag") == 429.0
    assert get_material_conductivity("Au") == 318.0

def test_bulk_conductivity_override():
    """Test that provided bulk_conductivity overrides NIST defaults."""
    assert get_material_conductivity("Si", 200.0) == 200.0
    assert get_material_conductivity("Ag", 500.0) == 500.0

def test_config_object_interface():
    """Test that config-like objects are handled correctly."""
    class MockConfig:
        material = "Si"
        bulk_conductivity = None
    
    config = MockConfig()
    assert get_material_conductivity(config) == 149.0

def test_config_object_with_override():
    """Test config object with bulk_conductivity attribute."""
    class MockConfig:
        material = "Si"
        bulk_conductivity = 250.0
    
    config = MockConfig()
    assert get_material_conductivity(config) == 250.0

def test_config_object_with_explicit_override():
    """Test config object with explicit bulk_conductivity argument."""
    class MockConfig:
        material = "Si"
        bulk_conductivity = 250.0
    
    config = MockConfig()
    # Explicit argument should override config attribute
    assert get_material_conductivity(config, 300.0) == 300.0

def test_non_standard_material_error():
    """Test that non-standard materials raise ValueError."""
    with pytest.raises(ValueError, match="not found in local store or NIST defaults"):
        get_material_conductivity("UnknownMaterial")

def test_list_available_materials():
    """Test that list_available_materials returns correct data."""
    materials = list_available_materials()
    assert "Si" in materials
    assert materials["Si"] == 149
    assert "CNT" in materials
    assert materials["CNT"] == 3500