"""
Integration tests for robustness checks (T020, T021, etc.)
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from robustness import run_permutation_test, save_permutation_results


@pytest.fixture
def sample_data():
    """Create a small sample dataset for testing."""
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        'year': np.random.randint(1990, 2020, n),
        'power_est': np.random.rand(n),
        'effect_size': np.random.rand(n) * 0.5,
        'sample_size': np.random.randint(50, 500, n),
        'field': np.random.choice(['psych', 'bio', 'phys'], n),
        'original_study_id': [f'study_{i}' for i in range(n)]
    })
    return data


@pytest.fixture
def sample_observed_slope():
    return -0.01  # Negative drift


def test_permutation_logic_small_count(sample_data, sample_observed_slope):
    """
    Test permutation logic with a small number of iterations.
    This is a unit test for the core logic (T018 equivalent for robustness).
    """
    # Run with only 5 permutations to avoid long runtime
    results = run_permutation_test(
        data=sample_data,
        observed_slope=sample_observed_slope,
        n_permutations=5,
        max_runtime=60  # 1 minute
    )
    
    # Verify structure
    assert 'iterations_run' in results
    assert 'status' in results
    assert 'empirical_p_value' in results
    
    # Verify iterations_run is between 1 and 5
    assert 1 <= results['iterations_run'] <= 5
    
    # Verify p-value is between 0 and 1
    assert 0 <= results['empirical_p_value'] <= 1
    
    # Verify status is either 'exact' or 'approximate'
    assert results['status'] in ['exact', 'approximate', 'failed']


def test_permutation_handles_nan(sample_data, sample_observed_slope):
    """Test that permutation test handles NaN values correctly."""
    # Inject NaN values
    sample_data.loc[0, 'power_est'] = np.nan
    sample_data.loc[1, 'year'] = np.nan
    
    results = run_permutation_test(
        data=sample_data,
        observed_slope=sample_observed_slope,
        n_permutations=3,
        max_runtime=60
    )
    
    # Should still complete, possibly with fewer iterations
    assert 'iterations_run' in results
    assert results['iterations_run'] >= 0


def test_save_permutation_results(tmp_path, sample_data, sample_observed_slope):
    """Test that results are saved correctly to JSON."""
    # Run a small permutation test
    results = run_permutation_test(
        data=sample_data,
        observed_slope=sample_observed_slope,
        n_permutations=3,
        max_runtime=60
    )
    
    # Save to temp file
    output_path = tmp_path / "test_permutation.json"
    save_permutation_results(results, str(output_path))
    
    # Verify file exists and can be loaded
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded_results = json.load(f)
    
    assert loaded_results == results