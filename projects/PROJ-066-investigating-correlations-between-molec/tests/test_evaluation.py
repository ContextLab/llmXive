"""
Integration tests for the evaluation pipeline.

Tests the full flow of:
- Loading processed data.
- Training models.
- Evaluating metrics.
- Generating visualizations (mocked for unit test).
- Saving metrics summary.
"""
import pytest
import pandas as pd
import numpy as np
import json
import sys
import os
from pathlib import Path
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from models.train import split_data, train_linear_regression, train_random_forest
from models.evaluate import calculate_metrics, baseline_comparison, save_metrics_summary

@pytest.fixture
def mock_data():
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'TPSA': np.random.rand(n) * 100,
        'logP': np.random.rand(n) * 5,
        'MW': np.random.rand(n) * 300 + 100,
        'target': np.random.rand(n) * 10
    })
    return df

def test_full_evaluation_pipeline(mock_data):
    """Test the end-to-end evaluation logic without file I/O."""
    train_df, test_df = split_data(mock_data, target_col='target', random_state=42)
    feature_cols = [c for c in train_df.columns if c not in ['target']]
    X_train, y_train = train_df[feature_cols], train_df['target']
    X_test, y_test = test_df[feature_cols], test_df['target']
    
    # Train
    lr = train_linear_regression(X_train, y_train)
    rf = train_random_forest(X_train, y_train, max_depth=3, n_estimators=5)
    
    # Evaluate
    lr_rmse, lr_r = calculate_metrics(lr, X_test, y_test)
    rf_rmse, rf_r = calculate_metrics(rf, X_test, y_test)
    baseline_rmse = baseline_comparison(y_train, y_test)
    
    assert lr_rmse > 0
    assert rf_rmse > 0
    assert baseline_rmse > 0
    
    # Check relative performance (RF should generally be better or comparable on synthetic data)
    # Just ensuring no crashes and valid numbers
    assert -1 <= lr_r <= 1
    assert -1 <= rf_r <= 1
    
def test_save_metrics_summary(tmp_path):
    """Test saving metrics summary to JSON."""
    metrics = {
        'baseline_rmse': 1.5,
        'model_lr_rmse': 1.2,
        'model_rf_rmse': 1.1,
        'model_lr_r': 0.8,
        'model_rf_r': 0.85,
        'pipeline_time_seconds': 10.5,
        'peak_memory_mb': 500,
        'plot_scatter_path': 'data/processed/plot_scatter.png',
        'plot_importance_path': 'data/processed/plot_importance.png'
    }
    
    output_path = tmp_path / "metrics_summary.json"
    save_metrics_summary(metrics, str(output_path))
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == metrics
