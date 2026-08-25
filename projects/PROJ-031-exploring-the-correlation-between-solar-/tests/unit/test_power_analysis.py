"""
Unit tests for power analysis functionality in code/analysis.py.
"""
import pytest
import pandas as pd
import numpy as np
from code.analysis import power_analysis, run_correlation_analysis
import json
import os
import tempfile

def test_power_analysis_calculation():
    """Test that power_analysis returns reasonable MDES values."""
    # Large sample should yield small MDES
    mdes_large = power_analysis(n=1000)
    assert 0.0 < mdes_large < 0.2, f"Large sample MDES should be small, got {mdes_large}"
    
    # Small sample should yield large MDES
    mdes_small = power_analysis(n=20)
    assert mdes_small > 0.4, f"Small sample MDES should be large, got {mdes_small}"
    
    # Edge case: n=1
    mdes_one = power_analysis(n=1)
    assert mdes_one == 1.0, f"n=1 should return MDES=1.0, got {mdes_one}"

def test_power_limitation_in_metrics():
    """Test that power limitation is recorded when N < 30."""
    # Create a small synthetic dataset
    df_small = pd.DataFrame({
        'event_date': pd.date_range('2010-01-01', periods=20, freq='D'),
        'flare_flux': np.random.uniform(1e-8, 1e-4, 20),
        'cme_speed': np.random.uniform(300, 2000, 20),
        'dst_min': np.random.uniform(-200, -50, 20)
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_path = os.path.join(tmpdir, 'metrics.json')
        results = run_correlation_analysis(df_small, metrics_path)
        
        assert 'power_limitation' in results
        assert results['power_limitation'] is not None
        assert 'warning' in results['power_limitation']
        assert 'implication' in results['power_limitation']
        assert results['sample_size'] == 20

def test_no_power_limitation_when_n_large():
    """Test that power limitation is None when N >= 30."""
    # Create a larger synthetic dataset
    df_large = pd.DataFrame({
        'event_date': pd.date_range('2010-01-01', periods=50, freq='D'),
        'flare_flux': np.random.uniform(1e-8, 1e-4, 50),
        'cme_speed': np.random.uniform(300, 2000, 50),
        'dst_min': np.random.uniform(-200, -50, 50)
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_path = os.path.join(tmpdir, 'metrics.json')
        results = run_correlation_analysis(df_large, metrics_path)
        
        assert 'power_limitation' in results
        assert results['power_limitation'] is None
        assert results['sample_size'] == 50

def test_mdes_in_results():
    """Test that MDES is included in results."""
    df = pd.DataFrame({
        'event_date': pd.date_range('2010-01-01', periods=40, freq='D'),
        'flare_flux': np.random.uniform(1e-8, 1e-4, 40),
        'cme_speed': np.random.uniform(300, 2000, 40),
        'dst_min': np.random.uniform(-200, -50, 40)
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_path = os.path.join(tmpdir, 'metrics.json')
        results = run_correlation_analysis(df, metrics_path)
        
        assert 'mdes' in results
        assert 0 < results['mdes'] < 1
        assert 'sample_size' in results
        assert results['sample_size'] == 40
