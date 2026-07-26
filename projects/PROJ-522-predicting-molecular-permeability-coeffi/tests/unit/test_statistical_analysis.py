"""
Unit tests for statistical analysis functions.
"""
import os
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from statistical_analysis import (
    calculate_fold_metrics,
    perform_paired_ttest,
    run_comparisons,
    generate_report
)

@pytest.fixture
def sample_predictions():
    """Create sample predictions data for testing."""
    data = {
        'fold': [0, 0, 0, 1, 1, 1, 2, 2, 2],
        'model': ['gcn', 'gcn', 'gcn', 'gcn', 'gcn', 'gcn', 'gcn', 'gcn', 'gcn',
                 'rf', 'rf', 'rf', 'rf', 'rf', 'rf', 'rf', 'rf', 'rf'],
        'true_value': [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0,
                      1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0],
        'predicted_value': [1.1, 2.1, 2.9, 1.2, 1.9, 3.1, 1.05, 2.05, 2.95,
                           1.5, 2.5, 2.5, 1.5, 2.5, 2.5, 1.5, 2.5, 2.5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_metrics_df():
    """Create sample metrics dataframe for testing."""
    data = {
        'fold': [0, 0, 1, 1, 2, 2],
        'model': ['gcn', 'rf', 'gcn', 'rf', 'gcn', 'rf'],
        'r2': [0.95, 0.85, 0.92, 0.80, 0.94, 0.82],
        'mae': [0.1, 0.2, 0.12, 0.25, 0.11, 0.22],
        'rmse': [0.15, 0.25, 0.18, 0.30, 0.16, 0.28]
    }
    return pd.DataFrame(data)

def test_calculate_fold_metrics(sample_predictions):
    """Test calculation of metrics per fold."""
    metrics_df = calculate_fold_metrics(sample_predictions)
    
    assert 'fold' in metrics_df.columns
    assert 'model' in metrics_df.columns
    assert 'r2' in metrics_df.columns
    assert 'mae' in metrics_df.columns
    assert 'rmse' in metrics_df.columns
    
    # Check that we have entries for both models across folds
    unique_folds = metrics_df['fold'].unique()
    unique_models = metrics_df['model'].unique()
    
    assert len(unique_folds) == 3  # folds 0, 1, 2
    assert len(unique_models) == 2  # gcn and rf

def test_perform_paired_ttest(sample_metrics_df):
    """Test paired t-test implementation."""
    result = perform_paired_ttest(
        sample_metrics_df, 
        'gcn', 
        'rf', 
        metric='r2', 
        alpha=0.05
    )
    
    assert 't_statistic' in result
    assert 'p_value' in result
    assert 'is_significant' in result
    assert 'mean_a' in result
    assert 'mean_b' in result
    
    # GNN should have higher mean R2 in this synthetic data
    assert result['mean_a'] > result['mean_b']
    
    # Check that normality test results are included
    assert 'shapiro_statistic' in result
    assert 'shapiro_p_value' in result

def test_paired_ttest_insufficient_data(sample_metrics_df):
    """Test that t-test fails gracefully with insufficient data."""
    # Create a dataframe with only 1 fold
    small_df = sample_metrics_df[sample_metrics_df['fold'] == 0]
    
    with pytest.raises(ValueError, match="Need at least 2 folds"):
        perform_paired_ttest(small_df, 'gcn', 'rf', metric='r2')

def test_run_comparisons(sample_metrics_df):
    """Test running all comparisons."""
    comparisons_df = run_comparisons(sample_metrics_df)
    
    assert isinstance(comparisons_df, pd.DataFrame)
    assert 'model_a' in comparisons_df.columns
    assert 'model_b' in comparisons_df.columns
    assert 'metric' in comparisons_df.columns
    assert 'p_value' in comparisons_df.columns
    
    # Should have comparisons for r2, mae, rmse
    assert len(comparisons_df) == 3  # 3 metrics

def test_generate_report(sample_metrics_df):
    """Test report generation."""
    comparisons_df = run_comparisons(sample_metrics_df)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        temp_path = f.name
    
    try:
        generate_report(comparisons_df, temp_path)
        
        # Check file exists and has content
        assert os.path.exists(temp_path)
        with open(temp_path, 'r') as f:
            content = f.read()
        
        assert "Statistical Comparison Report" in content
        assert "gcn" in content
        assert "rf" in content
        assert "p-value" in content
        assert "FR-003" in content or "Paired t-test" in content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_paired_ttest_unequal_folds(sample_metrics_df):
    """Test error handling for unequal fold counts."""
    # Create a scenario where models have different fold counts
    unequal_df = sample_metrics_df[~((sample_metrics_df['model'] == 'rf') & (sample_metrics_df['fold'] == 2))]
    
    with pytest.raises(ValueError, match="Unequal number of folds"):
        perform_paired_ttest(unequal_df, 'gcn', 'rf', metric='r2')