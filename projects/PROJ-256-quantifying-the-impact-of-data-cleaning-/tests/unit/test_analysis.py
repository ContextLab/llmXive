import pytest
import pandas as pd
import numpy as np
from code.analysis import run_t_test, run_linear_regression, run_baseline_analysis

def test_run_t_test():
    """Test t-test with known data."""
    data = {
        'outcome': [0, 0, 0, 1, 1, 1],
        'predictor': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    }
    df = pd.DataFrame(data)
    
    result = run_t_test(df, 'outcome', 'predictor')
    
    assert 'p_value' in result
    assert 'ci_lower' in result
    assert 'ci_upper' in result
    assert 'cohen_d' in result
    assert 0 <= result['p_value'] <= 1

def test_run_linear_regression():
    """Test linear regression with known data."""
    data = {
        'outcome': [1, 2, 3, 4, 5],
        'predictor': [2, 4, 6, 8, 10]
    }
    df = pd.DataFrame(data)
    
    result = run_linear_regression(df, 'outcome', ['predictor'])
    
    assert 'r_squared' in result
    assert 'p_values' in result
    assert result['r_squared'] > 0.9  # Perfect correlation

def test_run_baseline_analysis_dataframe():
    """Test run_baseline_analysis with dataframe input."""
    data = {
        'outcome': [0, 0, 0, 1, 1, 1],
        'x1': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        'x2': [10, 20, 30, 40, 50, 60]
    }
    df = pd.DataFrame(data)
    
    result = run_baseline_analysis(dataframe=df, outcome='outcome', predictors=['x1', 'x2'])
    
    assert 'x1' in result
    assert 'x2' in result
    assert 't_test' in result['x1']
    assert 'regression' in result['x1']
