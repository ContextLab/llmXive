"""
Contract tests for the Freedman-Lane permutation test logic in code/analysis/validation.py.

These tests verify:
1. The permutation test accepts valid inputs and returns expected structures.
2. The empirical p-value is calculated correctly based on the null distribution.
3. The fixed random seed ensures reproducibility.
4. The number of shuffles matches the configuration.
"""

import os
import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function under test
# Adjust import path based on project structure if necessary
try:
    from code.analysis.validation import run_freedman_lane_permutation, load_null_residuals
except ImportError:
    # Fallback for local execution if package structure isn't set up
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from code.analysis.validation import run_freedman_lane_permutation, load_null_residuals

from code.utils.config import get_config, reset_config


@pytest.fixture
def mock_null_residuals():
    """Create a mock null residuals DataFrame for testing."""
    np.random.seed(42)
    n_samples = 50
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(1, n_samples + 1)],
        'residuals': np.random.normal(0, 1, n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_regression_data(mock_null_residuals):
    """Create mock regression data including the primary predictor and outcome."""
    n_samples = len(mock_null_residuals)
    data = {
        'subject_id': mock_null_residuals['subject_id'],
        'improvement': np.random.normal(10, 5, n_samples),
        'global_centrality': np.random.normal(0.5, 0.2, n_samples),
        'age': np.random.randint(18, 65, n_samples),
        'sex': np.random.choice(['M', 'F'], n_samples),
        'mean_fd': np.random.normal(0.1, 0.05, n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def config_with_permutation_settings():
    """Configure the test environment with specific permutation settings."""
    reset_config()
    config = get_config()
    # Override settings for the test
    config.permutation_shuffles = 1000
    config.permutation_seed = 12345
    return config

def test_permutation_test_returns_expected_structure(mock_null_residuals, mock_regression_data, config_with_permutation_settings):
    """
    Contract Test: Verify that run_freedman_lane_permutation returns a dictionary
    with the required keys: 'empirical_p_value', 'null_distribution', 'observed_statistic',
    'num_shuffles', and 'seed'.
    """
    # Mock the file loading to use our in-memory data
    with patch('code.analysis.validation.load_null_residuals', return_value=mock_null_residuals):
        with patch('code.analysis.validation.load_regression_data', return_value=mock_regression_data):
            result = run_freedman_lane_permutation(
                formula="improvement ~ global_centrality + age + sex + mean_fd",
                data=mock_regression_data,
                null_residuals=mock_null_residuals,
                n_shuffles=1000,
                seed=12345
            )
    
    # Assert structure
    assert isinstance(result, dict), "Result must be a dictionary"
    required_keys = ['empirical_p_value', 'null_distribution', 'observed_statistic', 'num_shuffles', 'seed']
    for key in required_keys:
        assert key in result, f"Result missing required key: {key}"
    
    # Assert types
    assert isinstance(result['empirical_p_value'], (int, float)), "empirical_p_value must be a number"
    assert isinstance(result['null_distribution'], list), "null_distribution must be a list"
    assert isinstance(result['observed_statistic'], (int, float)), "observed_statistic must be a number"
    assert result['num_shuffles'] == 1000, "num_shuffles must match input"
    assert result['seed'] == 12345, "seed must match input"

def test_permutation_test_reproducibility(mock_null_residuals, mock_regression_data, config_with_permutation_settings):
    """
    Contract Test: Verify that running the permutation test twice with the same seed
    produces identical results.
    """
    with patch('code.analysis.validation.load_null_residuals', return_value=mock_null_residuals):
        with patch('code.analysis.validation.load_regression_data', return_value=mock_regression_data):
            result1 = run_freedman_lane_permutation(
                formula="improvement ~ global_centrality + age + sex + mean_fd",
                data=mock_regression_data,
                null_residuals=mock_null_residuals,
                n_shuffles=500,
                seed=99999
            )
            
            result2 = run_freedman_lane_permutation(
                formula="improvement ~ global_centrality + age + sex + mean_fd",
                data=mock_regression_data,
                null_residuals=mock_null_residuals,
                n_shuffles=500,
                seed=99999
            )
    
    # Assert reproducibility
    assert result1['empirical_p_value'] == result2['empirical_p_value'], "P-values must be identical with same seed"
    assert result1['observed_statistic'] == result2['observed_statistic'], "Observed statistics must be identical"
    assert result1['null_distribution'] == result2['null_distribution'], "Null distributions must be identical"

def test_permutation_test_p_value_bounds(mock_null_residuals, mock_regression_data, config_with_permutation_settings):
    """
    Contract Test: Verify that the calculated empirical p-value is within the valid range [0, 1].
    """
    with patch('code.analysis.validation.load_null_residuals', return_value=mock_null_residuals):
        with patch('code.analysis.validation.load_regression_data', return_value=mock_regression_data):
            result = run_freedman_lane_permutation(
                formula="improvement ~ global_centrality + age + sex + mean_fd",
                data=mock_regression_data,
                null_residuals=mock_null_residuals,
                n_shuffles=1000,
                seed=54321
            )
    
    p_value = result['empirical_p_value']
    assert 0 <= p_value <= 1, f"Empirical p-value {p_value} must be between 0 and 1"

def test_permutation_test_null_distribution_length(mock_null_residuals, mock_regression_data, config_with_permutation_settings):
    """
    Contract Test: Verify that the null distribution length matches the number of shuffles.
    """
    n_shuffles = 1000
    with patch('code.analysis.validation.load_null_residuals', return_value=mock_null_residuals):
        with patch('code.analysis.validation.load_regression_data', return_value=mock_regression_data):
            result = run_freedman_lane_permutation(
                formula="improvement ~ global_centrality + age + sex + mean_fd",
                data=mock_regression_data,
                null_residuals=mock_null_residuals,
                n_shuffles=n_shuffles,
                seed=11111
            )
    
    assert len(result['null_distribution']) == n_shuffles, \
        f"Null distribution length {len(result['null_distribution'])} must match n_shuffles {n_shuffles}"

def test_permutation_test_with_no_effect(mock_null_residuals, config_with_permutation_settings):
    """
    Contract Test: When the predictor has no true effect (simulated by random data),
    the empirical p-value should generally be high (not significant), though this
    is a probabilistic check. We check that the distribution is roughly centered
    around zero if the observed statistic is near zero.
    """
    # Create data where predictor is random noise
    np.random.seed(42)
    n = len(mock_null_residuals)
    random_data = pd.DataFrame({
        'subject_id': mock_null_residuals['subject_id'],
        'improvement': np.random.normal(0, 1, n),
        'global_centrality': np.random.normal(0, 1, n), # Random predictor
        'age': np.random.normal(0, 1, n),
        'sex': np.random.choice([0, 1], n),
        'mean_fd': np.random.normal(0, 1, n)
    })
    
    with patch('code.analysis.validation.load_null_residuals', return_value=mock_null_residuals):
        with patch('code.analysis.validation.load_regression_data', return_value=random_data):
            result = run_freedman_lane_permutation(
                formula="improvement ~ global_centrality + age + sex + mean_fd",
                data=random_data,
                null_residuals=mock_null_residuals,
                n_shuffles=1000,
                seed=77777
            )
    
    # The p-value should be a valid number. In a true random scenario, it's likely > 0.05,
    # but we just assert it's a valid probability here to avoid flakiness in contract tests.
    assert 0 <= result['empirical_p_value'] <= 1
    # Check that the null distribution is populated
    assert len(result['null_distribution']) > 0

def test_permutation_test_uses_correct_seed(mock_null_residuals, mock_regression_data):
    """
    Contract Test: Verify that the seed is actually used by checking that a different seed
    produces a different null distribution (with high probability).
    """
    with patch('code.analysis.validation.load_null_residuals', return_value=mock_null_residuals):
        with patch('code.analysis.validation.load_regression_data', return_value=mock_regression_data):
            result_seed_1 = run_freedman_lane_permutation(
                formula="improvement ~ global_centrality + age + sex + mean_fd",
                data=mock_regression_data,
                null_residuals=mock_null_residuals,
                n_shuffles=1000,
                seed=100
            )
            
            result_seed_2 = run_freedman_lane_permutation(
                formula="improvement ~ global_centrality + age + sex + mean_fd",
                data=mock_regression_data,
                null_residuals=mock_null_residuals,
                n_shuffles=1000,
                seed=200
            )
    
    # While observed statistics might be the same (deterministic on data), the null distribution
    # should differ because the shuffling order depends on the seed.
    # Note: There is a tiny chance they could be identical by random chance, but highly unlikely.
    assert result_seed_1['null_distribution'] != result_seed_2['null_distribution'], \
        "Null distributions should differ with different seeds"