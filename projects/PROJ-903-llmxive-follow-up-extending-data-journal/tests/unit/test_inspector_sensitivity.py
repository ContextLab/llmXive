import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from narrative.inspector import run_sensitivity_analysis, get_baseline_drivers, compute_partial_correlation

def test_compute_partial_correlation():
    """Test partial correlation computation with synthetic data."""
    np.random.seed(42)
    n = 100
    x = np.random.randn(n)
    y = np.random.randn(n)
    z = np.random.randn(n)
    
    # Create a DataFrame
    df = pd.DataFrame({'x': x, 'y': y, 'z': z})
    
    # Compute partial correlation of x and y controlling for z
    r, p = compute_partial_correlation(df, 'x', 'y', ['z'])
    
    # With random data, correlation should be low
    assert abs(r) < 0.5
    assert 0 <= p <= 1

def test_get_baseline_drivers():
    """Test extraction of baseline drivers."""
    baseline = {
        'primary_narrative': 'test',
        'var_x': 'A',
        'var_y': 'B',
        'r_value': 0.5,
        'p_value': 0.01
    }
    drivers = get_baseline_drivers(baseline)
    assert 'A' in drivers
    assert 'B' in drivers
    assert len(drivers) == 2

def test_sensitivity_analysis_schema():
    """Test that sensitivity analysis output matches mandatory schema."""
    # Create a small mock dataset
    np.random.seed(42)
    n = 50
    df = pd.DataFrame({
        'A': np.random.randn(n),
        'B': np.random.randn(n),
        'C': np.random.randn(n),
        'D': np.random.randn(n)
    })
    
    baseline_result = {
        'primary_narrative': 'A correlates with B',
        'var_x': 'A',
        'var_y': 'B',
        'r_value': 0.8,
        'p_value': 0.001
    }
    
    candidates = ['C', 'D']
    
    results = run_sensitivity_analysis(df, baseline_result, candidates)
    
    assert isinstance(results, list)
    assert len(results) > 0
    
    # Check schema for each result
    for item in results:
        assert 'threshold_config' in item
        assert 'claim' in item
        assert 'p_value' in item
        assert 'partial_r' in item
        
        assert isinstance(item['threshold_config'], str)
        assert isinstance(item['claim'], str)
        assert isinstance(item['p_value'], float)
        assert isinstance(item['partial_r'], float)
        
        # Check validity logic in claim
        p_val = item['p_value']
        r_val = item['partial_r']
        config = item['threshold_config']
        
        # Parse config to check validity (simple check)
        # Config format: "p<0.05, |r|>0.15"
        if "NO_SIGNIFICANT_COUNTERFACTUAL" in item['claim']:
            # Should be invalid
            pass
        else:
            # Should be valid
            assert p_val < 0.05
            assert abs(r_val) > 0.15

def test_sensitivity_analysis_empty_candidates():
    """Test sensitivity analysis with no candidates."""
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [1, 2, 3]})
    baseline = {'primary_narrative': 'test', 'var_x': 'A', 'var_y': 'B'}
    
    results = run_sensitivity_analysis(df, baseline, [])
    assert results == []
