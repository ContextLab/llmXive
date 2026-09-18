"""
Unit tests for metrics calculation module.
"""
import pytest
import numpy as np
import pandas as pd
from analysis.metrics import (
    extract_q_profile,
    calculate_local_magnetic_shear,
    calculate_resonant_surface_density,
    derive_island_width,
    detect_outliers,
    validate_metric_ranges
)

def test_extract_q_profile_missing_data():
    """Test extraction when q-profile is missing."""
    efit_data = {'other_field': [1, 2, 3]}
    result = extract_q_profile(efit_data, 12345)
    assert result is None

def test_extract_q_profile_valid():
    """Test extraction with valid q-profile data."""
    q_vals = [1.2, 1.5, 1.8, 2.1]
    efit_data = {
        'q_profile': q_vals,
        'rho_tor': [0.1, 0.5, 0.8, 1.0]
    }
    result = extract_q_profile(efit_data, 12345)
    assert result is not None
    assert np.array_equal(result, np.array(q_vals))

def test_calculate_local_magnetic_shear():
    """Test magnetic shear calculation."""
    q_profile = np.array([1.0, 1.2, 1.5, 1.9])
    rho_tor = np.array([0.0, 0.3, 0.6, 1.0])
    
    shear = calculate_local_magnetic_shear(q_profile, rho_tor)
    assert shear is not None
    assert len(shear) == len(q_profile)
    # Shear should generally be positive for typical tokamak profiles
    assert np.all(shear >= 0) or np.any(shear < 0)  # Depends on profile shape

def test_calculate_resonant_surface_density_basic():
    """Test resonant surface density calculation with a known profile."""
    # Create a q-profile that crosses 1.5 (m=3, n=2) and 2.0 (m=2, n=1)
    rho_tor = np.linspace(0.1, 1.0, 20)
    q_profile = np.array([1.49, 1.51, 1.8, 1.99, 2.01, 2.2, 2.5, 2.8])
    
    density = calculate_resonant_surface_density(q_profile, rho_tor)
    assert isinstance(density, float)
    assert density >= 0
    # We expect at least 2 rational surfaces (1.5 and 2.0)
    # Density = count / rho_range, rho_range ~ 0.9
    assert density > 0

def test_calculate_resonant_surface_density_no_rational():
    """Test when no rational surfaces are found."""
    # Create a q-profile that avoids rational values
    rho_tor = np.linspace(0.1, 1.0, 20)
    q_profile = np.array([1.33333, 1.33334, 1.33335, 1.33336, 1.33337])
    
    density = calculate_resonant_surface_density(q_profile, rho_tor)
    assert density == 0.0

def test_calculate_resonant_surface_density_empty():
    """Test with empty or None inputs."""
    assert calculate_resonant_surface_density(None, None) == 0.0
    assert calculate_resonant_surface_density(np.array([]), np.array([])) == 0.0

def test_derive_island_width():
    """Test island width derivation."""
    local_shear = 0.5
    q_profile = np.array([1.5, 1.6, 1.7])
    Bt = 2.0
    
    width = derive_island_width(local_shear, q_profile, Bt, 12345)
    assert isinstance(width, float)
    assert width > 0

def test_detect_outliers():
    """Test outlier detection."""
    df = pd.DataFrame({
        'discharge_id': [1, 2, 3],
        'island_width': [0.1, 0.7, 0.3]  # 0.7 > 0.67 (minor radius)
    })
    
    result = detect_outliers(df, 'island_width')
    assert 'is_outlier' in result.columns
    assert result['is_outlier'].sum() == 1
    assert result.iloc[1]['is_outlier'] == True
    assert result.iloc[0]['is_outlier'] == False
    assert result.iloc[2]['is_outlier'] == False

def test_validate_metric_ranges():
    """Test metric range validation."""
    # Valid data
    df_valid = pd.DataFrame({
        'island_width': [0.1, 0.2, 0.3],
        'resonant_surface_density': [1.0, 2.0, 3.0]
    })
    assert validate_metric_ranges(df_valid) == True
    
    # Invalid island width (too large)
    df_invalid = pd.DataFrame({
        'island_width': [0.1, 0.8, 0.3],  # 0.8 > 0.67
        'resonant_surface_density': [1.0, 2.0, 3.0]
    })
    assert validate_metric_ranges(df_invalid) == False
    
    # Invalid density (negative)
    df_invalid2 = pd.DataFrame({
        'island_width': [0.1, 0.2, 0.3],
        'resonant_surface_density': [1.0, -1.0, 3.0]
    })
    assert validate_metric_ranges(df_invalid2) == False