import os
import tempfile
import json
import pandas as pd
import numpy as np
from analysis.plot_coverage import load_and_prepare_data, run_regression_test, save_regression_results

def test_load_and_prepare_data():
    """Test that the function correctly aggregates coverage by beta."""
    # Create a temporary CSV
    data = {
        'beta': [0.0, 0.0, 0.2, 0.2, 0.5],
        'coverage_rate': [0.95, 0.96, 0.90, 0.88, 0.80],
        'status': ['passed', 'passed', 'passed', 'passed', 'passed']
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    try:
        result = load_and_prepare_data(temp_path)
        
        assert len(result) == 3, "Should have 3 unique beta levels"
        assert list(result['beta']) == [0.0, 0.2, 0.5], "Beta levels should be sorted"
        
        # Check mean calculation
        assert abs(result.loc[result['beta'] == 0.0, 'coverage_rate'].values[0] - 0.955) < 0.001
    finally:
        os.unlink(temp_path)

def test_run_regression_test_negative_slope():
    """Test regression detection of negative slope."""
    data = {
        'beta': [0.0, 0.2, 0.5, 0.8, 1.0],
        'coverage_rate': [0.95, 0.90, 0.80, 0.70, 0.60]
    }
    df = pd.DataFrame(data)
    
    results = run_regression_test(df)
    
    assert results['slope'] < 0, "Slope should be negative"
    assert results['negative_slope_confirmed'] is True
    assert results['p_value'] < 0.05, "Should be statistically significant"

def test_run_regression_test_positive_slope():
    """Test regression detection of positive slope (unexpected)."""
    data = {
        'beta': [0.0, 0.2, 0.5],
        'coverage_rate': [0.60, 0.80, 0.95]
    }
    df = pd.DataFrame(data)
    
    results = run_regression_test(df)
    
    assert results['slope'] > 0, "Slope should be positive"
    assert results['negative_slope_confirmed'] is False

def test_save_regression_results():
    """Test saving results to JSON."""
    results = {'slope': -0.1, 'p_value': 0.01, 'negative_slope_confirmed': True}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = os.path.join(tmpdir, 'test.json')
        save_regression_results(results, json_path)
        
        assert os.path.exists(json_path)
        
        with open(json_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['slope'] == -0.1
        assert loaded['p_value'] == 0.01
        assert loaded['negative_slope_confirmed'] is True