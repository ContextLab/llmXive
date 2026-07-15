"""
Unit tests for material property handling (T018, T037).
"""
import sys
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from material_db import get_material_conductivity, list_available_materials

def test_nist_defaults_trigger():
    """
    Verify NIST defaults trigger correctly for standard materials.
    """
    # Test known materials
    si_conductivity = get_material_conductivity("Si")
    assert si_conductivity == 149.0
    
    cnt_conductivity = get_material_conductivity("CNT")
    assert cnt_conductivity == 3500.0
    
    ag_conductivity = get_material_conductivity("Ag")
    assert ag_conductivity == 429.0
    
    au_conductivity = get_material_conductivity("Au")
    assert au_conductivity == 318.0

def test_non_standard_material_error():
    """
    Verify clear error is raised for non-standard materials.
    """
    # Test that an error is raised for a non-existent material
    with pytest.raises(ValueError) as exc_info:
        get_material_conductivity("NonExistentMaterial")
    
    # Verify the error message contains the expected text
    assert "not found in local store or NIST defaults" in str(exc_info.value)
    assert "please provide value in W/(m·K)" in str(exc_info.value)

def test_list_available_materials():
    """
    Verify list_available_materials returns expected materials.
    """
    materials = list_available_materials()
    assert "Si" in materials
    assert "CNT" in materials
    assert "Ag" in materials
    assert "Au" in materials
    assert len(materials) >= 4