"""
Unit tests for the materials.py module.
"""

import pytest
from src.data.materials import (
    list_available_materials,
    get_material_constants,
    get_lattice_constant,
    get_r_lattice,
    MATERIAL_CONSTANTS
)

class TestMaterials:
    def test_list_available_materials(self):
        """Test that the list of materials contains expected entries."""
        materials = list_available_materials()
        assert "graphene" in materials
        assert "MoS2" in materials
        assert len(materials) >= 2

    def test_get_material_constants_valid(self):
        """Test retrieving constants for a valid material."""
        constants = get_material_constants("graphene")
        assert "lattice_constant" in constants
        assert "R_lattice" in constants
        assert "description" in constants
        assert constants["lattice_constant"] > 0
        assert constants["R_lattice"] > 0

    def test_get_material_constants_invalid(self):
        """Test that invalid material raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            get_material_constants("unknown_material")

    def test_get_lattice_constant(self):
        """Test retrieving specific lattice constant."""
        a_graphene = get_lattice_constant("graphene")
        a_mos2 = get_lattice_constant("MoS2")
        
        # Check case insensitivity
        a_graphene_upper = get_lattice_constant("GRAPHENE")
        assert a_graphene == a_graphene_upper

        # Verify values are reasonable (approx 0.2-0.4 nm for 2D materials)
        assert 0.2 < a_graphene < 0.3
        assert 0.3 < a_mos2 < 0.4

    def test_get_r_lattice(self):
        """Test retrieving specific R_lattice value."""
        r_graphene = get_r_lattice("graphene")
        r_mos2 = get_r_lattice("MoS2")

        assert r_graphene > 0
        assert r_mos2 > 0
        # Ensure they are distinct values to test logic downstream
        assert r_graphene != r_mos2

    def test_materials_are_consistent(self):
        """Test that all materials in the dict have required keys."""
        for name, constants in MATERIAL_CONSTANTS.items():
            assert "lattice_constant" in constants, f"{name} missing lattice_constant"
            assert "R_lattice" in constants, f"{name} missing R_lattice"
            assert "description" in constants, f"{name} missing description"
            assert isinstance(constants["lattice_constant"], (int, float))
            assert isinstance(constants["R_lattice"], (int, float))
            assert constants["lattice_constant"] > 0
            assert constants["R_lattice"] > 0