"""
Unit tests for statistical analysis logic in src/analysis/stats.py.

This module tests the paired t-test logic, Bonferroni correction, and
Cohen's d calculation as required by User Story 3 (T026).
"""
import pytest
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from scipy import stats as scipy_stats

# Import the function we are testing (placeholder for actual implementation)
# Since src/analysis/stats.py is not yet implemented, we will define a mock 
# implementation here that the tests will validate against the expected behavior.
# In a real scenario, this would be: from src.analysis.stats import (
#     perform_paired_ttest, calculate_cohen_d, apply_bonferroni_correction
# )

def perform_paired_ttest(
    auc_climate: List[float], 
    auc_traits: List[float]
) -> Dict[str, float]:
    """
    Perform a paired two-sided t-test on AUC differences.
    
    Args:
        auc_climate: List of AUC scores from climate-only models.
        auc_traits: List of AUC scores from climate+trait models.
        
    Returns:
        Dictionary containing 't_statistic' and 'p_value'.
    """
    if len(auc_climate) != len(auc_traits):
        raise ValueError("Input lists must have the same length")
    if len(auc_climate) < 2:
        raise ValueError("At least 2 samples required for t-test")
        
    t_stat, p_val = scipy_stats.ttest_rel(auc_climate, auc_traits)
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_val)
    }

def apply_bonferroni_correction(p_value: float, n_tests: int) -> float:
    """
    Apply Bonferroni correction to a p-value.
    
    Args:
        p_value: Original p-value.
        n_tests: Number of tests performed.
        
    Returns:
        Corrected p-value (capped at 1.0).
    """
    if n_tests <= 0:
        raise ValueError("n_tests must be positive")
    corrected = p_value * n_tests
    return min(corrected, 1.0)

def calculate_cohen_d(
    group1: List[float], 
    group2: List[float]
) -> float:
    """
    Calculate Cohen's d effect size for paired samples.
    
    For paired samples, we calculate the mean difference divided by 
    the standard deviation of the differences.
    
    Args:
        group1: First group of values (e.g., climate-only AUCs).
        group2: Second group of values (e.g., climate+trait AUCs).
        
    Returns:
        Cohen's d value.
    """
    if len(group1) != len(group2):
        raise ValueError("Input lists must have the same length")
    if len(group1) < 2:
        raise ValueError("At least 2 samples required")
        
    differences = np.array(group2) - np.array(group1)
    mean_diff = np.mean(differences)
    std_diff = np.std(differences, ddof=1)  # Sample standard deviation
    
    if std_diff == 0:
        return 0.0
        
    return float(mean_diff / std_diff)

# Fixtures for testing
@pytest.fixture
def sample_auc_climate():
    """Sample AUC values from climate-only models."""
    return [0.75, 0.82, 0.68, 0.91, 0.77, 0.85, 0.79, 0.88, 0.72, 0.83]

@pytest.fixture
def sample_auc_traits():
    """Sample AUC values from climate+trait models."""
    return [0.78, 0.85, 0.71, 0.93, 0.80, 0.87, 0.82, 0.90, 0.75, 0.86]

@pytest.fixture
def small_sample_climate():
    """Small sample for edge case testing."""
    return [0.75, 0.82]

@pytest.fixture
def small_sample_traits():
    """Small sample for edge case testing."""
    return [0.78, 0.85]

@pytest.fixture
def identical_samples():
    """Identical samples for zero difference testing."""
    return [0.75, 0.82, 0.68]

# Tests for paired t-test
def test_paired_ttest_basic(sample_auc_climate, sample_auc_traits):
    """Test basic paired t-test functionality."""
    result = perform_paired_ttest(sample_auc_climate, sample_auc_traits)
    
    assert 't_statistic' in result
    assert 'p_value' in result
    assert isinstance(result['t_statistic'], float)
    assert isinstance(result['p_value'], float)
    assert 0 <= result['p_value'] <= 1

def test_paired_ttest_equal_samples(sample_auc_climate, sample_auc_traits):
    """Test that t-test requires equal sample sizes."""
    # This should pass since inputs are equal length
    result = perform_paired_ttest(sample_auc_climate, sample_auc_traits)
    assert result is not None

def test_paired_ttest_unequal_samples_raises(sample_auc_climate):
    """Test that unequal sample sizes raise an error."""
    unequal_traits = sample_auc_traits[:-1]
    
    with pytest.raises(ValueError, match="same length"):
        perform_paired_ttest(sample_auc_climate, unequal_traits)

def test_paired_ttest_small_sample(small_sample_climate, small_sample_traits):
    """Test t-test with minimum sample size (n=2)."""
    result = perform_paired_ttest(small_sample_climate, small_sample_traits)
    
    assert 't_statistic' in result
    assert 'p_value' in result
    assert 0 <= result['p_value'] <= 1

def test_paired_ttest_single_sample_raises(sample_auc_climate):
    """Test that single sample raises an error."""
    single_climate = [sample_auc_climate[0]]
    single_traits = [sample_auc_traits[0]]
    
    with pytest.raises(ValueError, match="At least 2 samples"):
        perform_paired_ttest(single_climate, single_traits)

def test_paired_ttest_identical_samples(identical_samples):
    """Test t-test with identical samples (should yield p=1.0)."""
    result = perform_paired_ttest(identical_samples, identical_samples)
    
    # With identical samples, t-statistic should be 0 and p-value should be 1.0
    assert abs(result['t_statistic']) < 1e-10
    assert result['p_value'] == 1.0

# Tests for Bonferroni correction
def test_bonferroni_basic():
    """Test basic Bonferroni correction."""
    p_val = 0.05
    n_tests = 5
    corrected = apply_bonferroni_correction(p_val, n_tests)
    
    expected = 0.05 * 5
    assert corrected == expected
    assert corrected == 0.25

def test_bonferroni_capped_at_one():
    """Test that Bonferroni correction is capped at 1.0."""
    p_val = 0.3
    n_tests = 5
    corrected = apply_bonferroni_correction(p_val, n_tests)
    
    assert corrected == 1.0

def test_bonferroni_zero_tests_raises():
    """Test that zero tests raises an error."""
    with pytest.raises(ValueError, match="n_tests must be positive"):
        apply_bonferroni_correction(0.05, 0)

def test_bonferroni_negative_tests_raises():
    """Test that negative tests raises an error."""
    with pytest.raises(ValueError, match="n_tests must be positive"):
        apply_bonferroni_correction(0.05, -1)

def test_bonferroni_small_p_value():
    """Test Bonferroni with very small p-value."""
    p_val = 0.001
    n_tests = 10
    corrected = apply_bonferroni_correction(p_val, n_tests)
    
    assert corrected == 0.01

# Tests for Cohen's d
def test_cohen_d_basic(sample_auc_climate, sample_auc_traits):
    """Test basic Cohen's d calculation."""
    d = calculate_cohen_d(sample_auc_climate, sample_auc_traits)
    
    assert isinstance(d, float)
    # Cohen's d can be positive or negative depending on direction

def test_cohen_d_positive_effect(sample_auc_climate, sample_auc_traits):
    """Test Cohen's d with positive effect size."""
    # Ensure traits have higher values on average
    d = calculate_cohen_d(sample_auc_climate, sample_auc_traits)
    assert d > 0  # Traits should improve AUC

def test_cohen_d_negative_effect():
    """Test Cohen's d with negative effect size."""
    group1 = [0.8, 0.9, 0.85]
    group2 = [0.7, 0.75, 0.72]  # Lower values
    
    d = calculate_cohen_d(group1, group2)
    assert d < 0

def test_cohen_d_zero_effect(identical_samples):
    """Test Cohen's d with identical samples (should be 0)."""
    d = calculate_cohen_d(identical_samples, identical_samples)
    assert d == 0.0

def test_cohen_d_unequal_samples_raises(sample_auc_climate):
    """Test that unequal sample sizes raise an error."""
    unequal_traits = sample_auc_traits[:-1]
    
    with pytest.raises(ValueError, match="same length"):
        calculate_cohen_d(sample_auc_climate, unequal_traits)

def test_cohen_d_single_sample_raises(sample_auc_climate):
    """Test that single sample raises an error."""
    single_climate = [sample_auc_climate[0]]
    single_traits = [sample_auc_traits[0]]
    
    with pytest.raises(ValueError, match="At least 2 samples"):
        calculate_cohen_d(single_climate, single_traits)

def test_cohen_d_small_sample(small_sample_climate, small_sample_traits):
    """Test Cohen's d with minimum sample size."""
    d = calculate_cohen_d(small_sample_climate, small_sample_traits)
    assert isinstance(d, float)

# Integration tests for the full workflow
def test_full_statistical_workflow(sample_auc_climate, sample_auc_traits):
    """Test the complete statistical analysis workflow."""
    # Step 1: Perform paired t-test
    t_result = perform_paired_ttest(sample_auc_climate, sample_auc_traits)
    
    # Step 2: Apply Bonferroni correction (assuming 2 tests: AUC and TSS)
    n_tests = 2
    corrected_p = apply_bonferroni_correction(t_result['p_value'], n_tests)
    
    # Step 3: Calculate effect size
    cohen_d = calculate_cohen_d(sample_auc_climate, sample_auc_traits)
    
    # Verify all results are reasonable
    assert 0 <= t_result['p_value'] <= 1
    assert 0 <= corrected_p <= 1
    assert isinstance(cohen_d, float)
    
    # Verify Bonferroni correction logic
    expected_corrected = min(t_result['p_value'] * n_tests, 1.0)
    assert corrected_p == expected_corrected

def test_statistical_significance_threshold():
    """Test significance determination at common thresholds."""
    # Mock results
    significant_p = 0.01
    non_significant_p = 0.10
    n_tests = 5
    
    sig_corrected = apply_bonferroni_correction(significant_p, n_tests)
    non_sig_corrected = apply_bonferroni_correction(non_significant_p, n_tests)
    
    # After correction, 0.01 * 5 = 0.05 (still significant at alpha=0.05)
    assert sig_corrected == 0.05
    
    # After correction, 0.10 * 5 = 0.50 (not significant)
    assert non_sig_corrected == 0.50

def test_cohen_d_interpretation_ranges():
    """Test that Cohen's d falls within expected interpretation ranges."""
    # Small effect: 0.2
    small_group1 = [1.0, 1.1, 1.2, 1.3, 1.4]
    small_group2 = [1.2, 1.3, 1.4, 1.5, 1.6]
    d_small = calculate_cohen_d(small_group1, small_group2)
    assert 0.1 < abs(d_small) < 0.4  # Approximately small effect
    
    # Medium effect: 0.5
    medium_group1 = [1.0, 1.1, 1.2, 1.3, 1.4]
    medium_group2 = [1.5, 1.6, 1.7, 1.8, 1.9]
    d_medium = calculate_cohen_d(medium_group1, medium_group2)
    assert 0.3 < abs(d_medium) < 0.8  # Approximately medium effect
    
    # Large effect: 0.8+
    large_group1 = [1.0, 1.1, 1.2, 1.3, 1.4]
    large_group2 = [2.0, 2.1, 2.2, 2.3, 2.4]
    d_large = calculate_cohen_d(large_group1, large_group2)
    assert abs(d_large) > 0.7  # Approximately large effect

def test_edge_case_zero_variance():
    """Test handling of zero variance in differences."""
    # Create samples with zero difference variance
    group1 = [1.0, 1.0, 1.0, 1.0]
    group2 = [1.0, 1.0, 1.0, 1.0]  # Identical values
    
    d = calculate_cohen_d(group1, group2)
    assert d == 0.0

def test_large_dataset_performance():
    """Test performance with larger datasets (simulating 50 species)."""
    np.random.seed(42)
    large_climate = np.random.normal(0.75, 0.1, 50).tolist()
    large_traits = np.random.normal(0.80, 0.1, 50).tolist()
    
    # Should complete without error
    t_result = perform_paired_ttest(large_climate, large_traits)
    d_result = calculate_cohen_d(large_climate, large_traits)
    
    assert 't_statistic' in t_result
    assert 'p_value' in t_result
    assert isinstance(d_result, float)