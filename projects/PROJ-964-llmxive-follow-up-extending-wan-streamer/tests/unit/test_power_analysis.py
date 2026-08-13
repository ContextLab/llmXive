"""
Unit tests for T029b: Power Analysis Module.
"""
import os
import sys
import json
import pytest
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np

# Add project root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.power_analysis import (
    estimate_variance,
    calculate_tost_sample_size,
    calculate_minimum_detectable_effect,
    run_power_analysis
)

def test_estimate_variance():
    """Test variance estimation from a simple dataframe."""
    data = pd.DataFrame({'latent_delta_magnitude': [1.0, 2.0, 3.0, 4.0, 5.0]})
    var = estimate_variance(data)
    # Variance of [1,2,3,4,5] is 2.5
    assert np.isclose(var, 2.5), f"Expected 2.5, got {var}"

def test_calculate_tost_sample_size():
    """Test sample size calculation logic."""
    variance = 1.0
    delta = 0.5
    alpha = 0.05
    power = 0.80
    
    result = calculate_tost_sample_size(variance, delta, alpha, power)
    
    assert result['estimated_variance'] == variance
    assert result['equivalence_margin_delta'] == delta
    assert result['required_sample_size'] > 0
    assert 'z_alpha' in result
    assert 'z_beta' in result

def test_calculate_mdes():
    """Test MDES calculation."""
    n = 100
    variance = 1.0
    alpha = 0.05
    power = 0.80
    
    mdes = calculate_minimum_detectable_effect(n, variance, alpha, power)
    assert mdes > 0
    # If n increases, MDES should decrease
    mdes_large_n = calculate_minimum_detectable_effect(400, variance, alpha, power)
    assert mdes_large_n < mdes

def test_run_power_analysis_integration(tmp_path):
    """Integration test for the full run_power_analysis function."""
    # Create a temporary mock data file
    mock_data_dir = tmp_path / "data" / "processed"
    mock_data_dir.mkdir(parents=True)
    
    mock_df = pd.DataFrame({
        'latent_delta_magnitude': np.random.normal(0, 1, 1000)
    })
    mock_file = mock_data_dir / "latents_raw.parquet"
    mock_df.to_parquet(mock_file)
    
    # Temporarily patch the load_pilot_data function or the path logic
    # Since load_pilot_data looks in project_root/data/processed, 
    # we need to ensure the test environment mimics the project structure 
    # or we mock the function.
    # For this test, we will mock the load_pilot_data function to return our mock_df.
    
    import data.power_analysis as power_module
    
    original_load = power_module.load_pilot_data
    
    def mock_load():
        return mock_df
    
    power_module.load_pilot_data = mock_load
    
    output_file = tmp_path / "power_analysis.json"
    
    try:
        results = run_power_analysis(output_path=output_file)
        
        assert output_file.exists()
        with open(output_file) as f:
            saved_data = json.load(f)
        
        assert saved_data['analysis_type'] == 'a_priori_power_analysis_tost'
        assert 'required_sample_size' in saved_data['recommendations']
        assert saved_data['pilot_sample_size'] == 1000
    finally:
        power_module.load_pilot_data = original_load