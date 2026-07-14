"""
Integration test for correlation analysis module.
Task: T019
"""
import os
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

from code.analysis.correlations import (
    load_metrics_data,
    perform_pca_on_metrics,
    save_pca_results,
    generate_full_metrics,
    save_full_metrics,
    run_correlations_with_fd_covariate,
    apply_fdr_correction,
    log_significant_correlations
)

@pytest.fixture
def synthetic_data():
    """Generate synthetic data with known correlations."""
    np.random.seed(42)
    n_subjects = 100
    
    # Create metrics with known correlations to motor score
    modularity = np.random.normal(0.5, 0.1, n_subjects)
    global_eff = np.random.normal(0.3, 0.05, n_subjects)
    participation = np.random.normal(0.4, 0.08, n_subjects)
    within_module = np.random.normal(0.6, 0.1, n_subjects)
    
    # Create motor score with known correlation to modularity
    motor_score = 2 * modularity + np.random.normal(0, 0.05, n_subjects)
    fd = np.random.normal(0.2, 0.05, n_subjects)
    
    df = pd.DataFrame({
        'subject_id': [f'sub_{i:03d}' for i in range(n_subjects)],
        'modularity': modularity,
        'global_efficiency': global_eff,
        'participation_coef': participation,
        'within_module_degree': within_module,
        'motor_score': motor_score,
        'MeanFD': fd
    })
    
    return df

def test_correlation_with_synthetic_data(synthetic_data):
    """
    Test correlation analysis on synthetic data with known correlations.
    Verifies that r, p, and q values are computed correctly.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "aggregated_metrics.csv")
        synthetic_data.to_csv(input_path, index=False)
        
        # Load data
        loaded_df = load_metrics_data(input_path)
        assert len(loaded_df) == 100
        
        # Perform PCA
        pca, factor_df = perform_pca_on_metrics(loaded_df)
        assert 'pca_factor_1' in factor_df.columns
        assert len(factor_df) == 100
        
        # Save PCA results
        loadings_path = os.path.join(tmpdir, "pca_loadings.csv")
        scores_path = os.path.join(tmpdir, "factor_scores.csv")
        save_pca_results(pca, factor_df, loadings_path, scores_path)
        
        # Verify files created
        assert os.path.exists(loadings_path)
        assert os.path.exists(scores_path)
        
        # Generate full metrics
        full_df = generate_full_metrics(loaded_df, factor_df)
        assert 'pca_factor_1' in full_df.columns
        assert len(full_df) == 100
        
        # Save full metrics
        full_path = os.path.join(tmpdir, "full_metrics.csv")
        save_full_metrics(full_df, full_path)
        assert os.path.exists(full_path)
        
        # Run correlations
        corr_results = run_correlations_with_fd_covariate(full_df)
        
        # Verify correlation results
        assert len(corr_results) == 4  # 4 metrics
        
        # Check that modularity has strong correlation (should be ~0.9+ due to construction)
        modularity_corr = corr_results[corr_results['metric_name'] == 'modularity']
        assert len(modularity_corr) == 1
        assert modularity_corr['r'].values[0] > 0.8  # Strong correlation
        assert modularity_corr['p'].values[0] < 0.001  # Significant
        
        # Apply FDR correction
        corr_results = apply_fdr_correction(corr_results)
        
        # Verify FDR columns added
        assert 'q' in corr_results.columns
        assert 'significant' in corr_results.columns
        
        # Verify that modularity is still significant after FDR
        assert modularity_corr['significant'].values[0] == True
        
        # Log significant correlations
        significant = log_significant_correlations(corr_results, threshold=0.3)
        assert len(significant) >= 1  # At least modularity should be significant
        
        # Verify correlation values match expectations
        r_val = modularity_corr['r'].values[0]
        p_val = modularity_corr['p'].values[0]
        
        # Check r is in expected range (should be very high due to construction)
        assert 0.8 < r_val < 1.0
        
        # Check p-value is very small
        assert p_val < 0.001
        
        print(f"Correlation test passed: r={r_val:.3f}, p={p_val:.6f}")