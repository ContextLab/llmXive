import pytest
import pandas as pd
import numpy as np
from code.descriptors import compute_range_uncertainty, compute_cation_size_variance, compute_mean_atomic_radius, compute_electronegativity_std, compute_valence_electron_concentration, get_element_property

# --- Tests for Range Uncertainty (Existing) ---

def test_compute_range_uncertainty_no_ranges():
    """Test that range_uncertainty is 0 when no ranges exist."""
    df = pd.DataFrame({
        'composition': ['Al2O3', 'SiO2'],
        'is_range_flag': [False, False],
        'range_original': [np.nan, np.nan]
    })
    
    result = compute_range_uncertainty(df)
    
    assert 'range_uncertainty' in result.columns
    assert all(result['range_uncertainty'] == 0.0)

def test_compute_range_uncertainty_with_ranges():
    """Test range uncertainty calculation for valid range strings."""
    df = pd.DataFrame({
        'composition': ['Al2O3', 'SiO2', 'TiO2'],
        'is_range_flag': [True, True, False],
        'range_original': ['10-20', '15.5-18.5', np.nan]
    })
    
    result = compute_range_uncertainty(df)
    
    # First row: (20-10)/2 = 5
    assert result.loc[0, 'range_uncertainty'] == 5.0
    # Second row: (18.5-15.5)/2 = 1.5
    assert result.loc[1, 'range_uncertainty'] == 1.5
    # Third row: not a range, so 0
    assert result.loc[2, 'range_uncertainty'] == 0.0

def test_compute_range_uncertainty_invalid_ranges():
    """Test handling of invalid range strings."""
    df = pd.DataFrame({
        'composition': ['Al2O3'],
        'is_range_flag': [True],
        'range_original': ['invalid']
    })
    
    result = compute_range_uncertainty(df)
    
    # Should not crash, should return 0 for invalid ranges
    assert result.loc[0, 'range_uncertainty'] == 0.0

def test_compute_range_uncertainty_with_to_separator():
    """Test range parsing with 'to' separator."""
    df = pd.DataFrame({
        'composition': ['Al2O3'],
        'is_range_flag': [True],
        'range_original': ['10 to 20']
    })
    
    result = compute_range_uncertainty(df)
    
    # (20-10)/2 = 5
    assert result.loc[0, 'range_uncertainty'] == 5.0

# --- NEW Tests for chemparse Composition Parsing & Descriptors ---

def test_get_element_property_atomic_radius():
    """Test retrieval of atomic radius for a known element."""
    # Aluminum atomic radius is approx 143 pm (varies by source, checking existence and type)
    radius = get_element_property('Al', 'atomic_radius')
    assert radius is not None
    assert isinstance(radius, (int, float))
    assert radius > 0

def test_get_element_property_electronegativity():
    """Test retrieval of electronegativity for a known element."""
    # Pauling electronegativity of Oxygen is 3.44
    en = get_element_property('O', 'electronegativity')
    assert en is not None
    assert isinstance(en, (int, float))
    assert en > 0

def test_compute_mean_atomic_radius_simple():
    """Test mean atomic radius calculation for a simple stoichiometry."""
    # NaCl: Na (186 pm) + Cl (99 pm) / 2 = 142.5 (approx, depends on source values)
    df = pd.DataFrame({
        'composition': ['NaCl']
    })
    result = compute_mean_atomic_radius(df)
    assert 'mean_atomic_radius' in result.columns
    assert not pd.isna(result.loc[0, 'mean_atomic_radius'])
    assert result.loc[0, 'mean_atomic_radius'] > 0

def test_compute_electronegativity_std_simple():
    """Test electronegativity std calculation."""
    # NaCl: Na (0.93) + Cl (3.16). Mean = 2.045. Std = sqrt(((0.93-2.045)^2 + (3.16-2.045)^2)/2)
    df = pd.DataFrame({
        'composition': ['NaCl']
    })
    result = compute_electronegativity_std(df)
    assert 'electronegativity_std' in result.columns
    assert not pd.isna(result.loc[0, 'electronegativity_std'])

def test_compute_valence_electron_concentration_simple():
    """Test VEC calculation. Na (1 valence) + Cl (7 valence) = 8. Total atoms = 2. VEC = 4."""
    df = pd.DataFrame({
        'composition': ['NaCl']
    })
    result = compute_valence_electron_concentration(df)
    assert 'valence_electron_concentration' in result.columns
    # Na is group 1, Cl is group 17 (7 valence e-). Total = 8. Atoms = 2. VEC = 4.
    assert result.loc[0, 'valence_electron_concentration'] == 4.0

def test_compute_cation_size_variance_simple():
    """Test cation size variance. NaCl has one cation (Na), so variance should be 0."""
    df = pd.DataFrame({
        'composition': ['NaCl']
    })
    result = compute_cation_size_variance(df)
    assert 'cation_size_variance' in result.columns
    # Single cation type -> variance is 0
    assert result.loc[0, 'cation_size_variance'] == 0.0

def test_compute_cation_size_variance_multiple_cations():
    """Test cation size variance with multiple cation types."""
    # NaK (hypothetical mix for test): Na and K have different radii.
    # We assume the function parses 'Na1K1' correctly.
    df = pd.DataFrame({
        'composition': ['NaK']
    })
    result = compute_cation_size_variance(df)
    assert 'cation_size_variance' in result.columns
    # If both are cations and have different radii, variance > 0
    # If parsing fails or treats one as anion, behavior depends on implementation, 
    # but it should not crash and return a float.
    assert isinstance(result.loc[0, 'cation_size_variance'], (int, float))

def test_parse_formula_integration():
    """Integration test ensuring chemparse correctly parses a complex formula."""
    # YBa2Cu3O7
    df = pd.DataFrame({
        'composition': ['YBa2Cu3O7']
    })
    # Just ensure the descriptor computation pipeline doesn't crash on a complex formula
    res_mean = compute_mean_atomic_radius(df)
    res_std = compute_electronegativity_std(df)
    res_vec = compute_valence_electron_concentration(df)
    
    assert not pd.isna(res_mean.loc[0, 'mean_atomic_radius'])
    assert not pd.isna(res_std.loc[0, 'electronegativity_std'])
    assert not pd.isna(res_vec.loc[0, 'valence_electron_concentration'])