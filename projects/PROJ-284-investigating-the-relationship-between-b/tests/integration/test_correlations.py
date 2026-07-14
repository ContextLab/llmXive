import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.correlations import (
    run_correlations_with_fd_covariate,
    apply_fdr_correction,
    perform_pca_on_metrics,
    generate_full_metrics
)

@pytest.fixture
def synthetic_metrics():
    """Generate synthetic metrics data with known correlations."""
    np.random.seed(42)
    n_subjects = 100
    
    # Create known correlations
    # Metric 1: positively correlated with motor score
    # Metric 2: negatively correlated with motor score
    # FD: uncorrelated with motor score (for control)
    
    motor_scores = np.random.normal(0, 1, n_subjects)
    fd = np.random.normal(0, 0.5, n_subjects)
    
    # Create metrics with known relationships
    modularity = 0.5 * motor_scores + np.random.normal(0, 0.3, n_subjects)
    global_efficiency = -0.4 * motor_scores + np.random.normal(0, 0.3, n_subjects)
    participation_coef = 0.3 * motor_scores + np.random.normal(0, 0.3, n_subjects)
    within_module_degree = 0.1 * motor_scores + np.random.normal(0, 0.3, n_subjects)
    
    df = pd.DataFrame({
        'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
        'modularity': modularity,
        'global_efficiency': global_efficiency,
        'participation_coef': participation_coef,
        'within_module_degree': within_module_degree,
        'fd': fd
    })
    
    return df

@pytest.fixture
def synthetic_pca_data():
    """Generate synthetic data for PCA testing."""
    np.random.seed(123)
    n_subjects = 50
    
    df = pd.DataFrame({
        'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
        'modularity': np.random.normal(0, 1, n_subjects),
        'global_efficiency': np.random.normal(0, 1, n_subjects),
        'participation_coef': np.random.normal(0, 1, n_subjects),
        'within_module_degree': np.random.normal(0, 1, n_subjects)
    })
    
    return df

def test_correlation_with_synthetic_data(synthetic_metrics):
    """
    Integration test: verify correlation analysis on synthetic data.
    
    Checks:
    1. Correlation coefficients match expected direction
    2. P-values are reasonable for the sample size
    3. FDR correction is applied correctly
    4. Significant correlations are identified correctly
    """
    # Run correlation analysis
    results = run_correlations_with_fd_covariate(synthetic_metrics)
    
    # Verify results structure
    assert not results.empty, "Results DataFrame should not be empty"
    assert 'metric_name' in results.columns, "Results should have metric_name column"
    assert 'r' in results.columns, "Results should have r column"
    assert 'p' in results.columns, "Results should have p column"
    assert 'q' in results.columns, "Results should have q (FDR) column"
    assert 'significant' in results.columns, "Results should have significant column"
    
    # Check that modularity has positive correlation (we created it with +0.5 coefficient)
    modularity_row = results[results['metric_name'] == 'modularity']
    assert not modularity_row.empty, "Modularity result should exist"
    assert modularity_row['r'].values[0] > 0, "Modularity should have positive correlation"
    assert modularity_row['r'].values[0] > 0.3, "Modularity correlation should be > 0.3"
    
    # Check that global_efficiency has negative correlation (we created it with -0.4 coefficient)
    ge_row = results[results['metric_name'] == 'global_efficiency']
    assert not ge_row.empty, "Global efficiency result should exist"
    assert ge_row['r'].values[0] < 0, "Global efficiency should have negative correlation"
    
    # Verify FDR correction was applied (q values should be different from p values)
    assert not results['p'].equals(results['q']), "FDR correction should modify p-values"
    
    # Verify significance flag is set based on q < 0.05
    significant_count = results['significant'].sum()
    assert significant_count >= 0, "Should have non-negative significant count"
    
    # For synthetic data with strong correlations, at least one should be significant
    # (with n=100, r=0.5 should be significant after FDR)
    assert significant_count >= 1, "At least one metric should be significant in synthetic data"

def test_fdr_correction_accuracy(synthetic_metrics):
    """Test that FDR correction produces valid q-values."""
    results = run_correlations_with_fd_covariate(synthetic_metrics)
    
    # Q-values should be in [0, 1]
    assert all((results['q'] >= 0) & (results['q'] <= 1)), "Q-values should be between 0 and 1"
    
    # Q-values should be monotonically increasing when sorted by p-values
    sorted_results = results.sort_values('p')
    sorted_q = sorted_results['q'].values
    assert all(np.diff(sorted_q) >= -1e-10), "Q-values should be roughly monotonic with p-values"

def test_pca_on_synthetic_data(synthetic_pca_data):
    """Test PCA implementation on synthetic data."""
    loadings, scores = perform_pca_on_metrics(synthetic_pca_data)
    
    # Verify loadings structure
    assert not loadings.empty, "Loadings should not be empty"
    assert 'component_1' in loadings.columns, "Loadings should have component_1"
    assert 'component_2' in loadings.columns, "Loadings should have component_2"
    assert len(loadings) == 4, "Loadings should have 4 rows (one per metric)"
    
    # Verify scores structure
    assert not scores.empty, "Scores should not be empty"
    assert 'subject_id' in scores.columns, "Scores should have subject_id"
    assert 'pca_factor_1' in scores.columns, "Scores should have pca_factor_1"
    assert len(scores) == len(synthetic_pca_data), "Scores should have same number of subjects"
    
    # Verify scores are numeric
    assert pd.api.types.is_numeric_dtype(scores['pca_factor_1']), "pca_factor_1 should be numeric"

def test_full_metrics_generation(synthetic_metrics, synthetic_pca_data):
    """Test merging of metrics and PCA scores."""
    # Run PCA
    _, pca_scores = perform_pca_on_metrics(synthetic_pca_data)
    
    # Generate full metrics
    full_metrics = generate_full_metrics(synthetic_pca_data, pca_scores)
    
    # Verify structure
    assert not full_metrics.empty, "Full metrics should not be empty"
    assert 'subject_id' in full_metrics.columns, "Should have subject_id"
    assert 'modularity' in full_metrics.columns, "Should have modularity"
    assert 'pca_factor_1' in full_metrics.columns, "Should have pca_factor_1"
    
    # Verify all original metrics are present
    expected_metrics = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    for metric in expected_metrics:
        assert metric in full_metrics.columns, f"Should have {metric}"