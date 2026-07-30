import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from analysis.evaluate_metrics import (
    compute_metrics,
    evaluate_dataset,
    save_metrics_to_json,
    load_projected_embeddings
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_metrics_classification():
    """Test AUC computation for binary classification."""
    labels = np.array([0, 1, 0, 1, 1, 0])
    preds = np.array([0.1, 0.9, 0.2, 0.8, 0.95, 0.15])
    
    metrics = compute_metrics(preds, labels, 'classification')
    
    assert 'auc' in metrics
    assert 0.5 <= metrics['auc'] <= 1.0  # AUC should be between 0.5 and 1.0 for reasonable predictions
    assert not np.isnan(metrics['auc'])

def test_compute_metrics_regression():
    """Test RMSE and MAE computation for regression."""
    labels = np.array([1.0, 2.0, 3.0, 4.0])
    preds = np.array([1.1, 2.1, 2.9, 4.2])
    
    metrics = compute_metrics(preds, labels, 'regression')
    
    assert 'rmse' in metrics
    assert 'mae' in metrics
    assert metrics['rmse'] > 0
    assert metrics['mae'] > 0
    assert not np.isnan(metrics['rmse'])

def test_evaluate_dataset_missing_predictions():
    """Test that evaluation fails gracefully if predictions are missing."""
    df = pd.DataFrame({
        'dataset_id': ['test'],
        'run_id': ['1'],
        'labels': [1],
        'task_type': ['classification']
        # Missing 'predictions' column
    })
    
    result = evaluate_dataset(df, 'test', 'classification')
    assert result is None

def test_save_metrics_to_json(temp_dir):
    """Test saving metrics to JSON file."""
    metrics = [
        {
            "dataset_id": "test_ds",
            "task_type": "classification",
            "num_samples": 10,
            "metrics": {"auc": 0.95}
        }
    ]
    
    output_path = temp_dir / "metrics_test.json"
    save_metrics_to_json(metrics, output_path, "run_123")
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['run_id'] == "run_123"
    assert len(data['metrics']) == 1
    assert data['metrics'][0]['dataset_id'] == "test_ds"

def test_load_projected_embeddings_missing_file(temp_dir):
    """Test that loading non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_projected_embeddings(temp_dir / "nonexistent.parquet")

def test_evaluate_dataset_insufficient_data():
    """Test evaluation with too few samples."""
    df = pd.DataFrame({
        'dataset_id': ['test'],
        'run_id': ['1'],
        'labels': [1],
        'predictions': [0.9],
        'task_type': ['classification']
    })
    
    result = evaluate_dataset(df, 'test', 'classification')
    assert result is None
