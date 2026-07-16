import os
import sys
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from code.preprocessing import calculate_correlation, calculate_r_squared, perform_construct_validity_check

def test_calculate_correlation():
    x = pd.Series([1, 2, 3, 4, 5])
    y = pd.Series([2, 4, 6, 8, 10])
    corr = calculate_correlation(x, y)
    assert abs(corr - 1.0) < 0.01

def test_calculate_r_squared():
    x = pd.Series([1, 2, 3, 4, 5])
    y = pd.Series([2, 4, 6, 8, 10])
    r2 = calculate_r_squared(x, y)
    assert abs(r2 - 1.0) < 0.01

def test_perform_construct_validity_check():
    # Create a mock dataframe
    data = {
        'adhesion_strength': [10, 20, 30, 40, 50],
        'crosslinker_density_proxy_1': [1, 2, 3, 4, 5],
        'crosslinker_density_proxy_2': [5, 4, 3, 2, 1]
    }
    df = pd.DataFrame(data)
    
    report = perform_construct_validity_check(df)
    
    assert 'proxy_name' in report.columns
    assert 'correlation' in report.columns
    assert 'r_squared' in report.columns
    assert 'status' in report.columns
    assert os.path.exists('data/processed/proxy_validation_report.csv')