"""
tests/integration/test_correlations.py
--------------------------------------

Integration tests for correlation analysis (T019).
"""
import numpy as np
import pandas as pd
from code.analysis.correlations import run_correlations_with_fd_covariate, apply_fdr_correction


def test_correlation_with_synthetic_data():
    """
    Test T019: Verify correlation (r, p, q) values on synthetic data.
    
    We create a dataset with a known linear relationship between
    a metric and a score, plus noise.
    """
    np.random.seed(42)
    n_subjects = 50
    
    # Create synthetic data with known correlation
    # y = 2*x + noise
    x = np.random.randn(n_subjects)
    noise = np.random.randn(n_subjects) * 0.5
    y = 2 * x + noise
    
    # Create DataFrame
    df = pd.DataFrame({
        'subject_id': range(n_subjects),
        'metric_val': x,
        'score': y,
        'fd': np.random.rand(n_subjects) * 0.2 # FD covariate
    })
    
    # Run correlation (metric vs score, controlling for FD)
    # Note: run_correlations_with_fd_covariate expects specific column names
    # We adapt the synthetic data to match expected schema
    df_renamed = df.rename(columns={
        'metric_val': 'participation_coef_mean',
        'score': 'motor_score',
        'fd': 'fd'
    })
    
    # Add dummy columns required by the function
    df_renamed['modularity'] = np.random.rand(n_subjects)
    df_renamed['global_efficiency'] = np.random.rand(n_subjects)
    df_renamed['within_module_degree_mean'] = np.random.rand(n_subjects)
    
    # Run correlations
    results = run_correlations_with_fd_covariate(
        df_renamed,
        metric_cols=['participation_coef_mean', 'modularity', 'global_efficiency', 'within_module_degree_mean'],
        outcome_col='motor_score',
        covariate_col='fd'
    )
    
    # Assertions
    assert isinstance(results, pd.DataFrame)
    assert 'metric_name' in results.columns
    assert 'r' in results.columns
    assert 'p' in results.columns
    assert 'q' in results.columns
    assert 'significant' in results.columns
    
    # Check that the true correlation (participation_coef_mean vs motor_score)
    # is detected as significant (p < 0.05)
    true_metric = results[results['metric_name'] == 'participation_coef_mean']
    if not true_metric.empty:
        p_val = true_metric['p'].values[0]
        assert p_val < 0.05, f"Expected p < 0.05 for true correlation, got {p_val}"
    
    # Check FDR correction
    assert (results['q'] >= 0).all() and (results['q'] <= 1).all()