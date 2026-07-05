# tests/unit/test_constants.py
"""
Unit tests for periodic table data integrity in code/utils/constants.py.
"""

import pytest
from code.utils.constants import (
    PERIODIC_TABLE,
    get_metallic_radius,
    get_electronegativity,
    ElementData,
)

class TestPeriodicTableData:
    """Tests for the PERIODIC_TABLE dictionary structure."""

    def test_required_elements_present(self):
        """Verify that key FCC metals (Ni, Cu, Al, Fe, Pt) are present."""
        required_elements = {"Ni", "Cu", "Al", "Fe", "Pt", "Au", "Ag", "Pb"}
        for elem in required_elements:
            assert elem in PERIODIC_TABLE, f"Missing required element: {elem}"

    def test_data_structure_integrity(self):
        """Verify that all entries are ElementData instances with valid types."""
        for symbol, data in PERIODIC_TABLE.items():
            assert isinstance(data, ElementData)
            assert isinstance(data.symbol, str)
            assert isinstance(data.name, str)
            assert isinstance(data.metallic_radius_pm, (int, float))
            assert isinstance(data.electronegativity, (int, float))
            
            # Sanity checks on values
            assert data.metallic_radius_pm > 0, f"Invalid radius for {symbol}"
            assert 0 < data.electronegativity <= 4.0, f"Invalid EN for {symbol}"

    def test_known_values(self):
        """Verify specific known values from literature."""
        # Nickel (Ni)
        assert PERIODIC_TABLE["Ni"].metallic_radius_pm == 124.0
        assert PERIODIC_TABLE["Ni"].electronegativity == 1.91
        
        # Copper (Cu)
        assert PERIODIC_TABLE["Cu"].metallic_radius_pm == 128.0
        assert PERIODIC_TABLE["Cu"].electronegativity == 1.90
        
        # Aluminum (Al)
        assert PERIODIC_TABLE["Al"].metallic_radius_pm == 143.0
        assert PERIODIC_TABLE["Al"].electronegativity == 1.61

    def test_case_insensitivity(self):
        """Verify that lookup is case-insensitive via helper functions."""
        assert get_metallic_radius("ni") == get_metallic_radius("Ni")
        assert get_electronegativity("fe") == get_electronegativity("Fe")

class TestHelperFunctions:
    """Tests for the accessor helper functions."""

    def test_get_metallic_radius_success(self):
        """Test successful retrieval of metallic radius."""
        radius = get_metallic_radius("Au")
        assert radius is not None
        assert radius == 144.0

    def test_get_metallic_radius_not_found(self):
        """Test retrieval for non-existent element returns None."""
        # Using a fictional element or one not in our list
        radius = get_metallic_radius("Xx")
        assert radius is None

    def test_get_electronegativity_success(self):
        """Test successful retrieval of electronegativity."""
        en = get_electronegativity("O")
        assert en is not None
        assert en == 3.44

    def test_get_electronegativity_not_found(self):
        """Test retrieval for non-existent element returns None."""
        en = get_electronegativity("Zz")
        assert en is None

    def test_missing_element_in_dict(self):
        """Ensure that missing keys in dict return None via helpers."""
        assert get_metallic_radius("Missing") is None
        assert get_electronegativity("Missing") is None
