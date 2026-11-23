"""
Tests for T020: Correlation Analysis and Modulation Amplitude Derivation.
"""
import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.correlation import (
    calculate_lagged_correlations, 
    calculate_rigidity_bin_correlations, 
    sinusoidal_model
)
from code.utils.config import CONFIG

@pytest.fixture
def mock_unified_data():
    """Generate mock unified timeseries data."""
    dates = pd.date_range(start='2011-01-01', end='2024-01-01', freq='D')
    n = len(dates)
    
    # Create synthetic solar cycle (sin wave)
    t = np.arange(n)
    solar_cycle = 100 * np.sin(2 * np.pi * t / (11 * 365)) + 50
    solar_cycle = np.clip(solar_cycle, 0, 200)
    
    # Create fluxes correlated with solar cycle (anti-correlated for cosmic rays)
    proton_flux = 1000 * (1 - 0.1 * np.sin(2 * np.pi * t / (11 * 365))) + np.random.normal(0, 10, n)
    helium_flux = 200 * (1 - 0.1 * np.sin(2 * np.pi * t / (11 * 365))) + np.random.normal(0, 5, n)
    heavy_flux = 50 * (1 - 0.1 * np.sin(2 * np.pi * t / (11 * 365))) + np.random.normal(0, 2, n)
    
    # Calculate ratios
    he_p = helium_flux / proton_flux
    fe_p = heavy_flux / proton_flux
    
    # Create multiple rigidity bins (simulate by slicing)
    bins = [1.0, 5.0, 10.0]
    rows = []
    for i, date in enumerate(dates):
        for b in bins:
            rows.append({
                'date': date,
                'rigidity_bin': b,
                'proton_flux': proton_flux[i],
                'helium_flux': helium_flux[i],
                'heavy_flux': heavy_flux[i],
                'sunspot_number': int(solar_cycle[i]),
                'He_p_ratio': he_p[i],
                'Fe_p_ratio': fe_p[i]
            })
    
    return pd.DataFrame(rows)

def test_calculate_lagged_correlations(mock_unified_data):
    """Test basic lagged correlation calculation."""
    # Filter for one bin
    data = mock_unified_data[mock_unified_data['rigidity_bin'] == 1.0]
    
    results = calculate_lagged_correlations(data, 'He_p_ratio', 'sunspot_number', max_lag_months=2)
    
    assert isinstance(results, dict)
    assert -2 in results
    assert 0 in results
    assert 2 in results
    
    # Check structure
    for lag, res in results.items():
        assert 'coefficient' in res
        assert 'p_value' in res

def test_sinusoidal_model():
    """Test the sinusoidal model function."""
    t = np.linspace(0, 10, 100)
    A, phi, T, C = 5, 0, 10, 10
    y = sinusoidal_model(t, A, phi, T, C)
    
    # Check amplitude (peak-to-trough should be 2*A = 10)
    peak = np.max(y)
    trough = np.min(y)
    assert np.isclose(peak - trough, 10, atol=0.5)
    
    # Check offset
    assert np.isclose(np.mean(y), C, atol=1)

def test_calculate_rigidity_bin_correlations(mock_unified_data):
    """Test full correlation pipeline including amplitude derivation."""
    results, amp_df = calculate_rigidity_bin_correlations(mock_unified_data)
    
    # Check results list
    assert len(results) > 0
    
    # Check schema of results
    required_keys = ['rigidity_bin', 'metric_type', 'metric_name', 'correlation_coefficient', 'p_value']
    for res in results:
        for key in required_keys:
            assert key in res
    
    # Check amplitude dataframe
    assert not amp_df.empty
    assert 'rigidity_bin' in amp_df.columns
    assert 'amplitude' in amp_df.columns
    assert 'method' in amp_df.columns
    
    # Verify amplitudes are positive
    assert (amp_df['amplitude'] > 0).all() or amp_df['amplitude'].isna().all()

def test_modulation_amplitude_schema(mock_unified_data):
    """Verify the output schema for modulation_amplitudes_baseline.csv matches T020 requirements."""
    _, amp_df = calculate_rigidity_bin_correlations(mock_unified_data)
    
    # T020 Requirement: Columns must be rigidity_bin, amplitude, method
    expected_cols = {'rigidity_bin', 'amplitude', 'method'}
    assert set(amp_df.columns) == expected_cols
    
    # Check data types
    assert amp_df['rigidity_bin'].dtype in [np.float64, np.float32, int]
    assert amp_df['amplitude'].dtype in [np.float64, np.float32]
    assert amp_df['method'].dtype == object

if __name__ == "__main__":
    pytest.main([__file__, "-v"])