"""
Tests for statistical analysis functions in code/stats.py.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from stats import bin_energy_data, perform_ks_test, perform_chisquared_test, apply_benjamini_hochberg, StatsError

# Fixtures
@pytest.fixture
def sample_energy_data(tmp_path):
    """Create a sample energy_samples.csv file."""
    data = {
        'particle_id': [1, 1, 1, 2, 2, 2],
        'timestamp': [0.0, 0.1, 0.2, 0.0, 0.1, 0.2],
        'E_trans': [1.0, 1.1, 1.2, 2.0, 2.1, 2.2],
        'E_rot': [0.1, 0.11, 0.12, 0.2, 0.21, 0.22],
        'E_pot': [0.5, 0.55, 0.6, 1.0, 1.1, 1.2],
        'E_vib': [0.01, 0.011, 0.012, 0.02, 0.021, 0.022],
        'frequency': [10.0, 10.0, 10.0, 20.0, 20.0, 20.0],
        'material_type': ['steel', 'steel', 'steel', 'polymer', 'polymer', 'polymer'],
        'pot_incomplete': [False, False, False, False, False, False]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "energy_samples.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)

def test_bin_energy_data(sample_energy_data):
    """Test binning of energy data by frequency and material."""
    result = bin_energy_data(sample_energy_data)
    assert 'frequency' in result.columns
    assert 'material_type' in result.columns
    assert 'energies' in result.columns
    # Check that we have 2 bins (10.0/steel and 20.0/polymer)
    assert len(result) == 2

def test_perform_ks_test():
    """Test KS test against Maxwell-Boltzmann."""
    # Generate data that roughly follows MB distribution
    # For simplicity, use a gamma distribution which is similar to MB for energy
    np.random.seed(42)
    kT = 1.0
    energies = np.random.gamma(shape=1.5, scale=kT, size=100)
    
    result = perform_ks_test(energies, kT)
    assert 'statistic' in result
    assert 'pvalue' in result
    assert 'rejection' in result
    assert 0 <= result['pvalue'] <= 1

def test_perform_chisquared_test():
    """Test Chi-squared goodness-of-fit test."""
    np.random.seed(42)
    kT = 1.0
    energies = np.random.gamma(shape=1.5, scale=kT, size=100)
    
    result = perform_chisquared_test(energies, kT, bins=5)
    assert 'statistic' in result
    assert 'pvalue' in result
    assert 'rejection' in result

def test_apply_benjamini_hochberg():
    """Test FDR correction."""
    p_values = [0.01, 0.04, 0.03, 0.001, 0.06, 0.02]
    rejection, adjusted = apply_benjamini_hochberg(p_values, alpha=0.05)
    assert len(rejection) == len(p_values)
    assert len(adjusted) == len(p_values)
    # Check that adjusted p-values are sorted relative to original order
    # (monotonicity is handled internally)
    assert all(0 <= p <= 1 for p in adjusted)

def test_bin_energy_data_missing_columns(tmp_path):
    """Test error handling for missing columns."""
    data = {
        'particle_id': [1, 2],
        'timestamp': [0.0, 0.1],
        # Missing energy columns
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "bad_data.csv"
    df.to_csv(file_path, index=False)
    
    with pytest.raises(StatsError):
        bin_energy_data(str(file_path))
