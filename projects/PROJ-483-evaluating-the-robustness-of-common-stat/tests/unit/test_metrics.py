import pytest
import pandas as pd
import numpy as np
from metrics import (
    clopper_pearson_ci, 
    calculate_type1_error, 
    verify_trend_monotonicity,
    update_aggregated_with_trend
)
import tempfile
import os

def test_clopper_pearson_ci_zero_successes():
    """Test CI when there are 0 successes."""
    lower, upper = clopper_pearson_ci(0, 100)
    assert lower == 0.0
    assert upper > 0.0
    assert upper < 1.0

def test_clopper_pearson_ci_all_successes():
    """Test CI when there are 100% successes."""
    lower, upper = clopper_pearson_ci(100, 100)
    assert lower > 0.0
    assert lower < 1.0
    assert upper == 1.0

def test_clopper_pearson_ci_normal():
    """Test CI for a normal binomial distribution."""
    # 50 successes in 100 trials, expected around 0.5
    lower, upper = clopper_pearson_ci(50, 100)
    assert 0.4 < lower < 0.6
    assert 0.4 < upper < 0.6
    assert lower < upper

def test_calculate_type1_error():
    """Test Type I error calculation."""
    p_values = [0.01, 0.02, 0.1, 0.2, 0.3]
    # 2 out of 5 are < 0.05
    error_rate = calculate_type1_error(p_values, alpha=0.05)
    assert error_rate == 0.4

def test_verify_trend_monotonicity_positive():
    """Test trend verification with a clear positive trend."""
    data = {
        'dependency_strength': [0.0, 0.2, 0.4, 0.6, 0.8],
        'observed_error_rate': [0.05, 0.08, 0.15, 0.25, 0.40]
    }
    df = pd.DataFrame(data)
    is_mono, corr, p_val = verify_trend_monotonicity(df)
    assert is_mono is True
    assert corr > 0
    assert p_val < 0.05

def test_verify_trend_monotonicity_negative():
    """Test trend verification with a negative trend."""
    data = {
        'dependency_strength': [0.0, 0.2, 0.4, 0.6, 0.8],
        'observed_error_rate': [0.40, 0.30, 0.25, 0.15, 0.08]
    }
    df = pd.DataFrame(data)
    is_mono, corr, p_val = verify_trend_monotonicity(df)
    assert is_mono is False
    assert corr < 0
    assert p_val < 0.05 # Should be significant negative

def test_verify_trend_monotonicity_flat():
    """Test trend verification with no trend."""
    data = {
        'dependency_strength': [0.0, 0.2, 0.4, 0.6, 0.8],
        'observed_error_rate': [0.05, 0.05, 0.05, 0.05, 0.05]
    }
    df = pd.DataFrame(data)
    is_mono, corr, p_val = verify_trend_monotonicity(df)
    assert is_mono is False
    assert corr == 0.0

def test_update_aggregated_with_trend(tmp_path):
    """Test the full pipeline of updating aggregated CSV with trend status."""
    input_data = {
        'dependency_strength': [0.0, 0.2, 0.4, 0.6, 0.8],
        'observed_error_rate': [0.05, 0.08, 0.15, 0.25, 0.40],
        'other_col': [1, 2, 3, 4, 5]
    }
    df_input = pd.DataFrame(input_data)
    
    input_path = tmp_path / "aggregated.csv"
    output_path = tmp_path / "aggregated_updated.csv"
    
    df_input.to_csv(input_path, index=False)
    
    update_aggregated_with_trend(str(input_path), str(output_path))
    
    assert os.path.exists(output_path)
    df_output = pd.read_csv(output_path)
    
    assert 'trend_status' in df_output.columns
    assert 'trend_correlation' in df_output.columns
    assert 'trend_p_value' in df_output.columns
    
    # Check that the status indicates a monotonic increase
    assert "Monotonic Increase" in df_output['trend_status'].iloc[0]

def test_update_aggregated_with_trend_no_trend(tmp_path):
    """Test update with data that has no trend."""
    input_data = {
        'dependency_strength': [0.0, 0.2, 0.4, 0.6, 0.8],
        'observed_error_rate': [0.05, 0.05, 0.05, 0.05, 0.05],
    }
    df_input = pd.DataFrame(input_data)
    
    input_path = tmp_path / "aggregated.csv"
    output_path = tmp_path / "aggregated_updated.csv"
    
    df_input.to_csv(input_path, index=False)
    
    update_aggregated_with_trend(str(input_path), str(output_path))
    
    df_output = pd.read_csv(output_path)
    assert "No Monotonic Trend" in df_output['trend_status'].iloc[0]
