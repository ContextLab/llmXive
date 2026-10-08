"""
Unit tests for bootstrapping module (T016).
"""
import pytest
import numpy as np
import pandas as pd
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, 'code')

from bootstrapping import (
    calculate_correlation,
    bootstrap_correlation,
    run_full_bootstrapping,
    save_results
)
from config import set_synthetic_mode

@pytest.fixture
def sample_data():
    """Create a sample DataFrame for testing."""
    np.random.seed(42)
    n = 15  # Small sample to trigger bootstrapping
    return pd.DataFrame({
        'global_efficiency': np.random.normal(0.5, 0.1, n),
        'cognitive_score': np.random.normal(75, 10, n)
    })

@pytest.fixture
def synthetic_mode():
    """Set synthetic mode for testing."""
    set_synthetic_mode(True)
    yield
    set_synthetic_mode(False)

def test_calculate_correlation_returns_float(sample_data):
    """Test that calculate_correlation returns a float."""
    result = calculate_correlation(sample_data, 'global_efficiency', 'cognitive_score')
    assert isinstance(result, float)
    assert -1.0 <= result <= 1.0

def test_calculate_correlation_handles_missing_columns(sample_data):
    """Test that calculate_correlation raises error for missing columns."""
    with pytest.raises(ValueError):
        calculate_correlation(sample_data, 'nonexistent_col', 'cognitive_score')

def test_calculate_correlation_insufficient_data():
    """Test that calculate_correlation raises error with insufficient data."""
    df = pd.DataFrame({
        'x': [1.0],
        'y': [2.0]
    })
    with pytest.raises(ValueError):
        calculate_correlation(df, 'x', 'y')

def test_bootstrap_correlation_returns_dict(sample_data):
    """Test that bootstrap_correlation returns expected dictionary structure."""
    result = bootstrap_correlation(
        sample_data,
        'global_efficiency',
        'cognitive_score',
        n_iterations=100,
        random_state=42
    )
    
    assert isinstance(result, dict)
    required_keys = [
        'observed_correlation',
        'bootstrap_mean',
        'bootstrap_std',
        'ci_lower',
        'ci_upper',
        'confidence_level',
        'n_iterations',
        'valid_iterations',
        'sample_size'
    ]
    
    for key in required_keys:
        assert key in result, f"Missing key: {key}"

def test_bootstrap_correlation_ci_bounds(sample_data):
    """Test that CI bounds are ordered correctly."""
    result = bootstrap_correlation(
        sample_data,
        'global_efficiency',
        'cognitive_score',
        n_iterations=100,
        random_state=42
    )
    
    assert result['ci_lower'] <= result['ci_upper']
    assert result['ci_lower'] >= -1.0
    assert result['ci_upper'] <= 1.0

def test_bootstrap_correlation_iterations(sample_data):
    """Test that bootstrap runs for specified number of iterations."""
    n_iter = 50
    result = bootstrap_correlation(
        sample_data,
        'global_efficiency',
        'cognitive_score',
        n_iterations=n_iter,
        random_state=42
    )
    
    assert result['n_iterations'] == n_iter
    assert result['valid_iterations'] <= n_iter

def test_save_results_creates_file(sample_data, tmp_path):
    """Test that save_results creates a valid JSON file."""
    test_results = {
        'test': 'data',
        'value': 42
    }
    
    output_path = tmp_path / 'test_output.json'
    save_results(test_results, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == test_results

def test_run_full_bootstrapping_triggers_small_sample_logic(synthetic_mode, sample_data):
    """Test that run_full_bootstrapping correctly identifies small sample size."""
    with patch('bootstrapping.load_preprocessed_data', return_value=sample_data):
        result = run_full_bootstrapping(n_iterations=100, random_state=42)
        
        assert result['triggered_by_small_sample'] == True
        assert result['sample_size'] == 15
        assert result['threshold_n'] == 20
        assert 'correlation_results' in result

def test_run_full_bootstrapping_with_large_sample(synthetic_mode):
    """Test that run_full_bootstrapping handles large samples correctly."""
    np.random.seed(42)
    large_df = pd.DataFrame({
        'global_efficiency': np.random.normal(0.5, 0.1, 50),
        'cognitive_score': np.random.normal(75, 10, 50)
    })
    
    with patch('bootstrapping.load_preprocessed_data', return_value=large_df):
        result = run_full_bootstrapping(n_iterations=100, random_state=42)
        
        assert result['triggered_by_small_sample'] == False
        assert result['sample_size'] == 50

def test_bootstrap_correlation_deterministic_with_seed(sample_data):
    """Test that bootstrap is deterministic with fixed random seed."""
    result1 = bootstrap_correlation(
        sample_data,
        'global_efficiency',
        'cognitive_score',
        n_iterations=100,
        random_state=42
    )
    
    result2 = bootstrap_correlation(
        sample_data,
        'global_efficiency',
        'cognitive_score',
        n_iterations=100,
        random_state=42
    )
    
    assert result1['observed_correlation'] == result2['observed_correlation']
    assert result1['bootstrap_mean'] == result2['bootstrap_mean']
    assert result1['ci_lower'] == result2['ci_lower']
    assert result1['ci_upper'] == result2['ci_upper']
