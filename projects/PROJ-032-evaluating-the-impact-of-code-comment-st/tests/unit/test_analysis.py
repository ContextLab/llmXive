import pytest
import numpy as np
from code.analysis import apply_fdr_correction

def test_fdr_correction_empty_dict():
    """Test FDR correction with empty p-values dictionary."""
    result = apply_fdr_correction({})
    assert result['corrected_p_values'] == {}
    assert result['is_significant'] == {}
    assert result['num_significant'] == 0
    assert result['threshold'] == 0.05

def test_fdr_correction_single_value():
    """Test FDR correction with a single p-value."""
    p_values = {'var1': 0.03}
    result = apply_fdr_correction(p_values)
    
    # With one value, BH correction should keep it as is
    assert 'var1' in result['corrected_p_values']
    assert abs(result['corrected_p_values']['var1'] - 0.03) < 1e-6
    assert result['is_significant']['var1'] == (0.03 < 0.05)
    assert result['num_significant'] == 1 if 0.03 < 0.05 else 0

def test_fdr_correction_multiple_values():
    """Test FDR correction with multiple p-values."""
    p_values = {
        'var1': 0.01,
        'var2': 0.04,
        'var3': 0.15,
        'var4': 0.20
    }
    
    result = apply_fdr_correction(p_values)
    
    # Check that all keys are present
    assert set(result['corrected_p_values'].keys()) == set(p_values.keys())
    assert set(result['is_significant'].keys()) == set(p_values.keys())
    
    # Check that corrected p-values are >= original (monotonicity)
    for var in p_values:
        assert result['corrected_p_values'][var] >= p_values[var]
    
    # Check that corrected p-values are <= 1.0
    for var in result['corrected_p_values']:
        assert result['corrected_p_values'][var] <= 1.0
    
    # Check that significant variables have corrected p < 0.05
    for var, is_sig in result['is_significant'].items():
        if is_sig:
            assert result['corrected_p_values'][var] < 0.05

def test_fdr_correction_different_alpha():
    """Test FDR correction with different alpha thresholds."""
    p_values = {
        'var1': 0.01,
        'var2': 0.04,
        'var3': 0.15
    }
    
    # Test with alpha = 0.10
    result_10 = apply_fdr_correction(p_values, alpha=0.10)
    assert result_10['threshold'] == 0.10
    
    # Test with alpha = 0.01
    result_01 = apply_fdr_correction(p_values, alpha=0.01)
    assert result_01['threshold'] == 0.01
    
    # Higher alpha should result in more or equal significant variables
    assert result_10['num_significant'] >= result_01['num_significant']

def test_fdr_correction_all_significant():
    """Test FDR correction where all p-values are very small."""
    p_values = {
        'var1': 0.001,
        'var2': 0.002,
        'var3': 0.003
    }
    
    result = apply_fdr_correction(p_values)
    assert result['num_significant'] == 3
    assert all(result['is_significant'].values())

def test_fdr_correction_none_significant():
    """Test FDR correction where all p-values are large."""
    p_values = {
        'var1': 0.8,
        'var2': 0.9,
        'var3': 0.95
    }
    
    result = apply_fdr_correction(p_values)
    assert result['num_significant'] == 0
    assert not any(result['is_significant'].values())