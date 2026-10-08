import pytest
import numpy as np
import pandas as pd
import os
import tempfile
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.statistics import (
    format_delta_r2,
    log_regression_summary,
    fit_regression,
    fit_baseline_regression,
    run_permutation_test,
    construct_covariates_dict,
    validate_alignment,
    collect_static_strengths,
    RegressionResult
)
from config import get_config

def test_format_delta_r2_precision():
    """Test that delta R2 is formatted to exactly 4 decimal places."""
    result = format_delta_r2(0.123456)
    assert result == "0.1235"
    
    result = format_delta_r2(0.0)
    assert result == "0.0000"
    
    result = format_delta_r2(-0.05)
    assert result == "-0.0500"

def test_construct_covariates_dict():
    """Test covariates dict construction."""
    static = [0.1, 0.2]
    ages = [25, 30]
    sexes = ["M", "F"]
    edus = [16, 18]
    
    cov = construct_covariates_dict(static, ages, sexes, edus)
    
    assert 'static_connectivity_strength' in cov
    assert 'age' in cov
    assert 'sex' in cov
    assert 'education' in cov
    assert cov['static_connectivity_strength'] == static

def test_validate_alignment():
    """Test alignment validation."""
    assert validate_alignment([1, 2], [3, 4], [5, 6], ["a", "b"]) is True
    
    with pytest.raises(ValueError):
        validate_alignment([1], [2, 3], [4, 5], ["a", "b"])

def test_collect_static_strengths():
    """Test collection of static strengths."""
    results = [0.1, 0.2, 0.3]
    collected = collect_static_strengths(results)
    assert isinstance(collected, list)
    assert all(isinstance(x, float) for x in collected)

def test_run_permutation_test():
    """Test permutation test returns correct structure."""
    flex = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    creat = np.array([1.1, 2.2, 2.9, 4.1, 5.2])
    
    result = run_permutation_test(flex, creat, n_permutations=100, seed=42)
    
    assert 'empirical_p_value' in result
    assert 'distribution_of_max_stats' in result
    assert isinstance(result['empirical_p_value'], float)
    assert 0.0 <= result['empirical_p_value'] <= 1.0
    assert len(result['distribution_of_max_stats']) == 100

def test_fit_regression_structure():
    """Test that fit_regression returns a valid RegressionResult."""
    flex = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    creat = np.array([1.1, 2.2, 2.9, 4.1, 5.2])
    cov = {
        'age': [20, 21, 22, 23, 24],
        'sex': ['M', 'F', 'M', 'F', 'M'],
        'education': [10, 12, 14, 16, 18],
        'static_connectivity_strength': [0.1, 0.2, 0.3, 0.4, 0.5]
    }
    
    result = fit_regression(flex, creat, cov)
    
    assert isinstance(result, RegressionResult)
    assert isinstance(result.coefficients, dict)
    assert 'network_flexibility' in result.coefficients
    assert 'pearson_r' in result.__dict__
    assert isinstance(result.pearson_r, float)

def test_fit_baseline_regression():
    """Test baseline regression."""
    creat = np.array([1.1, 2.2, 2.9, 4.1, 5.2])
    static = [0.1, 0.2, 0.3, 0.4, 0.5]
    cov = {
        'age': [20, 21, 22, 23, 24],
        'sex': ['M', 'F', 'M', 'F', 'M'],
        'education': [10, 12, 14, 16, 18],
        'static_connectivity_strength': static
    }
    
    result = fit_baseline_regression(creat, static, cov)
    
    assert isinstance(result, RegressionResult)
    assert 'static_connectivity_strength' in result.coefficients

def test_log_regression_summary():
    """Test that log_regression_summary creates/updates the CSV correctly."""
    # Setup temporary config for testing
    config = get_config()
    original_path = config.DATA_PATH
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config.DATA_PATH = tmpdir
        output_path = Path(tmpdir) / "interim" / "regression_summary.csv"
        
        # First call (should create file)
        log_regression_summary("sub_001", 0.15, 3.2, 0.85, 0.01)
        
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 1
        assert df.iloc[0]['subject_id'] == 'sub_001'
        
        # Second call (should append)
        log_regression_summary("sub_002", 0.22, 4.1, 0.90, 0.02)
        
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert df.iloc[1]['subject_id'] == 'sub_002'
        
        # Verify columns
        expected_cols = ['subject_id', 'flexibility', 'creativity', 'pearson_r', 'empirical_p_value']
        assert list(df.columns) == expected_cols
    
    # Restore
    config.DATA_PATH = original_path
