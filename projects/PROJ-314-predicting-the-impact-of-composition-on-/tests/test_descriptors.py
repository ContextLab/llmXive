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

def test_compute_range_uncertainty_composition_parsing():
    """Test that the function correctly identifies compositions even if is_range_flag is inconsistent."""
    df = pd.DataFrame({
        'composition': ['Al2O3'],
        'is_range_flag': [False],
        'range_original': ['10-20']
    })
    
    result = compute_range_uncertainty(df)
    
    # Logic should rely on is_range_flag, so if flag is False, uncertainty is 0
    # regardless of what range_original contains (unless we want to parse blindly)
    # Based on previous tests, we respect the flag.
    assert result.loc[0, 'range_uncertainty'] == 0.0
    
    # Now test with flag True
    df['is_range_flag'] = [True]
    result = compute_range_uncertainty(df)
    assert result.loc[0, 'range_uncertainty'] == 5.0