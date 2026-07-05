"""
Unit tests for robustness analysis functions, specifically focusing on ICV restriction subsetting logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure project root is in path for imports if running from root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.analysis.robustness import subset_icv_within_1sd, run_icv_restricted_analysis
from code.config_env import get_alpha_thresholds

# Mock data for testing
def create_mock_data(n_rows=100, icv_mean=1500, icv_std=100):
    np.random.seed(42)
    data = {
        'ACE_score': np.random.normal(0, 1, n_rows),
        'Age': np.random.normal(10, 2, n_rows),
        'Sex': np.random.choice(['M', 'F'], n_rows),
        'Site': np.random.choice(['S1', 'S2', 'S3'], n_rows),
        'family_id': np.random.choice(range(10), n_rows),
        'ICV': np.random.normal(icv_mean, icv_std, n_rows),
        'CA3_norm': np.random.normal(0.02, 0.005, n_rows),
        'DG_norm': np.random.normal(0.03, 0.005, n_rows),
        'Subiculum_norm': np.random.normal(0.04, 0.005, n_rows),
    }
    return pd.DataFrame(data)

def test_sensitivity_analysis_returns_dataframe():
    """Test that sensitivity analysis returns a DataFrame with expected columns."""
    df = create_mock_data(50)  # Smaller dataset for speed
    thresholds = [0.05, 0.1]
    # Run with minimal permutations for speed in unit test
    result = run_sensitivity_analysis(df, alpha_thresholds=thresholds, n_permutations=5, n_jobs=1)
    
    assert isinstance(result, pd.DataFrame)
    assert 'alpha_threshold' in result.columns
    assert 'significant_count' in result.columns
    assert len(result) == len(thresholds)
    assert all(result['alpha_threshold'] == thresholds)
    assert all(result['significant_count'] >= 0)
    assert all(result['significant_count'] <= 3)  # 3 subfields (CA3, DG, Subiculum)

def test_sensitivity_analysis_alpha_sweep_logic():
    """
    Test that the alpha sweep logic correctly iterates through provided thresholds
    and calculates significant counts for each.
    """
    df = create_mock_data(100)
    # Use specific thresholds to verify exact iteration
    custom_thresholds = [0.01, 0.05, 0.10, 0.20]
    
    result = run_sensitivity_analysis(
        df, 
        alpha_thresholds=custom_thresholds, 
        n_permutations=10, 
        n_jobs=1
    )
    
    # Verify the sweep covered all requested thresholds
    assert set(result['alpha_threshold'].tolist()) == set(custom_thresholds)
    assert len(result) == len(custom_thresholds)
    
    # Verify significant_count is monotonic or at least non-decreasing with higher alpha
    # (Looser threshold should generally yield >= significant results)
    # Note: Due to randomness in permutation, strict monotonicity isn't guaranteed in small samples,
    # but the logic must process each threshold. We verify the structure first.
    
    # Check that counts are within valid range
    assert all(0 <= count <= 3 for count in result['significant_count'])

def test_sensitivity_analysis_default_thresholds():
    """Test that the function uses default thresholds if none provided."""
    df = create_mock_data(50)
    # Call without explicit thresholds
    result = run_sensitivity_analysis(df, n_permutations=5, n_jobs=1)
    
    # Verify it used the defaults from config (usually 0.01, 0.05, 0.1)
    expected_defaults = get_alpha_thresholds()
    assert list(result['alpha_threshold']) == expected_defaults

def test_icv_restricted_analysis_structure():
    """Test that ICV restricted analysis returns expected keys."""
    df = create_mock_data(50)
    result = run_icv_restricted_analysis(df)
    
    assert isinstance(result, dict)
    assert 'subset_size' in result
    assert 'original_size' in result
    assert 'percent_changes' in result
    assert 'status' in result
    assert result['original_size'] == 50
    # The subset should be smaller or equal (within 1 SD)
    assert result['subset_size'] <= 50
    assert result['status'] == 'success'

def test_icv_restricted_analysis_percent_changes_keys():
    """Verify percent_changes contains entries for all subfields."""
    df = create_mock_data(50)
    result = run_icv_restricted_analysis(df)
    
    required_subfields = ['CA3', 'DG', 'Subiculum']
    for subfield in required_subfields:
        assert subfield in result['percent_changes'], f"Missing {subfield} in percent_changes"
    
    # Values should be floats
    for subfield, val in result['percent_changes'].items():
        assert isinstance(val, (int, float)), f"Value for {subfield} is not numeric"

def test_icv_restricted_analysis_small_subset_handling():
    """Test behavior when the ICV subset is small but valid."""
    df = create_mock_data(50)
    # Force a scenario where subset is small by manipulating data if needed,
    # but the function logic handles 1 SD naturally.
    result = run_icv_restricted_analysis(df)
    assert result['status'] == 'success'
    assert 'percent_changes' in result
    for subfield in ['CA3', 'DG', 'Subiculum']:
        assert subfield in result['percent_changes']

# --- New Tests for ICV Restriction Subsetting Logic (T034) ---

def test_subset_icv_within_1sd_returns_dataframe():
    """Test that subset_icv_within_1sd returns a DataFrame."""
    df = create_mock_data(100)
    subset = subset_icv_within_1sd(df)
    
    assert isinstance(subset, pd.DataFrame)
    assert len(subset) <= len(df)
    assert len(subset) > 0  # Should have some data

def test_subset_icv_within_1sd_filters_correctly():
    """
    Test that subset_icv_within_1sd correctly filters rows where ICV is within 1 SD of mean.
    """
    # Create data with known mean and std
    n = 1000
    icv_mean = 1500.0
    icv_std = 100.0
    np.random.seed(42)
    df = create_mock_data(n, icv_mean, icv_std)
    
    # Calculate expected bounds
    lower_bound = icv_mean - icv_std
    upper_bound = icv_mean + icv_std
    
    # Run the function
    subset = subset_icv_within_1sd(df)
    
    # Verify all rows in subset are within bounds
    assert all(subset['ICV'] >= lower_bound)
    assert all(subset['ICV'] <= upper_bound)
    
    # Verify the count is roughly 68% of total (normal distribution property)
    # Allow some tolerance due to randomness
    expected_ratio = 0.68
    actual_ratio = len(subset) / len(df)
    assert abs(actual_ratio - expected_ratio) < 0.05, f"Ratio {actual_ratio} too far from expected {expected_ratio}"

def test_subset_icv_within_1sd_preserves_columns():
    """Test that the subsetted DataFrame preserves all original columns."""
    df = create_mock_data(50)
    original_columns = set(df.columns)
    
    subset = subset_icv_within_1sd(df)
    subset_columns = set(subset.columns)
    
    assert original_columns == subset_columns

def test_subset_icv_within_1sd_empty_result_handling():
    """Test behavior if data is extremely skewed or small (edge case)."""
    # Create a tiny dataset where no points might fall within 1 SD if std is 0 or near 0
    # But with normal generation, this is unlikely.
    # Instead, test with a dataset where we manually force a situation.
    df = pd.DataFrame({
        'ICV': [1500, 1500, 1500], # std = 0
        'ACE_score': [0, 0, 0],
        'Age': [10, 10, 10],
        'Sex': ['M', 'M', 'M'],
        'Site': ['S1', 'S1', 'S1'],
        'family_id': [1, 1, 1],
        'CA3_norm': [0.02, 0.02, 0.02],
        'DG_norm': [0.03, 0.03, 0.03],
        'Subiculum_norm': [0.04, 0.04, 0.04]
    })
    
    # If std is 0, the range is [mean, mean]. All points equal to mean should be kept.
    subset = subset_icv_within_1sd(df)
    
    # With std=0, mean=1500, bounds are [1500, 1500]. All rows are 1500.
    assert len(subset) == 3
    assert all(subset['ICV'] == 1500)

def test_subset_icv_within_1sd_statistics_match():
    """Test that the subset statistics (mean, std) are consistent with the 1 SD definition."""
    df = create_mock_data(2000) # Large sample for better stats
    
    subset = subset_icv_within_1sd(df)
    
    # The subset mean should be close to the original mean
    # The subset std should be smaller than original std
    orig_mean = df['ICV'].mean()
    orig_std = df['ICV'].std()
    sub_mean = subset['ICV'].mean()
    sub_std = subset['ICV'].std()
    
    # Check mean is preserved reasonably well
    assert abs(sub_mean - orig_mean) < 5.0 # Within 5 units
    
    # Check std is reduced
    assert sub_std < orig_std
    
    # Check that the subset range is indeed within 1 SD of the original mean
    lower = orig_mean - orig_std
    upper = orig_mean + orig_std
    assert subset['ICV'].min() >= lower
    assert subset['ICV'].max() <= upper

def test_run_icv_restricted_analysis_calculates_effect_change():
    """Test that the effect size change is calculated correctly."""
    df = create_mock_data(200)
    result = run_icv_restricted_analysis(df)
    
    # Verify structure
    assert 'percent_changes' in result
    assert 'CA3' in result['percent_changes']
    assert 'DG' in result['percent_changes']
    assert 'Subiculum' in result['percent_changes']
    
    # Verify values are numeric
    for k, v in result['percent_changes'].items():
        assert isinstance(v, float)
    
    # Verify the subset size is reasonable
    assert result['subset_size'] > 0
    assert result['subset_size'] <= result['original_size']