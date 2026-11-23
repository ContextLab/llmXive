import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the functions to test
from analysis.stats import (
    calculate_summary_statistics_for_task,
    run_paired_ttest_dp_vs_nondp,
    run_unpaired_ttest_majority_vs_minority,
    load_metrics_from_csv,
    filter_time_limited,
    filter_utility_collapse
)

def test_calculate_variance_across_seeds():
    """Test that variance is calculated correctly across seeds for a configuration."""
    # Create mock data with 5 seeds for one configuration
    data = {
        'alpha': [0.1, 0.1, 0.1, 0.1, 0.1],
        'epsilon': [0.5, 0.5, 0.5, 0.5, 0.5],
        'global_accuracy': [0.80, 0.82, 0.79, 0.81, 0.83],
        'majority_accuracy': [0.85, 0.87, 0.84, 0.86, 0.88],
        'minority_accuracy': [0.70, 0.72, 0.69, 0.71, 0.73],
        'seed': [1, 2, 3, 4, 5]
    }
    df = pd.DataFrame(data)
    
    result = calculate_summary_statistics_for_task(df)
    
    assert len(result) == 1
    assert result.iloc[0]['seed_count'] == 5
    # Variance should be non-zero
    assert result.iloc[0]['global_accuracy_variance'] > 0
    assert result.iloc[0]['majority_accuracy_variance'] > 0
    assert result.iloc[0]['minority_accuracy_variance'] > 0

def test_paired_ttest_logic():
    """Test that paired t-test runs without error and returns expected structure."""
    # Mock data with matching seeds for DP and Non-DP
    data = {
        'alpha': [0.1, 0.1, 0.1, 0.1],
        'epsilon': [0.5, 0.5, 0.5, 0.5],
        'seed': [1, 2, 1, 2],
        'global_accuracy': [0.80, 0.82, 0.85, 0.87], # DP, DP, Non-DP, Non-DP
        'is_nondp': [False, False, True, True]
    }
    df = pd.DataFrame(data)
    
    result = run_paired_ttest_dp_vs_nondp(df)
    
    assert 'p_values' in result
    assert 'power_reduced' in result
    # Should have a result for the key "0.1_0.5"
    key = "0.1_0.5"
    assert key in result['p_values']
    assert isinstance(result['p_values'][key], list)
    # Should not be power reduced if we have pairs
    assert result['power_reduced'][key] == False

def test_unpaired_ttest_fallback_to_mannwhitney():
    """Test that Mann-Whitney U is used when valid runs < 3."""
    # Mock data with only 2 runs
    data = {
        'alpha': [0.1, 0.1],
        'epsilon': [0.5, 0.5],
        'majority_accuracy': [0.85, 0.87],
        'minority_accuracy': [0.70, 0.72]
    }
    df = pd.DataFrame(data)
    
    result = run_unpaired_ttest_majority_vs_minority(df)
    
    assert 'p_values' in result
    key = "0.1_0.5"
    assert key in result['p_values']
    # Should be flagged as power reduced
    assert result['power_reduced'][key] == True

def test_filter_time_limited():
    """Test filtering of time-limited rows."""
    data = {
        'accuracy': [0.8, 0.7, 0.9],
        'is_time_limited': [False, True, False]
    }
    df = pd.DataFrame(data)
    
    filtered = filter_time_limited(df)
    assert len(filtered) == 2
    assert not filtered['is_time_limited'].any()

def test_filter_utility_collapse():
    """Test filtering of utility collapse rows."""
    data = {
        'accuracy': [0.8, 0.02, 0.9],
        'epsilon': [0.5, 0.01, 0.5]
    }
    df = pd.DataFrame(data)
    
    filtered = filter_utility_collapse(df)
    assert len(filtered) == 2
    # Check that low accuracy and low epsilon rows are gone
    assert not ((filtered['accuracy'] < 0.05) | (filtered['epsilon'] < 0.05)).any()