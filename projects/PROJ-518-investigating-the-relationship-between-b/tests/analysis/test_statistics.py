import numpy as np
import pytest
from analysis.statistics import (
    RegressionResult,
    format_delta_r2,
    log_regression_summary,
    fit_regression,
    fit_baseline_regression,
    run_permutation_test,
    merge_permutation_data,
    apply_fwe_correction,
    construct_sensitivity_df,
    run_sensitivity_analysis
)
import pandas as pd
import os
import tempfile

def test_format_delta_r2():
    """Test that format_delta_r2 formats to 4 decimal places."""
    result = format_delta_r2(0.123456789)
    assert result == "0.12345"
    
    result = format_delta_r2(0.00001)
    assert result == "0.0000"
    
    result = format_delta_r2(1.0)
    assert result == "1.0000"

def test_fit_regression_includes_pearson_r():
    """Test that fit_regression returns pearson_r in RegressionResult."""
    np.random.seed(42)
    n = 50
    flexibility = np.random.randn(n)
    creativity = 0.5 * flexibility + np.random.randn(n) * 0.5
    
    covariates = {
        'static_connectivity_strength': np.random.randn(n).tolist(),
        'age': np.random.randint(20, 40, n).tolist(),
        'sex': ['male' if i % 2 == 0 else 'female' for i in range(n)],
        'education': np.random.randint(12, 20, n).tolist()
    }
    
    result = fit_regression(flexibility, creativity, covariates)
    
    assert isinstance(result, RegressionResult)
    assert hasattr(result, 'pearson_r')
    assert isinstance(result.pearson_r, float)
    assert not np.isnan(result.pearson_r)
    assert hasattr(result, 'p_value')
    assert isinstance(result.p_value, float)

def test_log_regression_summary_creates_file():
    """Test that log_regression_summary creates the CSV file with pearson_r."""
    np.random.seed(42)
    n = 50
    flexibility = np.random.randn(n)
    creativity = 0.5 * flexibility + np.random.randn(n) * 0.5
    
    covariates = {
        'static_connectivity_strength': np.random.randn(n).tolist(),
        'age': np.random.randint(20, 40, n).tolist(),
        'sex': ['male' if i % 2 == 0 else 'female' for i in range(n)],
        'education': np.random.randint(12, 20, n).tolist()
    }
    
    result = fit_regression(flexibility, creativity, covariates)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_regression_summary.csv')
        log_regression_summary(result, output_path)
        
        assert os.path.exists(output_path)
        
        df = pd.read_csv(output_path)
        assert 'pearson_r' in df.columns
        assert 'p_value' in df.columns
        assert len(df) == 1
        
        # Verify the values match
        assert abs(df['pearson_r'].iloc[0] - result.pearson_r) < 1e-6

def test_regression_result_has_delta_r2_fields():
    """Test that RegressionResult can hold delta_r2 fields."""
    result = RegressionResult(
        coefficients={'flexibility': 0.5},
        r_squared=0.5,
        adjusted_r_squared=0.45,
        pearson_r=0.7,
        p_value=0.01,
        delta_r2=0.05,
        delta_r2_str="0.0500"
    )
    
    assert result.delta_r2 == 0.05
    assert result.delta_r2_str == "0.0500"

def test_fit_baseline_regression():
    """Test baseline regression model."""
    np.random.seed(42)
    n = 50
    creativity = np.random.randn(n)
    static_strengths = np.random.randn(n).tolist()
    
    covariates = {
        'age': np.random.randint(20, 40, n).tolist(),
        'sex': ['male' if i % 2 == 0 else 'female' for i in range(n)],
        'education': np.random.randint(12, 20, n).tolist()
    }
    
    result = fit_baseline_regression(creativity, static_strengths, covariates)
    
    assert isinstance(result, RegressionResult)
    assert result.pearson_r != result.pearson_r  # NaN check
    assert 'static_connectivity_strength' in result.coefficients

def test_run_permutation_test():
    """Test permutation test returns correct structure."""
    np.random.seed(42)
    n = 30
    flexibility = np.random.randn(n)
    creativity = np.random.randn(n)
    
    result = run_permutation_test(flexibility, creativity, n_permutations=100, seed=42)
    
    assert 'empirical_p_value' in result
    assert 'distribution_of_max_stats' in result
    assert isinstance(result['empirical_p_value'], float)
    assert 0 <= result['empirical_p_value'] <= 1
    assert len(result['distribution_of_max_stats']) == 100

def test_merge_permutation_data():
    """Test merging permutation data."""
    p_values = [0.01, 0.05, 0.1]
    dist = [0.1, 0.2, 0.3]
    
    merged = merge_permutation_data(p_values, dist)
    
    assert 'p_values' in merged
    assert 'distribution_of_max_stats' in merged
    assert merged['p_values'] == p_values
    assert merged['distribution_of_max_stats'] == dist

def test_apply_fwe_correction_bonferroni():
    """Test Bonferroni correction."""
    merged_data = {
        'p_values': [0.01, 0.05, 0.1],
        'distribution_of_max_stats': []
    }
    
    adjusted = apply_fwe_correction(merged_data, method='bonferroni')
    
    assert len(adjusted) == 3
    # Bonferroni: p * k, capped at 1.0
    assert adjusted[0] == 0.03  # 0.01 * 3
    assert adjusted[1] == 0.15  # 0.05 * 3
    assert adjusted[2] == 0.3   # 0.1 * 3

def test_construct_sensitivity_df():
    """Test constructing sensitivity DataFrame."""
    data = {
        'window_lengths': [20, 30, 40],
        'correlations': [0.1, 0.2, 0.3],
        'p_values': [0.01, 0.05, 0.1]
    }
    
    df = construct_sensitivity_df(data)
    
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ['window_length', 'correlation', 'p_value']
    assert len(df) == 3
    assert df['window_length'].tolist() == [20, 30, 40]