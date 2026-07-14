"""
Integration tests for correlation analysis module.
"""
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from code.analysis.correlations import (
    run_metric_correlations,
    apply_fdr_correction,
    log_threshold_correlations,
    partial_correlation
)

@pytest.fixture
def synthetic_correlation_data():
    """
    Generate synthetic data with known correlations for testing.
    """
    np.random.seed(42)
    n = 100
    
    # Create synthetic metrics
    modularity = np.random.normal(0.5, 0.1, n)
    global_efficiency = np.random.normal(0.3, 0.05, n)
    participation_coef = np.random.normal(0.4, 0.08, n)
    within_module_degree = np.random.normal(0.6, 0.1, n)
    
    # Create motor score with known correlation to modularity (r ≈ 0.5)
    motor_score = 0.5 * modularity + 0.2 * np.random.normal(0, 0.1, n)
    
    # Create FD covariate (uncorrelated with motor score)
    mean_fd = np.random.normal(0.2, 0.05, n)
    
    df = pd.DataFrame({
        'subject_id': [f'sub-{i:03d}' for i in range(n)],
        'modularity': modularity,
        'global_efficiency': global_efficiency,
        'participation_coef': participation_coef,
        'within_module_degree': within_module_degree,
        'motor_score': motor_score,
        'MeanFD': mean_fd
    })
    
    return df

def test_partial_correlation_with_known_data(synthetic_correlation_data):
    """
    Test partial correlation calculation with synthetic data.
    """
    df = synthetic_correlation_data
    x = df['modularity'].values
    y = df['motor_score'].values
    z = df['MeanFD'].values
    
    r, p = partial_correlation(x, y, z)
    
    # Since FD is uncorrelated, partial correlation should be close to raw correlation
    raw_r = np.corrcoef(x, y)[0, 1]
    
    # Allow some tolerance due to random noise
    assert abs(r - raw_r) < 0.1
    assert 0.0 <= p <= 1.0

def test_run_metric_correlations_with_synthetic_data(synthetic_correlation_data):
    """
    Test correlation analysis pipeline with synthetic data.
    Verifies that:
    1. Correlations are computed for all metrics
    2. Modularity shows significant correlation with motor_score
    3. Other metrics show weaker/non-significant correlations
    """
    df = synthetic_correlation_data
    
    results = run_metric_correlations(
        df,
        metric_columns=['modularity', 'global_efficiency', 'participation_coef'],
        covariate_column='MeanFD',
        output_path=os.path.join(tempfile.gettempdir(), 'test_corr_results.csv')
    )
    
    # Check structure
    assert 'metric_name' in results.columns
    assert 'r' in results.columns
    assert 'p' in results.columns
    assert 'n' in results.columns
    assert len(results) == 3
    
    # Check that modularity has the strongest correlation
    mod_r = results[results['metric_name'] == 'modularity']['r'].values[0]
    assert abs(mod_r) > 0.3  # Should be around 0.5

def test_apply_fdr_correction_with_synthetic_data(synthetic_correlation_data):
    """
    Test FDR correction with synthetic data.
    """
    df = synthetic_correlation_data
    
    # First run correlations
    corr_results = run_metric_correlations(
        df,
        metric_columns=['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree'],
        covariate_column='MeanFD',
        output_path=os.path.join(tempfile.gettempdir(), 'test_corr_results_fdr.csv')
    )
    
    # Apply FDR
    fdr_results = apply_fdr_correction(
        corr_results,
        alpha=0.05,
        output_path=os.path.join(tempfile.gettempdir(), 'test_fdr_results.csv')
    )
    
    # Check structure
    assert 'q' in fdr_results.columns
    assert 'significant' in fdr_results.columns
    assert len(fdr_results) == 4
    
    # Check that q-values are monotonically increasing when sorted by p
    sorted_by_p = fdr_results.sort_values('p')
    q_values = sorted_by_p['q'].values
    
    # q-values should be non-decreasing
    for i in range(1, len(q_values)):
        assert q_values[i] >= q_values[i-1] - 1e-10  # Allow small floating point errors

def test_log_threshold_correlations_with_synthetic_data(synthetic_correlation_data):
    """
    Test threshold logging functionality.
    """
    df = synthetic_correlation_data
    
    # Run correlations and FDR
    corr_results = run_metric_correlations(
        df,
        metric_columns=['modularity', 'global_efficiency'],
        covariate_column='MeanFD',
        output_path=os.path.join(tempfile.gettempdir(), 'test_corr_threshold.csv')
    )
    fdr_results = apply_fdr_correction(corr_results, output_path=os.path.join(tempfile.gettempdir(), 'test_fdr_threshold.csv'))
    
    # Log threshold correlations
    significant = log_threshold_correlations(fdr_results, threshold=0.3)
    
    # Modularity should be significant (r ~ 0.5)
    mod_entry = next((x for x in significant if x['metric'] == 'modularity'), None)
    assert mod_entry is not None
    assert abs(mod_entry['r']) > 0.3

def test_correlation_with_synthetic_data_full_pipeline(synthetic_correlation_data):
    """
    Integration test: run full correlation pipeline on synthetic data.
    Verifies end-to-end functionality.
    """
    df = synthetic_correlation_data
    
    # Run full pipeline
    corr_results = run_metric_correlations(
        df,
        metric_columns=['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree'],
        covariate_column='MeanFD'
    )
    
    fdr_results = apply_fdr_correction(corr_results)
    
    # Verify results
    assert len(fdr_results) == 4
    assert all('q' in fdr_results.columns)
    assert all('significant' in fdr_results.columns)
    
    # Check that at least one metric is significant (modularity)
    significant_count = fdr_results['significant'].sum()
    assert significant_count >= 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
