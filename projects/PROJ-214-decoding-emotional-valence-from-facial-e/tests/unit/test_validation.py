"""Unit tests for validation functions."""

import numpy as np
import pytest
from validate import calculate_cohens_d, run_permutation_test, run_paired_ttest

def test_cohens_d():
    """Test Cohen's d calculation."""
    # Two identical groups should have d = 0
    group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    group2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    d = calculate_cohens_d(group1, group2)
    assert np.isclose(d, 0.0)
    
    # Groups with known difference
    group1 = np.array([1.0, 2.0, 3.0])
    group2 = np.array([3.0, 4.0, 5.0])
    d = calculate_cohens_d(group1, group2)
    # Manual calculation:
    # mean1 = 2, mean2 = 4, diff = 2
    # pooled_std = sqrt(((1^2 + 1^2 + 1^2) + (1^2 + 1^2 + 1^2)) / (3+3-2)) = sqrt(6/4) = sqrt(1.5)
    # d = 2 / sqrt(1.5) ≈ 1.633
    expected = 2.0 / np.sqrt(1.5)
    assert np.isclose(d, expected, rtol=0.01)

def test_permutation_test_structure():
    """Test that permutation test returns expected structure."""
    observed = np.array([0.6, 0.7, 0.65, 0.72, 0.68])
    baseline = np.array([0.5, 0.52, 0.48, 0.51, 0.49])
    
    result = run_permutation_test(observed, baseline, n_permutations=100)
    
    assert 'p_value' in result
    assert 'permuted_distribution' in result
    assert 'observed_difference' in result
    
    assert result['p_value'] >= 0.0
    assert result['p_value'] <= 1.0
    assert len(result['permuted_distribution']) == 100

def test_paired_ttest_structure():
    """Test that paired t-test returns expected structure."""
    sample1 = np.array([0.6, 0.7, 0.65, 0.72, 0.68])
    sample2 = np.array([0.5, 0.52, 0.48, 0.51, 0.49])
    
    result = run_paired_ttest(sample1, sample2)
    
    assert 't_statistic' in result
    assert 'p_value' in result
    assert 'mean_difference' in result
    
    assert result['p_value'] >= 0.0
    assert result['p_value'] <= 1.0

def test_permutation_test_significance():
    """Test that permutation test detects significant difference."""
    # Create clearly different groups
    observed = np.array([0.8, 0.85, 0.82, 0.88, 0.83])
    baseline = np.array([0.5, 0.52, 0.48, 0.51, 0.49])
    
    result = run_permutation_test(observed, baseline, n_permutations=1000)
    
    # With clearly different groups, p-value should be low
    assert result['p_value'] < 0.05
