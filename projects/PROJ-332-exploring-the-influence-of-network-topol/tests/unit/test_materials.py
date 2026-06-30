"""
Unit tests for material property fallback and NIST defaults.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the code directory to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from material_db import get_material_conductivity, list_available_materials


class TestNISTDefaults:
    """Test that NIST defaults are triggered correctly for standard materials."""

    def test_nist_defaults_trigger_silicon(self):
        """Verify NIST default for Silicon (Si) is 149 W/(m·K)."""
        result = get_material_conductivity("Si")
        assert result == 149.0
        assert isinstance(result, float)

    def test_nist_defaults_trigger_copper(self):
        """Verify NIST default for Copper (Cu) is not present (should raise error)."""
        # Based on T004, Cu is not in the NIST defaults list (Si, CNT, Ag, Au)
        with pytest.raises(ValueError) as exc_info:
            get_material_conductivity("Cu")
        assert "Material Cu not found in local store or NIST defaults" in str(exc_info.value)

    def test_nist_defaults_trigger_careful_ag(self):
        """Verify NIST default for Silver (Ag) is 429 W/(m·K)."""
        result = get_material_conductivity("Ag")
        assert result == 429.0

    def test_nist_defaults_trigger_gold(self):
        """Verify NIST default for Gold (Au) is 318 W/(m·K)."""
        result = get_material_conductivity("Au")
        assert result == 318.0

    def test_nist_defaults_trigger_cnt(self):
        """Verify NIST default for CNT is 3500 W/(m·K)."""
        result = get_material_conductivity("CNT")
        assert result == 3500.0

    def test_non_standard_material_error(self):
        """Verify clear error message for non-standard materials."""
        with pytest.raises(ValueError) as exc_info:
            get_material_conductivity("UnknownMaterial")
        error_msg = str(exc_info.value)
        assert "Material UnknownMaterial not found" in error_msg
        assert "local store or NIST defaults" in error_msg
        assert "please provide value" in error_msg

    def test_list_available_materials(self):
        """Verify list_available_materials returns the correct set of materials."""
        materials = list_available_materials()
        expected = {"Si", "CNT", "Ag", "Au"}
        assert isinstance(materials, list)
        assert set(materials) == expected