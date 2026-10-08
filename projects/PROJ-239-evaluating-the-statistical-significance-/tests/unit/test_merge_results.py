"""
Unit tests for merge_results.py
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.scripts.merge_results import (
    load_results,
    prepare_baseline_for_aggregation,
    prepare_robust_for_aggregation,
    compute_error_rates_and_ci
)

@pytest.fixture
def temp_baseline_csv():
    """Create a temporary baseline results CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("iteration,icc,alpha,p_value,rejected\n")
        f.write("1,0.1,0.05,0.03,True\n")
        f.write("2,0.1,0.05,0.07,False\n")
        f.write("3,0.1,0.05,0.02,True\n")
        f.write("4,0.2,0.05,0.01,True\n")
        f.write("5,0.2,0.05,0.04,True\n")
        return f.name

@pytest.fixture
def temp_robust_csv():
    """Create a temporary robust results CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("iteration,icc,method,p_value,rejected\n")
        f.write("1,0.1,ClusterRobust,0.08,False\n")
        f.write("2,0.1,ClusterRobust,0.12,False\n")
        f.write("3,0.1,ClusterRobust,0.06,False\n")
        f.write("4,0.2,ClusterRobust,0.05,False\n")
        f.write("5,0.2,ClusterRobust,0.09,False\n")
        f.write("6,0.1,Permutation,0.07,False\n")
        f.write("7,0.1,Permutation,0.11,False\n")
        f.write("8,0.1,Permutation,0.04,False\n")
        return f.name

@pytest.fixture
def temp_empty_csv():
    """Create a temporary empty CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("")
        return f.name

def test_load_results_success(temp_baseline_csv, temp_robust_csv):
    """Test successful loading of results files."""
    baseline_df, robust_df = load_results(temp_baseline_csv, temp_robust_csv)
    
    assert isinstance(baseline_df, pd.DataFrame)
    assert isinstance(robust_df, pd.DataFrame)
    assert len(baseline_df) == 5
    assert len(robust_df) == 8
    
    # Cleanup
    os.unlink(temp_baseline_csv)
    os.unlink(temp_robust_csv)

def test_load_results_missing_baseline(temp_robust_csv):
    """Test error when baseline file is missing."""
    with pytest.raises(FileNotFoundError):
        load_results("nonexistent.csv", temp_robust_csv)

def test_load_results_missing_robust(temp_baseline_csv):
    """Test error when robust file is missing."""
    with pytest.raises(FileNotFoundError):
        load_results(temp_baseline_csv, "nonexistent.csv")

def test_load_results_empty_file(temp_empty_csv, temp_robust_csv):
    """Test error when baseline file is empty."""
    with pytest.raises(ValueError):
        load_results(temp_empty_csv, temp_robust_csv)
    
    os.unlink(temp_empty_csv)

def test_prepare_baseline_for_aggregation(temp_baseline_csv):
    """Test baseline preparation logic."""
    df = pd.read_csv(temp_baseline_csv)
    prepared = prepare_baseline_for_aggregation(df)
    
    assert 'ICC' in prepared.columns
    assert 'Alpha' in prepared.columns
    assert 'Method' in prepared.columns
    assert 'rejected' in prepared.columns
    assert all(prepared['Method'] == 'Naive')
    
    os.unlink(temp_baseline_csv)

def test_prepare_robust_for_aggregation(temp_robust_csv):
    """Test robust preparation logic."""
    df = pd.read_csv(temp_robust_csv)
    prepared = prepare_robust_for_aggregation(df)
    
    assert 'ICC' in prepared.columns
    assert 'Alpha' in prepared.columns
    assert 'Method' in prepared.columns
    assert 'rejected' in prepared.columns
    assert all(prepared['Method'].isin(['ClusterRobust', 'Permutation']))
    
    os.unlink(temp_robust_csv)

def test_compute_error_rates_and_ci(temp_baseline_csv, temp_robust_csv):
    """Test error rate and CI computation."""
    baseline_df = pd.read_csv(temp_baseline_csv)
    robust_df = pd.read_csv(temp_robust_csv)
    
    baseline_prepared = prepare_baseline_for_aggregation(baseline_df)
    robust_prepared = prepare_robust_for_aggregation(robust_df)
    
    combined = pd.concat([baseline_prepared, robust_prepared], ignore_index=True)
    result = compute_error_rates_and_ci(combined)
    
    assert len(result) > 0
    assert set(result.columns) == {'ICC', 'Alpha', 'Method', 'Empirical_Error_Rate', 'CI_Lower', 'CI_Upper'}
    
    # Check that error rates are between 0 and 1
    assert all(result['Empirical_Error_Rate'] >= 0)
    assert all(result['Empirical_Error_Rate'] <= 1)
    
    # Check that CIs are between 0 and 1
    assert all(result['CI_Lower'] >= 0)
    assert all(result['CI_Upper'] <= 1)
    assert all(result['CI_Lower'] <= result['CI_Upper'])
    
    os.unlink(temp_baseline_csv)
    os.unlink(temp_robust_csv)

def test_compute_error_rates_and_ci_with_zero_rejections():
    """Test CI computation when there are zero rejections."""
    df = pd.DataFrame({
        'ICC': [0.1, 0.1, 0.1],
        'Alpha': [0.05, 0.05, 0.05],
        'Method': ['Test', 'Test', 'Test'],
        'rejected': [False, False, False]
    })
    
    result = compute_error_rates_and_ci(df)
    
    assert len(result) == 1
    assert result['Empirical_Error_Rate'].iloc[0] == 0.0
    assert result['CI_Lower'].iloc[0] == 0.0
    assert result['CI_Upper'].iloc[0] > 0.0  # Upper bound should be > 0 for n>0

def test_compute_error_rates_and_ci_with_all_rejections():
    """Test CI computation when all observations are rejections."""
    df = pd.DataFrame({
        'ICC': [0.1, 0.1, 0.1],
        'Alpha': [0.05, 0.05, 0.05],
        'Method': ['Test', 'Test', 'Test'],
        'rejected': [True, True, True]
    })
    
    result = compute_error_rates_and_ci(df)
    
    assert len(result) == 1
    assert result['Empirical_Error_Rate'].iloc[0] == 1.0
    assert result['CI_Upper'].iloc[0] == 1.0
    assert result['CI_Lower'].iloc[0] < 1.0  # Lower bound should be < 1 for n>0
