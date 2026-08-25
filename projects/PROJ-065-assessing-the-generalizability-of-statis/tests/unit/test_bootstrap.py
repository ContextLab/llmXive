"""
Unit tests for stratified bootstrap logic in bootstrap_engine.py.

Tests T019: Unit test for stratified bootstrap logic with N=50.
"""
import pytest
import random
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from bootstrap_engine import stratified_resample, calculate_stability_rate, BootstrapResult
from config import MAX_ITERATIONS

# Set seed for reproducibility in tests
TEST_SEED = 42
random.seed(TEST_SEED)
np.random.seed(TEST_SEED)

@pytest.fixture
def sample_data_n50():
    """
    Create a synthetic dataset with N=50 for testing stratified resampling.
    Structure mimics expected baseline_metrics.csv format.
    """
    n_samples = 50
    # Create 3 strata (disciplines) with roughly equal distribution
    strata = ['psychology'] * 17 + ['economics'] * 17 + ['biology'] * 16
    
    data = {
        'osf_id': [f'study_{i:03d}' for i in range(n_samples)],
        'discipline': strata,
        'original_p_value': np.random.uniform(0.01, 0.15, n_samples),
        'sample_size': np.random.randint(100, 500, n_samples),
        'effect_size': np.random.normal(0.3, 0.1, n_samples)
    }
    
    return pd.DataFrame(data)

@pytest.fixture
def sample_data_imbalanced():
    """
    Create a dataset with imbalanced strata to test edge cases.
    """
    n_samples = 50
    # 40 psychology, 5 economics, 5 biology
    strata = ['psychology'] * 40 + ['economics'] * 5 + ['biology'] * 5
    
    data = {
        'osf_id': [f'study_{i:03d}' for i in range(n_samples)],
        'discipline': strata,
        'original_p_value': np.random.uniform(0.01, 0.15, n_samples),
        'sample_size': np.random.randint(100, 500, n_samples),
        'effect_size': np.random.normal(0.3, 0.1, n_samples)
    }
    
    return pd.DataFrame(data)

def test_stratified_resample_returns_correct_size(sample_data_n50):
    """
    Test that stratified_resample returns a DataFrame of the same size as input.
    """
    resampled = stratified_resample(sample_data_n50, strata_col='discipline', seed=TEST_SEED)
    assert len(resampled) == len(sample_data_n50), "Resampled data must have same size as original"

def test_stratified_resample_preserves_strata_distribution(sample_data_n50):
    """
    Test that stratified_resample preserves the original strata distribution.
    """
    original_counts = sample_data_n50['discipline'].value_counts()
    resampled = stratified_resample(sample_data_n50, strata_col='discipline', seed=TEST_SEED)
    resampled_counts = resampled['discipline'].value_counts()
    
    # Check that counts match exactly (stratified sampling with replacement within strata)
    for stratum in original_counts.index:
        assert original_counts[stratum] == resampled_counts[stratum], \
            f"Stratum {stratum} distribution not preserved: {original_counts[stratum]} != {resampled_counts[stratum]}"

def test_stratified_resample_with_imbalanced_data(sample_data_imbalanced):
    """
    Test stratified resampling with imbalanced strata.
    """
    resampled = stratified_resample(sample_data_imbalanced, strata_col='discipline', seed=TEST_SEED)
    
    assert len(resampled) == 50, "Resampled data must have correct size"
    
    # Verify each stratum is represented
    strata_counts = resampled['discipline'].value_counts()
    assert 'psychology' in strata_counts.index
    assert 'economics' in strata_counts.index
    assert 'biology' in strata_counts.index
    
    # Check specific counts
    assert strata_counts['psychology'] == 40
    assert strata_counts['economics'] == 5
    assert strata_counts['biology'] == 5

def test_stratified_resample_deterministic_with_seed(sample_data_n50):
    """
    Test that stratified_resample produces identical results with the same seed.
    """
    resample1 = stratified_resample(sample_data_n50, strata_col='discipline', seed=TEST_SEED)
    resample2 = stratified_resample(sample_data_n50, strata_col='discipline', seed=TEST_SEED)
    
    # Compare all columns
    pd.testing.assert_frame_equal(resample1.reset_index(drop=True), 
                                resample2.reset_index(drop=True),
                                check_dtype=True)

def test_stratified_resample_changes_with_different_seed(sample_data_n50):
    """
    Test that stratified_resample produces different results with different seeds.
    """
    resample1 = stratified_resample(sample_data_n50, strata_col='discipline', seed=TEST_SEED)
    resample2 = stratified_resample(sample_data_n50, strata_col='discipline', seed=TEST_SEED + 1)
    
    # They should be different (with high probability)
    # Note: There's a tiny chance they could be identical by coincidence, but extremely unlikely
    are_equal = resample1.reset_index(drop=True).equals(resample2.reset_index(drop=True))
    assert not are_equal, "Different seeds should produce different resamples"

def test_stratified_resample_handles_single_stratum():
    """
    Test stratified resampling with only one stratum.
    """
    n_samples = 50
    data = {
        'osf_id': [f'study_{i:03d}' for i in range(n_samples)],
        'discipline': ['psychology'] * n_samples,
        'original_p_value': np.random.uniform(0.01, 0.15, n_samples),
        'sample_size': np.random.randint(100, 500, n_samples),
        'effect_size': np.random.normal(0.3, 0.1, n_samples)
    }
    df = pd.DataFrame(data)
    
    resampled = stratified_resample(df, strata_col='discipline', seed=TEST_SEED)
    
    assert len(resampled) == 50
    assert all(resampled['discipline'] == 'psychology')

def test_stratified_resample_preserves_data_types(sample_data_n50):
    """
    Test that stratified_resample preserves data types.
    """
    resampled = stratified_resample(sample_data_n50, strata_col='discipline', seed=TEST_SEED)
    
    assert resampled['osf_id'].dtype == sample_data_n50['osf_id'].dtype
    assert resampled['discipline'].dtype == sample_data_n50['discipline'].dtype
    assert resampled['original_p_value'].dtype == sample_data_n50['original_p_value'].dtype
    assert resampled['sample_size'].dtype == sample_data_n50['sample_size'].dtype
    assert resampled['effect_size'].dtype == sample_data_n50['effect_size'].dtype

def test_stratified_resample_with_n50_multiple_times(sample_data_n50):
    """
    Test that stratified resampling works correctly when called multiple times.
    """
    results = []
    for i in range(10):
        resampled = stratified_resample(sample_data_n50, strata_col='discipline', seed=TEST_SEED + i)
        results.append(resampled)
        assert len(resampled) == 50
        
        # Verify strata distribution for each
        counts = resampled['discipline'].value_counts()
        assert len(counts) == 3  # All 3 disciplines present

def test_stratified_resample_edge_case_small_stratum():
    """
    Test stratified resampling when one stratum has very few samples.
    """
    # Create data with one stratum having only 1 sample
    data = {
        'osf_id': [f'study_{i:03d}' for i in range(50)],
        'discipline': ['psychology'] * 48 + ['economics'] * 1 + ['biology'] * 1,
        'original_p_value': np.random.uniform(0.01, 0.15, 50),
        'sample_size': np.random.randint(100, 500, 50),
        'effect_size': np.random.normal(0.3, 0.1, 50)
    }
    df = pd.DataFrame(data)
    
    resampled = stratified_resample(df, strata_col='discipline', seed=TEST_SEED)
    
    assert len(resampled) == 50
    counts = resampled['discipline'].value_counts()
    assert counts['economics'] == 1
    assert counts['biology'] == 1
    assert counts['psychology'] == 48

def test_stability_rate_calculation_with_resampled_data(sample_data_n50):
    """
    Test that stability rate calculation works with stratified resampled data.
    """
    # Run stratified resampling
    resampled = stratified_resample(sample_data_n50, strata_col='discipline', seed=TEST_SEED)
    
    # Simulate p-values from bootstrap iterations
    n_iterations = 100
    p_values = np.random.uniform(0.01, 0.10, n_iterations)
    
    # Calculate stability rate
    stability_rate = calculate_stability_rate(p_values, threshold=0.05)
    
    assert 0.0 <= stability_rate <= 1.0
    assert isinstance(stability_rate, float)

def test_stability_rate_with_all_significant():
    """
    Test stability rate when all p-values are significant.
    """
    p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.049])
    stability_rate = calculate_stability_rate(p_values, threshold=0.05)
    
    assert stability_rate == 1.0

def test_stability_rate_with_none_significant():
    """
    Test stability rate when no p-values are significant.
    """
    p_values = np.array([0.06, 0.07, 0.08, 0.09, 0.10])
    stability_rate = calculate_stability_rate(p_values, threshold=0.05)
    
    assert stability_rate == 0.0

def test_stability_rate_with_mixed_values():
    """
    Test stability rate with mixed significant and non-significant p-values.
    """
    p_values = np.array([0.01, 0.04, 0.06, 0.09, 0.03])
    stability_rate = calculate_stability_rate(p_values, threshold=0.05)
    
    # 3 out of 5 are significant (0.01, 0.04, 0.03)
    expected_rate = 3.0 / 5.0
    assert abs(stability_rate - expected_rate) < 1e-6

def test_bootstrap_result_creation():
    """
    Test that BootstrapResult can be created with expected fields.
    """
    result = BootstrapResult(
        study_id="test_study",
        baseline_stability_rate=0.75,
        alt_spec_stability_rates=[0.70, 0.68, 0.72, 0.69, 0.71],
        sensitivity_rates={
            'sampling_rate_at_0.01': 0.60,
            'sampling_rate_at_0.05': 0.75,
            'sampling_rate_at_0.10': 0.85,
            'specification_rate_at_0.01': 0.55,
            'specification_rate_at_0.05': 0.70,
            'specification_rate_at_0.10': 0.80
        },
        iterations_performed=1000
    )
    
    assert result.study_id == "test_study"
    assert result.baseline_stability_rate == 0.75
    assert len(result.alt_spec_stability_rates) == 5
    assert result.iterations_performed == 1000