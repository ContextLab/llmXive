"""
Unit tests for correlation analysis functions.
"""
import pytest
import pandas as pd
import numpy as np
from code.analysis.correlations import (
    compute_correlations,
    apply_fdr_correction,
    log_significant_correlations,
    CORRELATION_THRESHOLD
)
from code.logging_config import get_logger

logger = get_logger(__name__)

@pytest.fixture
def sample_metrics_df():
    """Create a sample DataFrame for testing."""
    np.random.seed(42)
    n_subjects = 100
    
    df = pd.DataFrame({
        'subject_id': [f'sub_{i}' for i in range(n_subjects)],
        'modularity': np.random.randn(n_subjects) * 0.1 + 0.5,
        'global_efficiency': np.random.randn(n_subjects) * 0.05 + 0.3,
        'participation_coef': np.random.randn(n_subjects) * 0.02 + 0.1,
        'within_module_degree': np.random.randn(n_subjects) * 0.03 + 0.2,
        'motor_score': np.random.randn(n_subjects) * 5 + 50,
        'fd': np.random.randn(n_subjects) * 0.1 + 0.2
    })
    
    return df

def test_compute_correlations_basic(sample_metrics_df):
    """Test basic correlation computation."""
    metric_cols = ['modularity', 'global_efficiency']
    results = compute_correlations(sample_metrics_df, metric_cols)
    
    assert isinstance(results, pd.DataFrame)
    assert 'metric_name' in results.columns
    assert 'r' in results.columns
    assert 'p' in results.columns
    assert len(results) == len(metric_cols)
    
    logger.log("test_compute_correlations_basic", n_results=len(results))

def test_compute_correlations_with_covariate(sample_metrics_df):
    """Test correlation computation with FD covariate."""
    metric_cols = ['participation_coef']
    results = compute_correlations(sample_metrics_df, metric_cols, covariate_col='fd')
    
    assert 'covariate_controlled' in results.columns
    assert all(results['covariate_controlled'])
    
    logger.log("test_compute_correlations_with_covariate")

def test_apply_fdr_correction(sample_metrics_df):
    """Test FDR correction application."""
    # First compute correlations
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    results = compute_correlations(sample_metrics_df, metric_cols)
    
    # Apply FDR
    corrected_results = apply_fdr_correction(results)
    
    assert 'q' in corrected_results.columns
    assert 'significant' in corrected_results.columns
    assert all(corrected_results['q'] >= 0)
    assert all(corrected_results['q'] <= 1)
    
    logger.log("test_apply_fdr_correction", n_significant=corrected_results['significant'].sum())

def test_log_significant_correlations(sample_metrics_df):
    """Test logging of significant correlations."""
    # Create data with a known strong correlation
    np.random.seed(123)
    n = 50
    df = pd.DataFrame({
        'subject_id': [f'sub_{i}' for i in range(n)],
        'modularity': np.random.randn(n),
        'motor_score': np.random.randn(n),
        'fd': np.random.randn(n)
    })
    
    # Force a strong correlation
    df['motor_score'] = df['modularity'] * 2 + np.random.randn(n) * 0.1
    
    results = compute_correlations(df, ['modularity'])
    results = apply_fdr_correction(results)
    
    # This should log if r > threshold
    log_significant_correlations(results, threshold=CORRELATION_THRESHOLD)
    
    logger.log("test_log_significant_correlations")

def test_correlation_threshold_logging(sample_metrics_df):
    """Test that correlations above threshold are logged."""
    # Create data with a strong correlation
    np.random.seed(456)
    n = 50
    df = pd.DataFrame({
        'subject_id': [f'sub_{i}' for i in range(n)],
        'modularity': np.random.randn(n),
        'motor_score': np.random.randn(n),
        'fd': np.random.randn(n)
    })
    
    # Create a correlation > 0.3
    df['motor_score'] = df['modularity'] * 0.5 + np.random.randn(n) * 0.2
    
    results = compute_correlations(df, ['modularity'])
    results = apply_fdr_correction(results)
    
    # Check that the correlation exceeds threshold
    if not results.empty:
        r_value = results.iloc[0]['r']
        if abs(r_value) > CORRELATION_THRESHOLD:
            # Should have logged the threshold exceedance
            logger.log("test_correlation_threshold_logging", r=r_value, threshold=CORRELATION_THRESHOLD)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])