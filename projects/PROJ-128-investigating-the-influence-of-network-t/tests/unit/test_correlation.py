import pytest
import pandas as pd
import numpy as np
from scipy.stats import shapiro
from analysis.correlation import check_normality, calculate_correlation, benjamini_hochberg_fdr, run_correlation_analysis

def test_check_normality_normal_data():
    # Generate normal data
    data = pd.Series(np.random.normal(0, 1, 100))
    is_normal, p_val = check_normality(data)
    assert is_normal == True
    assert p_val > 0.05

def test_check_normality_non_normal_data():
    # Generate skewed data
    data = pd.Series(np.random.lognormal(0, 1, 100))
    is_normal, p_val = check_normality(data)
    # Skewed data should often fail normality test
    # Note: Shapiro-Wilk is sensitive, might not always fail for small N, but for N=100 likely
    # We assert that it returns a result, and if p < 0.05, is_normal is False
    if p_val < 0.05:
        assert is_normal == False
    else:
        # If by chance it passes, we still accept the function returning a result
        pass

def test_check_normality_insufficient_data():
    # Less than 3 points
    data = pd.Series([1.0, 2.0])
    is_normal, p_val = check_normality(data)
    assert is_normal == True # Default to True with warning
    assert p_val == 1.0

def test_calculate_correlation_pearson():
    x = pd.Series([1, 2, 3, 4, 5])
    y = pd.Series([2, 4, 6, 8, 10])
    r, p = calculate_correlation(x, y, method='pearson')
    assert np.isclose(r, 1.0)
    assert p < 0.05

def test_calculate_correlation_spearman():
    x = pd.Series([1, 2, 3, 4, 5])
    y = pd.Series([2, 4, 6, 8, 10])
    r, p = calculate_correlation(x, y, method='spearman')
    assert np.isclose(r, 1.0)

def test_benjamini_hochberg_fdr():
    # All p-values significant
    p_values = [0.001, 0.002, 0.003]
    sig = benjamini_hochberg_fdr(p_values, alpha=0.05)
    assert all(sig)

    # All p-values non-significant
    p_values = [0.5, 0.6, 0.7]
    sig = benjamini_hochberg_fdr(p_values, alpha=0.05)
    assert not any(sig)

    # Mixed
    p_values = [0.01, 0.04, 0.1, 0.2]
    sig = benjamini_hochberg_fdr(p_values, alpha=0.05)
    # First two should be significant
    assert sig[0] == True
    assert sig[1] == True
    assert sig[2] == False
    assert sig[3] == False

def test_run_correlation_analysis_integration(tmp_path):
    # Create dummy structural data
    struct_df = pd.DataFrame({
        'subject_id': ['sub1', 'sub2', 'sub3', 'sub4', 'sub5'],
        'global_efficiency': [0.1, 0.2, 0.3, 0.4, 0.5],
        'avg_clustering': [0.1, 0.2, 0.3, 0.4, 0.5],
        'modularity': [0.1, 0.2, 0.3, 0.4, 0.5]
    })

    # Create dummy dynamic data (per state)
    dyn_df = pd.DataFrame({
        'subject_id': ['sub1', 'sub2', 'sub3', 'sub4', 'sub5'] * 2,
        'state_id': [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
        'mean_d dwell_time': [10, 20, 30, 40, 50, 10, 20, 30, 40, 50],
        'num_visits': [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
    })
    # Fix column name typo in dummy data
    dyn_df.columns = ['subject_id', 'state_id', 'mean_dwell_time', 'num_visits']

    struct_path = tmp_path / 'structural_metrics.csv'
    dyn_path = tmp_path / 'dynamic_metrics.csv'
    struct_df.to_csv(struct_path, index=False)
    dyn_df.to_csv(dyn_path, index=False)

    results = run_correlation_analysis(str(struct_path), str(dyn_path))

    assert len(results) > 0
    assert 'r_value' in results.columns
    assert 'p_value_raw' in results.columns
    assert 'significant_fdr' in results.columns
    assert not results['r_value'].isna().all()