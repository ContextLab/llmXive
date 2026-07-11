"""
Unit tests for periodic table utilities in utils/periodic_table.py.
"""
import pytest
from utils.periodic_table import (
    get_element_properties,
    get_atomic_radius,
    get_valence,
    get_electronegativity,
    calculate_weighted_average,
    calculate_atomic_radius_mismatch,
    calculate_valence_electron_concentration,
    calculate_electronegativity_average
)

class TestPeriodicTableUtils:
    """Test suite for periodic table utility functions."""

    def test_get_element_properties(self):
        """Test retrieval of element properties."""
        props = get_element_properties("Fe")
        assert props is not None, "Fe properties should not be None"
        assert "atomic_radius" in props, "Properties should contain atomic_radius"
        assert "valence" in props, "Properties should contain valence"
        assert "electronegativity" in props, "Properties should contain electronegativity"

    def test_get_atomic_radius(self):
        """Test atomic radius retrieval."""
        radius = get_atomic_radius("Fe")
        assert radius is not None, "Atomic radius for Fe should not be None"
        assert isinstance(radius, float), "Atomic radius should be a float"

    def test_get_valence(self):
        """Test valence retrieval."""
        valence = get_valence("Fe")
        assert valence is not None, "Valence for Fe should not be None"
        assert isinstance(valence, (int, float)), "Valence should be numeric"

    def test_get_electronegativity(self):
        """Test electronegativity retrieval."""
        en = get_electronegativity("Fe")
        assert en is not None, "Electronegativity for Fe should not be None"
        assert isinstance(en, float), "Electronegativity should be a float"

    def test_calculate_weighted_average(self):
        """Test weighted average calculation."""
        elements = ["Fe", "Cr", "Ni"]
        fractions = [0.6, 0.2, 0.2]
        # Sum of fractions must be 1.0
        assert abs(sum(fractions) - 1.0) < 1e-6, "Fractions should sum to 1.0"
        
        result = calculate_weighted_average(elements, fractions, "atomic_radius")
        assert result is not None, "Weighted average should not be None"
        assert isinstance(result, float), "Weighted average should be a float"

    def test_calculate_atomic_radius_mismatch(self):
        """Test atomic radius mismatch calculation."""
        elements = ["Fe", "Cr"]
        fractions = [0.8, 0.2]
        result = calculate_atomic_radius_mismatch(elements, fractions)
        assert result is not None, "Mismatch should not be None"
        assert isinstance(result, float), "Mismatch should be a float"
        assert result >= 0.0, "Mismatch should be non-negative"

    def test_calculate_valence_electron_concentration(self):
        """Test VEC calculation."""
        elements = ["Fe", "Cr"]
        fractions = [0.8, 0.2]
        result = calculate_valence_electron_concentration(elements, fractions)
        assert result is not None, "VEC should not be None"
        assert isinstance(result, float), "VEC should be a float"

    def test_calculate_electronegativity_average(self):
        """Test average electronegativity calculation."""
        elements = ["Fe", "Cr"]
        fractions = [0.8, 0.2]
        result = calculate_electronegativity_average(elements, fractions)
        assert result is not None, "Avg EN should not be None"
        assert isinstance(result, float), "Avg EN should be a float"
