"""
Unit tests for thermodynamic feature engineering functions in features.py.
"""
import pytest
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

# Import the specific functions being tested from the features module
from features import (
    parse_composition,
    calculate_mixing_enthalpy,
    calculate_atomic_size_mismatch,
    calculate_electronegativity_variance,
    get_element_properties_safe
)

class TestMixingEnthalpy:
    """Tests for the calculate_mixing_enthalpy function."""

    def test_mixing_enthalpy_ternary_system(self):
        """Test mixing enthalpy calculation for a known ternary system."""
        # Example: Cu-Zr-Al system (common bulk metallic glass former)
        # Composition: Cu60Zr30Al10 (atomic percent)
        composition = {'Cu': 0.60, 'Zr': 0.30, 'Al': 0.10}
        
        # Calculate mixing enthalpy
        result = calculate_mixing_enthalpy(composition)
        
        # Verify result is a float
        assert isinstance(result, float), "Mixing enthalpy should be a float"
        
        # Verify result is negative (exothermic mixing is favorable for glass formation)
        # Note: The actual value depends on the binary interaction parameters in mendeleev
        # We assert it's a reasonable physical value (typically between -50 and 0 kJ/mol)
        assert -100 < result < 10, f"Mixing enthalpy {result} is outside expected physical range"

    def test_mixing_enthalpy_symmetric(self):
        """Test that mixing enthalpy is symmetric with respect to element order."""
        comp1 = {'Fe': 0.5, 'Ni': 0.5}
        comp2 = {'Ni': 0.5, 'Fe': 0.5}
        
        result1 = calculate_mixing_enthalpy(comp1)
        result2 = calculate_mixing_enthalpy(comp2)
        
        assert np.isclose(result1, result2), "Mixing enthalpy should be symmetric"

    def test_mixing_enthalpy_pure_element(self):
        """Test that mixing enthalpy is zero for a pure element."""
        # A "pure" element technically has no mixing, but our function expects
        # a composition. For a single element with 100% abundance, 
        # the mixing enthalpy should be zero.
        composition = {'Fe': 1.0}
        result = calculate_mixing_enthalpy(composition)
        
        # For a single component, there are no pairs, so enthalpy is 0
        assert np.isclose(result, 0.0), "Mixing enthalpy for pure element should be 0"

    def test_mixing_enthalpy_invalid_element(self):
        """Test that mixing enthalpy raises error for invalid element."""
        # This should fail gracefully if we try to use an invalid element
        # The function should raise a KeyError or ValueError for unknown elements
        composition = {'InvalidElement': 1.0}
        
        with pytest.raises((KeyError, ValueError)):
            calculate_mixing_enthalpy(composition)

    def test_mixing_enthalpy_normalization(self):
        """Test that composition fractions are normalized if they don't sum to 1."""
        # Input sums to 2.0
        composition = {'Fe': 1.0, 'Ni': 1.0}
        
        # Should normalize internally and produce same result as 0.5/0.5
        result = calculate_mixing_enthalpy(composition)
        expected = calculate_mixing_enthalpy({'Fe': 0.5, 'Ni': 0.5})
        
        assert np.isclose(result, expected), "Mixing enthalpy should handle unnormalized input"

class TestAtomicSizeMismatch:
    """Tests for the calculate_atomic_size_mismatch function."""

    def test_atomic_size_mismatch_basic(self):
        """Test atomic size mismatch for a simple binary system."""
        composition = {'Fe': 0.5, 'Ni': 0.5}
        result = calculate_atomic_size_mismatch(composition)
        
        assert isinstance(result, float), "Atomic size mismatch should be a float"
        assert result >= 0, "Atomic size mismatch should be non-negative"

    def test_atomic_size_mismatch_single_element(self):
        """Test that atomic size mismatch is zero for a single element."""
        composition = {'Fe': 1.0}
        result = calculate_atomic_size_mismatch(composition)
        
        assert np.isclose(result, 0.0), "Atomic size mismatch for pure element should be 0"

class TestElectronegativityVariance:
    """Tests for the calculate_electronegativity_variance function."""

    def test_electronegativity_variance_basic(self):
        """Test electronegativity variance for a simple binary system."""
        composition = {'C': 0.5, 'Fe': 0.5}
        result = calculate_electronegativity_variance(composition)
        
        assert isinstance(result, float), "Electronegativity variance should be a float"
        assert result >= 0, "Electronegativity variance should be non-negative"

    def test_electronegativity_variance_single_element(self):
        """Test that electronegativity variance is zero for a single element."""
        composition = {'Fe': 1.0}
        result = calculate_electronegativity_variance(composition)
        
        assert np.isclose(result, 0.0), "Electronegativity variance for pure element should be 0"

class TestParseComposition:
    """Tests for the parse_composition function."""

    def test_parse_composition_valid(self):
        """Test parsing of a valid composition string."""
        comp_str = "Cu60Zr30Al10"
        result = parse_composition(comp_str)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'Cu' in result and 'Zr' in result and 'Al' in result
        assert abs(result['Cu'] - 0.60) < 1e-6
        assert abs(result['Zr'] - 0.30) < 1e-6
        assert abs(result['Al'] - 0.10) < 1e-6

    def test_parse_composition_invalid(self):
        """Test that invalid composition strings raise an error."""
        with pytest.raises(ValueError):
            parse_composition("InvalidComposition")

    def test_parse_composition_empty(self):
        """Test that empty composition string raises an error."""
        with pytest.raises(ValueError):
            parse_composition("")

class TestGetElementPropertiesSafe:
    """Tests for the get_element_properties_safe function."""

    def test_get_element_properties_safe_valid(self):
        """Test retrieving properties for a valid element."""
        props = get_element_properties_safe("Fe")
        
        assert isinstance(props, dict), "Properties should be a dictionary"
        assert 'atomic_radius' in props
        assert 'electronegativity' in props
        assert 'melting_point' in props

    def test_get_element_properties_safe_invalid(self):
        """Test that invalid element symbol raises an error."""
        with pytest.raises(ValueError):
            get_element_properties_safe("InvalidElement")