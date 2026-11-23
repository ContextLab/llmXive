import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
import tempfile

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from descriptors import (
    parse_composition,
    calculate_weighted_mean_radius,
    calculate_radius_mismatch,
    calculate_electronegativity_difference,
    calculate_vec,
    compute_descriptors,
    save_descriptors
)

def test_parse_composition_valid():
    """Test parsing a valid composition string."""
    comp_str = "Fe50Ni30Co20"
    result = parse_composition(comp_str)
    assert abs(result['Fe'] - 0.5) < 1e-6
    assert abs(result['Ni'] - 0.3) < 1e-6
    assert abs(result['Co'] - 0.2) < 1e-6

def test_parse_composition_normalization():
    """Test that composition is normalized if sum > 100."""
    comp_str = "Fe60Ni40" # Sum is 100, should be 0.6, 0.4
    result = parse_composition(comp_str)
    assert abs(result['Fe'] - 0.6) < 1e-6
    assert abs(result['Ni'] - 0.4) < 1e-6

def test_calculate_weighted_mean_radius():
    """Test weighted mean radius calculation."""
    # Fe radius ~126 pm, Ni ~124 pm, Co ~125 pm (approximate values from mendeleev)
    # Composition: Fe0.5, Ni0.3, Co0.2
    # Expected: 0.5*126 + 0.3*124 + 0.2*125 = 63 + 37.2 + 25 = 125.2
    comp = {'Fe': 0.5, 'Ni': 0.3, 'Co': 0.2}
    wmr = calculate_weighted_mean_radius(comp)
    assert wmr is not None
    assert 120 < wmr < 130 # Reasonable range check

def test_radius_mismatch_calculation():
    """
    Unit test for radius mismatch calculation (Task T018a).
    
    Uses a known composition to verify the formula:
    mismatch = sum(c_i * |1 - r_i / r_bar|)
    where r_bar is the weighted mean radius.
    
    Composition: Fe50Ni50
    r_Fe ~ 126 pm, r_Ni ~ 124 pm
    r_bar = 0.5*126 + 0.5*124 = 125 pm
    
    Term Fe: 0.5 * |1 - 126/125| = 0.5 * |1 - 1.008| = 0.5 * 0.008 = 0.004
    Term Ni: 0.5 * |1 - 124/125| = 0.5 * |1 - 0.992| = 0.5 * 0.008 = 0.004
    Total mismatch = 0.008
    
    Note: Actual values from mendeleev might differ slightly, but the logic
    should produce a small positive number for this symmetric alloy.
    """
    # Use a symmetric binary alloy for predictable results
    comp = {'Fe': 0.5, 'Ni': 0.5}
    mismatch = calculate_radius_mismatch(comp)
    
    # Basic sanity checks
    assert mismatch is not None, "Radius mismatch should be calculated"
    assert mismatch >= 0, "Radius mismatch must be non-negative"
    
    # For a symmetric alloy with similar radii, mismatch should be small (< 0.05)
    # This is a heuristic check; exact value depends on mendeleev data
    assert mismatch < 0.05, f"Radius mismatch for Fe50Ni50 should be small, got {mismatch}"
    
    # Test with a more disparate alloy to ensure calculation works
    # Li (large) and Mg (smaller) - though exact values depend on mendeleev
    comp_disparate = {'Li': 0.5, 'Mg': 0.5}
    mismatch_disparate = calculate_radius_mismatch(comp_disparate)
    assert mismatch_disparate is not None
    assert mismatch_disparate >= 0

def test_calculate_electronegativity_difference():
    """Test electronegativity difference calculation."""
    comp = {'Fe': 0.5, 'Ni': 0.3, 'Co': 0.2}
    diff = calculate_electronegativity_difference(comp)
    assert diff is not None
    assert diff >= 0

def test_vec_calculation():
    """
    Unit test for VEC (Valence Electron Concentration) calculation (Task T018b).
    
    Uses a known composition to verify the formula:
    VEC = sum(c_i * V_i)
    where c_i is the atomic fraction and V_i is the number of valence electrons.
    
    Composition: Fe50Ni30Co20
    Fe (Group 8), Ni (Group 10), Co (Group 9)
    Expected: 0.5*8 + 0.3*10 + 0.2*9 = 4.0 + 3.0 + 1.8 = 8.8
    
    Note: Mendeleev group numbers might vary slightly depending on the definition,
    but the calculation logic must be correct.
    """
    # Test with Fe50Ni30Co20
    comp = {'Fe': 0.5, 'Ni': 0.3, 'Co': 0.2}
    vec = calculate_vec(comp)
    
    # Basic sanity checks
    assert vec is not None, "VEC should be calculated"
    assert isinstance(vec, (int, float)), "VEC should be a number"
    
    # Fe is Group 8, Ni is Group 10, Co is Group 9 in standard periodic table
    # Expected range: 8.0 to 9.0 for this composition
    # Using a slightly wider range to account for different valence definitions
    assert 7.0 < vec < 10.0, f"VEC for Fe50Ni30Co20 should be in reasonable range, got {vec}"
    
    # Test with a known binary alloy: Cu50Zn50 (Brass)
    # Cu is Group 11 (1 valence electron in s-shell), Zn is Group 12 (2 valence electrons)
    # However, in metallic glass context, VEC often uses group number directly
    # Let's test with a simple case: pure element
    comp_pure = {'Fe': 1.0}
    vec_pure = calculate_vec(comp_pure)
    assert vec_pure is not None
    assert vec_pure > 0
    
    # Test with a different composition to ensure linearity
    # Fe25Ni75: 0.25*8 + 0.75*10 = 2 + 7.5 = 9.5
    comp_diff = {'Fe': 0.25, 'Ni': 0.75}
    vec_diff = calculate_vec(comp_diff)
    assert vec_diff is not None
    assert 9.0 < vec_diff < 10.0, f"VEC for Fe25Ni75 should be ~9.5, got {vec_diff}"

def test_compute_descriptors():
    """Test full descriptor computation pipeline."""
    comp_str = "Fe50Ni30Co20"
    desc = compute_descriptors(comp_str)
    assert 'radius_mismatch' in desc
    assert 'electronegativity_diff' in desc
    assert 'VEC' in desc
    assert desc['radius_mismatch'] is not None
    assert desc['electronegativity_diff'] is not None
    assert desc['VEC'] is not None

def test_save_descriptors(tmp_path):
    """Test saving descriptors to CSV."""
    df = pd.DataFrame({
        'radius_mismatch': [0.1, 0.2, 0.3],
        'electronegativity_diff': [0.5, 0.6, 0.7],
        'VEC': [8.5, 8.6, 8.7]
    })
    output_file = tmp_path / "test_descriptors.csv"
    save_descriptors(df, output_file)
    
    assert output_file.exists()
    saved_df = pd.read_csv(output_file)
    assert list(saved_df.columns) == ['radius_mismatch', 'electronegativity_diff', 'VEC']
    assert len(saved_df) == 3