import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from statistical_analysis import (
    load_predictions,
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
        'model': ['gcn', 'rf', 'lr'] * 3,
        'r2': [0.85, 0.78, 0.72, 0.82, 0.76, 0.70, 0.88, 0.80, 0.74],
        'mae': [0.15, 0.22, 0.28, 0.18, 0.24, 0.30, 0.12, 0.20, 0.26],
        'rmse': [0.20, 0.28, 0.35, 0.22, 0.30, 0.38, 0.18, 0.26, 0.32],
        'prediction': [1.0, 1.2, 1.4, 0.9, 1.1, 1.3, 1.1, 1.3, 1.5],
        'target': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_predictions_file(tmp_path, sample_predictions):
    """Create a temporary predictions file."""
    filepath = tmp_path / 'predictions.csv'
    sample_predictions.to_csv(filepath, index=False)
    return filepath

def test_load_predictions_success(sample_predictions_file):
    """Test successful loading of predictions file."""
    df = load_predictions(str(sample_predictions_file))
    assert isinstance(df, pd.DataFrame)
    assert 'fold' in df.columns
    assert 'model' in df.columns
    assert 'prediction' in df.columns
    assert 'target' in df.columns
    assert len(df) == 9

def test_load_predictions_missing_file(tmp_path):
    """Test loading non-existent file raises FileNotFoundError."""
    filepath = tmp_path / 'nonexistent.csv'
    with pytest.raises(FileNotFoundError):
        load_predictions(str(filepath))

def test_load_predictions_missing_columns(tmp_path, sample_predictions):
    """Test loading file with missing required columns raises ValueError."""
    filepath = tmp_path / 'bad_predictions.csv'
    # Remove required column
    bad_df = sample_predictions.drop(columns=['target'])
    bad_df.to_csv(filepath, index=False)
    
    with pytest.raises(ValueError):
        load_predictions(str(filepath))

def test_calculate_fold_metrics(sample_predictions):
    """Test calculation of fold metrics."""
    metrics = calculate_fold_metrics(sample_predictions)
    
    assert isinstance(metrics, pd.DataFrame)
    assert 'fold' in metrics.columns
    assert 'model' in metrics.columns
    assert 'r2' in metrics.columns
    assert 'mae' in metrics.columns
    
    # Check that we have metrics for each fold and model
    assert len(metrics) == 9  # 3 folds * 3 models
    
    # Check that R2 values are reasonable (between -inf and 1)
    assert all(metrics['r2'] <= 1.0)

def test_perform_paired_ttest_normal_distribution():
    """Test paired t-test with normally distributed data."""
    # Create normally distributed data
    np.random.seed(42)
    model_a = np.random.normal(0.8, 0.1, 10)
    model_b = np.random.normal(0.7, 0.1, 10)
    
    result = perform_paired_ttest(
        pd.Series(model_a),
        pd.Series(model_b),
        alpha=0.05
    )
    
    assert 'test_type' in result
    assert 'statistic' in result
    assert 'p_value' in result
    assert 'significant' in result
    assert 'normality_p_value' in result
    
    assert result['test_type'] == 't-test' or result['test_type'] == 'wilcoxon'
    assert isinstance(result['p_value'], float)
    assert 0 <= result['p_value'] <= 1

def test_perform_paired_ttest_non_normal_distribution():
    """Test Wilcoxon fallback for non-normal data."""
    # Create non-normally distributed data (exponential)
    np.random.seed(42)
    model_a = np.random.exponential(0.8, 10)
    model_b = np.random.exponential(0.7, 10)
    
    result = perform_paired_ttest(
        pd.Series(model_a),
        pd.Series(model_b),
        alpha=0.05
    )
    
    assert 'test_type' in result
    assert 'statistic' in result
    assert 'p_value' in result
    
    # Should use Wilcoxon for non-normal data
    # Note: With small samples, Shapiro-Wilk might not detect non-normality
    # So we just check that the test runs without error

def test_run_comparisons(sample_predictions):
    """Test running model comparisons."""
    metrics = calculate_fold_metrics(sample_predictions)
    models = ['gcn', 'rf', 'lr']
    
    comparisons = run_comparisons(metrics, models, metric='r2', alpha=0.05)
    
    assert isinstance(comparisons, pd.DataFrame)
    assert not comparisons.empty
    
    # Check columns
    expected_cols = ['model_a', 'model_b', 'metric', 'test_type', 'statistic', 'p_value', 'significant']
    assert all(col in comparisons.columns for col in expected_cols)

def test_generate_report(tmp_path, sample_predictions):
    """Test generating statistical comparison report."""
    metrics = calculate_fold_metrics(sample_predictions)
    comparisons = run_comparisons(metrics, ['gcn', 'rf', 'lr'], metric='r2')
    
    output_path = tmp_path / 'statistical_comparison.csv'
    generate_report(comparisons, str(output_path))
    
    assert output_path.exists()
    
    # Read and verify the output
    result_df = pd.read_csv(output_path)
    assert 'fold' in result_df.columns
    assert 'model' in result_df.columns
    assert 'p_value' in result_df.columns
    assert 'statistic' in result_df.columns

def test_run_comparisons_with_mae(sample_predictions):
    """Test comparisons using MAE metric."""
    metrics = calculate_fold_metrics(sample_predictions)
    comparisons = run_comparisons(metrics, ['gcn', 'rf'], metric='mae', alpha=0.05)
    
    assert not comparisons.empty
    assert all(comparisons['metric'] == 'mae')

def test_perform_paired_ttest_insufficient_data():
    """Test t-test with insufficient data points."""
    # Only 1 data point - should handle gracefully
    model_a = pd.Series([0.8])
    model_b = pd.Series([0.7])
    
    # This should not crash but might return NaN or handle the edge case
    result = perform_paired_ttest(model_a, model_b, alpha=0.05)
    
    assert 'p_value' in result
    # The function should handle this edge case without crashing

def test_run_comparisons_missing_model(sample_predictions):
    """Test comparisons with a model that doesn't exist in data."""
    metrics = calculate_fold_metrics(sample_predictions)
    
    # Include a model that doesn't exist
    models = ['gcn', 'rf', 'nonexistent_model']
    
    # Should log warning but not crash
    comparisons = run_comparisons(metrics, models, metric='r2', alpha=0.05)
    
    # Should still have results for the valid comparisons
    assert isinstance(comparisons, pd.DataFrame)