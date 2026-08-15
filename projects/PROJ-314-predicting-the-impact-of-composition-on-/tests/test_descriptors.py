"""
Unit tests for descriptor computation functions.
"""
import pytest
import pandas as pd
import numpy as np
from code.descriptors import (
    compute_valence_electron_concentration,
    compute_mean_atomic_radius,
    compute_electronegativity_std,
    compute_cation_size_variance,
    compute_range_uncertainty,
    compute_descriptors
)

def test_compute_valence_electron_concentration_al2o3():
    """
    Test VEC calculation for Al2O3.
    Al: Group 13 -> 3 valence electrons.
    O: Group 16 -> 6 valence electrons.
    Formula: Al2O3
    Total valence = (2 * 3) + (3 * 6) = 6 + 18 = 24
    Total atoms = 2 + 3 = 5
    VEC = 24 / 5 = 4.8
    """
    result = compute_valence_electron_concentration("Al2O3")
    expected = 4.8
    assert np.isclose(result, expected, rtol=1e-5), f"Expected {expected}, got {result}"

def test_compute_valence_electron_concentration_sio2():
    """
    Test VEC calculation for SiO2.
    Si: Group 14 -> 4 valence electrons.
    O: Group 16 -> 6 valence electrons.
    Formula: SiO2
    Total valence = (1 * 4) + (2 * 6) = 4 + 12 = 16
    Total atoms = 1 + 2 = 3
    VEC = 16 / 3 = 5.333...
    """
    result = compute_valence_electron_concentration("SiO2")
    expected = 16.0 / 3.0
    assert np.isclose(result, expected, rtol=1e-5), f"Expected {expected}, got {result}"

def test_compute_valence_electron_concentration_mgo():
    """
    Test VEC calculation for MgO.
    Mg: Group 2 -> 2 valence electrons.
    O: Group 16 -> 6 valence electrons.
    Formula: MgO
    Total valence = (1 * 2) + (1 * 6) = 8
    Total atoms = 2
    VEC = 8 / 2 = 4.0
    """
    result = compute_valence_electron_concentration("MgO")
    expected = 4.0
    assert np.isclose(result, expected, rtol=1e-5), f"Expected {expected}, got {result}"

def test_compute_valence_electron_concentration_invalid():
    """
    Test VEC calculation for invalid composition.
    """
    result = compute_valence_electron_concentration("Invalid")
    assert result == 0.0, f"Expected 0.0 for invalid input, got {result}"

def test_compute_mean_atomic_radius():
    """
    Test mean atomic radius calculation.
    """
    # Just check it runs and returns a number
    result = compute_mean_atomic_radius("Al2O3")
    assert isinstance(result, float), "Result should be a float"
    assert result > 0, "Radius should be positive"

def test_compute_electronegativity_std():
    """
    Test electronegativity std calculation.
    """
    result = compute_electronegativity_std("Al2O3")
    assert isinstance(result, float), "Result should be a float"
    assert result >= 0, "Std should be non-negative"

def test_compute_cation_size_variance():
    """
    Test cation size variance calculation.
    """
    result = compute_cation_size_variance("Al2O3")
    assert isinstance(result, float), "Result should be a float"
    assert result >= 0, "Variance should be non-negative"

def test_compute_range_uncertainty():
    """
    Test range uncertainty calculation.
    """
    result = compute_range_uncertainty("1000-1200")
    # Midpoint = 1100, Range = 200, Uncertainty = 100
    # Relative = 100 / 1100 = 0.0909...
    expected = 100.0 / 1100.0
    assert np.isclose(result, expected, rtol=1e-5), f"Expected {expected}, got {result}"

def test_compute_range_uncertainty_single_value():
    """
    Test range uncertainty for single value (no range).
    """
    result = compute_range_uncertainty("1100")
    assert result == 0.0, f"Expected 0.0 for single value, got {result}"

def test_compute_descriptors_dataframe():
    """
    Test compute_descriptors function with a DataFrame.
    """
    data = {
        'composition': ['Al2O3', 'SiO2', 'MgO'],
        'weibull_modulus': [10.0, 5.0, 15.0],
        'range_original': ['1000-1200', '1500', '1300-1400']
    }
    df = pd.DataFrame(data)
    
    result_df = compute_descriptors(df)
    
    assert 'valence_electron_concentration' in result_df.columns
    assert 'mean_atomic_radius' in result_df.columns
    assert 'electronegativity_std' in result_df.columns
    assert 'range_uncertainty' in result_df.columns
    
    # Check specific values
    assert np.isclose(result_df.loc[0, 'valence_electron_concentration'], 4.8)
    assert np.isclose(result_df.loc[1, 'valence_electron_concentration'], 16.0/3.0)
    assert np.isclose(result_df.loc[2, 'valence_electron_concentration'], 4.0)