import pytest
import pandas as pd
import numpy as np
import os
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import run_bootstrap_ci, load_analysis_data
from config import get_config

def test_bootstrap_ci_structure():
    """
    Test that bootstrap CI function returns the expected structure.
    Uses mock data to ensure the logic runs without needing real data files.
    """
    # Create a mock DataFrame mimicking the joined data from T012 and T020
    # We need: planet_name, water_mixing_ratio, is_upper_limit
    n_samples = 50
    mock_data = {
        'planet_name': [f'planet_{i}' for i in range(n_samples)],
        'water_mixing_ratio': np.random.uniform(-8, -4, n_samples),
        'is_upper_limit': np.random.choice([True, False], n_samples, p=[0.2, 0.8])
    }
    df = pd.DataFrame(mock_data)

    # Run bootstrap with fewer iterations for speed
    result = run_bootstrap_ci(df, n_iterations=100, random_seed=123)

    # Verify structure
    assert 'iterations' in result
    assert 'ci_lower' in result
    assert 'ci_upper' in result
    assert 'tau_estimate' in result
    assert 'sample_size' in result

    assert result['iterations'] == 100
    assert result['sample_size'] == n_samples
    assert isinstance(result['ci_lower'], float)
    assert isinstance(result['ci_upper'], float)
    
    # CI lower should be less than upper
    assert result['ci_lower'] <= result['ci_upper']

def test_bootstrap_reproducibility():
    """
    Test that running with the same seed produces the same results.
    """
    n_samples = 30
    mock_data = {
        'planet_name': [f'p_{i}' for i in range(n_samples)],
        'water_mixing_ratio': np.random.uniform(-8, -4, n_samples),
        'is_upper_limit': np.random.choice([True, False], n_samples)
    }
    df = pd.DataFrame(mock_data)

    result1 = run_bootstrap_ci(df, n_iterations=50, random_seed=999)
    result2 = run_bootstrap_ci(df, n_iterations=50, random_seed=999)

    assert result1['ci_lower'] == result2['ci_lower']
    assert result1['ci_upper'] == result2['ci_upper']