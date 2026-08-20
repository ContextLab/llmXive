"""
Unit tests for the bootstrap resampling functionality in analysis.py.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Import the function to test
from analysis import run_bootstrap_ci, compute_censored_kendall_tau

@pytest.fixture
def sample_censored_data():
    """Create a small sample dataset with censored values for testing."""
    data = {
        'temperature': [1000, 1200, 1400, 1600, 1800, 2000],
        'water_mixing_ratio': [-4.0, -3.8, -3.5, -3.2, -3.0, -2.8],
        'is_censored': [False, False, False, True, True, True]
    }
    return pd.DataFrame(data)

def test_bootstrap_ci_computation(sample_censored_data):
    """Test that bootstrap_ci returns a valid dictionary with expected keys."""
    results = run_bootstrap_ci(sample_censored_data, n_iterations=10, random_state=42)

    assert isinstance(results, dict)
    assert 'iterations' in results
    assert 'ci_lower' in results
    assert 'ci_upper' in results
    assert 'mean_tau' in results
    assert 'std_dev' in results

    assert results['iterations'] == 10
    assert isinstance(results['ci_lower'], float)
    assert isinstance(results['ci_upper'], float)
    assert results['ci_lower'] <= results['ci_upper']

def test_bootstrap_ci_with_low_iterations(sample_censored_data):
    """Test bootstrap with a very low number of iterations."""
    results = run_bootstrap_ci(sample_censored_data, n_iterations=2, random_state=123)

    assert results['iterations'] == 2
    # With 2 iterations, CI might be wide or equal, but should not crash
    assert 'ci_lower' in results

def test_bootstrap_ci_empty_dataframe():
    """Test that an empty dataframe raises an error."""
    empty_df = pd.DataFrame(columns=['temperature', 'water_mixing_ratio', 'is_censored'])
    with pytest.raises(ValueError, match="Cannot bootstrap with empty dataset"):
        run_bootstrap_ci(empty_df, n_iterations=10)

def test_bootstrap_ci_missing_columns(sample_censored_data):
    """Test that missing required columns raise an error."""
    incomplete_df = sample_censored_data.drop(columns=['temperature'])
    # The function should handle the missing column gracefully or raise an error
    # In our implementation, it logs a warning and skips, but if no valid taus are found, it raises RuntimeError
    with pytest.raises(RuntimeError, match="Bootstrap failed to produce any valid Tau values"):
        run_bootstrap_ci(incomplete_df, n_iterations=5)

def test_save_bootstrap_results():
    """Test saving bootstrap results to a JSON file."""
    from analysis import save_bootstrap_results

    test_results = {
        "iterations": 100,
        "mean_tau": 0.5,
        "ci_lower": 0.3,
        "ci_upper": 0.7,
        "std_dev": 0.1
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_bootstrap.json"
        save_bootstrap_results(test_results, str(output_path))

        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = json.load(f)

        assert loaded == test_results

def test_compute_censored_kendall_tau_basic():
    """Test basic computation of censored Kendall's tau."""
    data = {
        'temperature': [100, 200, 300, 400, 500],
        'water_mixing_ratio': [1.0, 2.0, 3.0, 4.0, 5.0],
        'is_censored': [False, False, False, False, False]
    }
    df = pd.DataFrame(data)
    tau, p_val = compute_censored_kendall_tau(df, 'temperature', 'water_mixing_ratio')

    # Perfect positive correlation should yield tau close to 1.0
    assert tau > 0.9
    assert 0.0 <= p_val <= 1.0

def test_compute_censored_kendall_tau_censored():
    """Test computation with some censored values."""
    data = {
        'temperature': [100, 200, 300, 400, 500],
        'water_mixing_ratio': [1.0, 2.0, 3.0, 4.0, 5.0],
        'is_censored': [False, False, True, True, True]
    }
    df = pd.DataFrame(data)
    tau, p_val = compute_censored_kendall_tau(df, 'temperature', 'water_mixing_ratio')

    # Should not crash and return a valid tau
    assert -1.0 <= tau <= 1.0
    assert 0.0 <= p_val <= 1.0
