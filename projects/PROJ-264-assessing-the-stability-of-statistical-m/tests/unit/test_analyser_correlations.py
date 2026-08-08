import pandas as pd
import numpy as np
from code.analyser import calculate_correlations, aggregate_metrics, aggregate_log_variance

def test_calculate_correlations_cv():
    """Test correlation calculation for CV metric."""
    # Create mock data
    metrics_df = pd.DataFrame({
        'dataset_id': [1, 2, 3, 4, 5],
        'model_name': ['LR', 'LR', 'LR', 'LR', 'LR'],
        'cv_accuracy': [0.1, 0.05, 0.02, 0.01, 0.005]
    })
    
    props_df = pd.DataFrame({
        'dataset_id': [1, 2, 3, 4, 5],
        'n_samples': [1000, 2000, 5000, 10000, 20000],
        'n_features': [10, 10, 10, 10, 10]
    })
    
    result = calculate_correlations(metrics_df, props_df, 'CV')
    
    assert not result.empty
    assert 'pearson_r' in result.columns
    assert 'pearson_p_value' in result.columns
    assert 'spearman_rho' in result.columns
    # Check that correlation is negative (as N increases, CV should decrease)
    assert result['pearson_r'].iloc[0] < 0

def test_calculate_correlations_log_variance():
    """Test correlation calculation for LogVariance metric."""
    metrics_df = pd.DataFrame({
        'dataset_id': [1, 2, 3, 4, 5],
        'model_name': ['RF', 'RF', 'RF', 'RF', 'RF'],
        'log_variance_accuracy': [-2.0, -3.0, -4.0, -5.0, -6.0]
    })
    
    props_df = pd.DataFrame({
        'dataset_id': [1, 2, 3, 4, 5],
        'n_samples': [1000, 2000, 5000, 10000, 20000],
        'n_features': [10, 10, 10, 10, 10]
    })
    
    result = calculate_correlations(metrics_df, props_df, 'LogVariance')
    
    assert not result.empty
    assert 'pearson_r' in result.columns
    # Correlation should be negative
    assert result['pearson_r'].iloc[0] < 0

def test_calculate_correlations_insufficient_data():
    """Test handling of insufficient data points."""
    metrics_df = pd.DataFrame({
        'dataset_id': [1],
        'model_name': ['LR'],
        'cv_accuracy': [0.1]
    })
    
    props_df = pd.DataFrame({
        'dataset_id': [1],
        'n_samples': [1000],
        'n_features': [10]
    })
    
    result = calculate_correlations(metrics_df, props_df, 'CV')
    assert result.empty

def test_calculate_correlations_with_nan():
    """Test handling of NaN values."""
    metrics_df = pd.DataFrame({
        'dataset_id': [1, 2, 3],
        'model_name': ['LR', 'LR', 'LR'],
        'cv_accuracy': [0.1, np.nan, 0.05]
    })
    
    props_df = pd.DataFrame({
        'dataset_id': [1, 2, 3],
        'n_samples': [1000, 2000, 5000],
        'n_features': [10, 10, 10]
    })
    
    result = calculate_correlations(metrics_df, props_df, 'CV')
    # Should not crash, should use valid points
    assert not result.empty