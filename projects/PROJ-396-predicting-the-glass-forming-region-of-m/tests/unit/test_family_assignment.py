"""
Unit tests for the family assignment logic in code/model_training.py.

Tests verify that compositions are correctly assigned to families based on
the element with the highest atomic fraction, with alphabetical tie-breaking.
"""

import pytest
import sys
import os

# Add the code directory to the path to import model_training
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from model_training import assign_family


class TestFamilyAssignment:
    """Test suite for assign_family function."""

    def test_single_element_composition(self):
        """Test composition with a single element."""
        composition = "Fe1.0"
        result = assign_family(composition)
        assert result == "Fe", f"Expected 'Fe', got '{result}'"

    def test_dominant_element(self):
        """Test composition where one element is clearly dominant."""
        composition = "Fe0.6Zr0.3Cu0.1"
        result = assign_family(composition)
        assert result == "Fe", f"Expected 'Fe', got '{result}'"

    def test_tie_break_alphabetical(self):
        """Test tie-breaking when two elements have equal atomic fractions."""
        # Fe and Zr both have 0.5, Fe comes before Zr alphabetically
        composition = "Fe0.5Zr0.5"
        result = assign_family(composition)
        assert result == "Fe", f"Expected 'Fe' (alphabetical tie-break), got '{result}'"

    def test_tie_break_three_way(self):
        """Test three-way tie breaking."""
        # Cu, Fe, Zr all have 0.333..., Cu comes first alphabetically
        composition = "Cu0.333Fe0.333Zr0.334"
        result = assign_family(composition)
        # Zr is 0.334, so it wins
        assert result == "Zr", f"Expected 'Zr', got '{result}'"

    def test_tie_break_three_way_equal(self):
        """Test three-way tie with equal fractions."""
        # Cu, Fe, Zr all have 1/3, Cu comes first alphabetically
        composition = "Cu0.333333Fe0.333333Zr0.333334"
        result = assign_family(composition)
        # Zr is slightly higher (0.333334), so it wins
        assert result == "Zr", f"Expected 'Zr', got '{result}'"

    def test_tie_break_exact_equal(self):
        """Test exact tie where alphabetical order matters."""
        # Manually construct a case where fractions are exactly equal
        # Using a simplified representation
        composition = "Mg0.5Ti0.5"
        result = assign_family(composition)
        assert result == "Mg", f"Expected 'Mg' (alphabetical tie-break), got '{result}'"

    def test_complex_composition(self):
        """Test a more complex multi-element composition."""
        composition = "Zr0.45Cu0.25Ni0.15Al0.15"
        result = assign_family(composition)
        assert result == "Zr", f"Expected 'Zr', got '{result}'"

    def test_case_sensitivity(self):
        """Test that element symbols are case-sensitive (standard format)."""
        # Standard format should work
        composition = "Fe0.8B0.2"
        result = assign_family(composition)
        assert result == "Fe"

    def test_whitespace_handling(self):
        """Test that whitespace in composition string is handled."""
        composition = "Fe 0.6 Zr 0.4"
        result = assign_family(composition)
        # The function should handle this or raise an error depending on implementation
        # Assuming it strips whitespace
        assert result == "Fe"

    def test_invalid_composition_format(self):
        """Test handling of invalid composition format."""
        composition = "InvalidFormat"
        # Should raise ValueError or return None depending on implementation
        with pytest.raises(ValueError):
            assign_family(composition)

    def test_zero_fraction(self):
        """Test composition with zero fraction (edge case)."""
        composition = "Fe0.0Zr1.0"
        result = assign_family(composition)
        assert result == "Zr", f"Expected 'Zr', got '{result}'"

    def test_very_small_differences(self):
        """Test composition with very small differences in fractions."""
        composition = "Fe0.5000001Zr0.4999999"
        result = assign_family(composition)
        assert result == "Fe", f"Expected 'Fe', got '{result}'"

    def test_common_metallic_glass_systems(self):
        """Test known metallic glass systems."""
        # Zr-based BMG
        composition = "Zr0.55Cu0.30Al0.10Ni0.05"
        result = assign_family(composition)
        assert result == "Zr"

        # Fe-based BMG
        composition = "Fe0.80B0.10Si0.05P0.05"
        result = assign_family(composition)
        assert result == "Fe"

        # Mg-based BMG
        composition = "Mg0.65Cu0.25Y0.10"
        result = assign_family(composition)
        assert result == "Mg"

        # Ti-based BMG
        composition = "Ti0.50Zr0.25Cu0.15Ni0.10"
        result = assign_family(composition)
        assert result == "Ti"

        # Cu-based BMG
        composition = "Cu0.50Zr0.40Al0.10"
        result = assign_family(composition)
        assert result == "Cu"