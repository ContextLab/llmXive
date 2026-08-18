import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis import run_bootstrap_ci, save_bootstrap_results, load_analysis_data

@pytest.fixture
def mock_data():
    """Create a mock DataFrame with censored data."""
    np.random.seed(42)
    n = 50
    # Generate some mixing ratios
    ratios = np.random.normal(0, 1, n)
    # Generate some upper limit flags (0 = detection, 1 = upper limit)
    is_upper = np.random.choice([0, 1], n, p=[0.8, 0.2])
    
    df = pd.DataFrame({
        'water_mixing_ratio': ratios,
        'is_upper_limit': is_upper,
        'snr': np.random.uniform(2, 10, n) # For QC filter
    })
    return df

def test_bootstrap_ci_structure(mock_data, tmp_path):
    """Test that bootstrap_ci returns the correct structure."""
    result = run_bootstrap_ci(mock_data, n_iterations=10, random_seed=123)
    
    assert 'iterations' in result
    assert 'ci_lower' in result
    assert 'ci_upper' in result
    assert 'tau_median' in result
    
    assert result['iterations'] == 10
    assert isinstance(result['ci_lower'], (float, type(None)))
    assert isinstance(result['ci_upper'], (float, type(None)))
    assert isinstance(result['tau_median'], (float, type(None)))

def test_bootstrap_ci_values(mock_data):
    """Test that bootstrap CI values are reasonable."""
    result = run_bootstrap_ci(mock_data, n_iterations=100, random_seed=456)
    
    if result['ci_lower'] is not None:
        # CI lower should be <= tau_median <= CI upper
        assert result['ci_lower'] <= result['tau_median']
        assert result['tau_median'] <= result['ci_upper']
        
        # Values should be in [-1, 1] range for Kendall's tau
        assert -1.0 <= result['ci_lower'] <= 1.0
        assert -1.0 <= result['ci_upper'] <= 1.0

def test_save_bootstrap_results(mock_data, tmp_path):
    """Test that results are saved correctly to JSON."""
    result = run_bootstrap_ci(mock_data, n_iterations=10, random_seed=789)
    output_path = tmp_path / "test_bootstrap.json"
    
    save_bootstrap_results(result, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
        
    assert saved_data['iterations'] == 10
    assert saved_data['ci_lower'] == result['ci_lower']
    assert saved_data['ci_upper'] == result['ci_upper']
    assert saved_data['tau_median'] == result['tau_median']

def test_insufficient_data():
    """Test behavior with insufficient data."""
    df = pd.DataFrame({
        'water_mixing_ratio': [1.0],
        'is_upper_limit': [0],
        'snr': [5.0]
    })
    
    result = run_bootstrap_ci(df, n_iterations=10)
    
    assert result['error'] == "Insufficient data"
    assert result['ci_lower'] is None
    assert result['ci_upper'] is None
    assert result['tau_median'] is None
