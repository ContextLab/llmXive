import pytest
import os
import pandas as pd
from code.power import calculate_retrospective_power, run_retrospective_power_analysis
from code.aggregate_power import aggregate_power_analysis

def test_retrospective_power_integration():
    """
    Integration test: Verify that retrospective power analysis runs and produces expected output structure.
    """
    # Simulate model results
    model_results = {
        'interaction_coef': 0.15,
        'interaction_se': 0.05
    }
    n = 500
    
    results = run_retrospective_power_analysis(
        np.abs(model_results['interaction_coef'] / np.sqrt(n)), 
        n, 
        0.05, 
        0.80
    )
    
    assert 'observed_power' in results
    assert 'required_n' in results
    assert 'effect_size' in results
    assert 'met_target' in results
    assert 0 <= results['observed_power'] <= 1
    assert results['required_n'] > 0

def test_aggregate_power_analysis_structure():
    """
    Test that aggregate function returns correct keys.
    """
    model_results = {
        'interaction_coef': 0.1,
        'interaction_se': 0.04
    }
    n = 300
    
    # We mock the file writing part by just checking the return structure
    # The actual file writing is tested in test_save_retrospective_power_results if needed
    results, path = aggregate_power_analysis(model_results, n, 0.05)
    
    assert os.path.exists(path)
    df = pd.read_csv(path)
    assert 'observed_power' in df.columns
    assert 'required_n' in df.columns
    assert 'effect_size' in df.columns
    assert 'met_target' in df.columns