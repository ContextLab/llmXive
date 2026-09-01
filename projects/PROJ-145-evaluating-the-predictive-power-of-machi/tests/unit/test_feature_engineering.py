"""
Unit tests for feature engineering logic.
"""

import pytest
import numpy as np
from code.feature_engineering import calculate_compositional_descriptors, get_element_property

def test_weighted_mean_calculation():
    """
    Test that weighted mean is calculated correctly.
    Example: 50% Fe (radius ~126) + 50% Ni (radius ~124) -> Mean ~125
    """
    # Using a known simple composition: Fe0.5Ni0.5
    desc = calculate_compositional_descriptors("Fe0.5Ni0.5")
    
    # Check keys exist
    assert "mean_atomic_radius" in desc
    assert "var_atomic_radius" in desc
    
    # Verify logic (approximate values from periodic table)
    # Fe radius ~ 126 pm, Ni radius ~ 124 pm
    # Mean should be roughly 125
    mean_radius = desc["mean_atomic_radius"]
    assert 120 < mean_radius < 130, f"Expected radius ~125, got {mean_radius}"

def test_variance_calculation():
    """
    Test that variance is non-zero for mixed elements.
    """
    desc = calculate_compositional_descriptors("Fe0.5Ni0.5")
    # Variance should be > 0 if elements are different
    assert desc["var_atomic_radius"] > 0

def test_variance_clamping():
    """
    Test that near-zero variance is clamped to MIN_THRESHOLD.
    Using a single element or identical elements.
    """
    # Pure Fe should have 0 variance theoretically, but our code clamps it
    desc = calculate_compositional_descriptors("Fe")
    assert desc["var_atomic_radius"] >= 1e-6, "Variance should be clamped to minimum threshold"

def test_invalid_composition():
    """
    Test that invalid composition strings raise an error.
    """
    with pytest.raises(ValueError):
        calculate_compositional_descriptors("InvalidElement123")

def test_element_property_fetch():
    """
    Test fetching specific element properties.
    """
    # Test VEC for Iron (Fe is Group 8, usually 8 valence electrons)
    vec_fe = get_element_property("Fe", "VEC")
    assert vec_fe == 8.0, f"Expected VEC 8 for Fe, got {vec_fe}"
    
    # Test Electronegativity
    en_fe = get_element_property("Fe", "electronegativity")
    assert en_fe > 0, "Electronegativity should be positive"

def test_composition_parsing_variants():
    """
    Test different composition string formats supported by pymatgen.
    """
    # Standard stoichiometry
    desc1 = calculate_compositional_descriptors("Fe0.2Co0.2Ni0.2Cr0.2Mn0.2")
    
    # Integer ratios (pymatgen normalizes)
    desc2 = calculate_compositional_descriptors("FeCoNiCrMn")
    
    # Both should produce same mean/var for the same relative proportions
    np.testing.assert_almost_equal(desc1["mean_atomic_radius"], desc2["mean_atomic_radius"])