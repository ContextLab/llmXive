import pytest
import pandas as pd
import numpy as np
from code.data.preprocessing import calculate_energy_density, verify_column_integrity

def test_placeholder_preprocessing():
    """Placeholder test to ensure the test file is valid."""
    assert True

def test_energy_density_calculation():
    """Test that energy density is calculated correctly."""
    data = {
        'laser_power': [200.0, 300.0],
        'scan_speed': [1000.0, 1000.0],
        'hatch_spacing': [0.1, 0.1],
        'layer_thickness': [0.05, 0.05],
        'ductility': [5.0, 6.0],
        'alloy_family': ['Inconel 718', 'Inconel 718']
    }
    df = pd.DataFrame(data)
    
    result_df = calculate_energy_density(df)
    
    # E_v = 200 / (1000 * 0.1 * 0.05) = 200 / 5 = 40
    expected_ev_0 = 40.0
    # E_v = 300 / (1000 * 0.1 * 0.05) = 300 / 5 = 60
    expected_ev_1 = 60.0
    
    assert 'energy_density' in result_df.columns
    assert np.isclose(result_df['energy_density'].iloc[0], expected_ev_0)
    assert np.isclose(result_df['energy_density'].iloc[1], expected_ev_1)

def test_energy_density_zero_denominator():
    """Test that zero denominator results in NaN and logs a warning (handled via result check)."""
    data = {
        'laser_power': [200.0],
        'scan_speed': [0.0],
        'hatch_spacing': [0.1],
        'layer_thickness': [0.05],
        'ductility': [5.0],
        'alloy_family': ['Inconel 718']
    }
    df = pd.DataFrame(data)
    
    result_df = calculate_energy_density(df)
    
    assert pd.isna(result_df['energy_density'].iloc[0])

def test_verify_column_integrity_success():
    """Test integrity check passes with all required columns."""
    data = {
        'laser_power': [200.0],
        'scan_speed': [1000.0],
        'hatch_spacing': [0.1],
        'layer_thickness': [0.05],
        'ductility': [5.0],
        'alloy_family': ['Inconel 718'],
        'energy_density': [40.0]
    }
    df = pd.DataFrame(data)
    
    assert verify_column_integrity(df) is True

def test_verify_column_integrity_failure():
    """Test integrity check fails with missing columns."""
    data = {
        'laser_power': [200.0],
        # Missing other required columns
    }
    df = pd.DataFrame(data)
    
    assert verify_column_integrity(df) is False