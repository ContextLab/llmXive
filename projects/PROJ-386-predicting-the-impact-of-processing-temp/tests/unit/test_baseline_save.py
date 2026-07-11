import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the function under test
from models.baseline import save_model_artifacts, train_baseline_model, stratified_split_by_study

@pytest.fixture
def sample_data():
    """Create a mock dataset with interaction features."""
    np.random.seed(42)
    n = 100
    data = {
        'source_study': ['StudyA'] * 50 + ['StudyB'] * 50,
        'Temperature': np.random.uniform(400, 600, n),
        'Mg_pct': np.random.uniform(0.5, 2.0, n),
        'Si_pct': np.random.uniform(0.1, 1.0, n),
        'Temperature_x_Mg': np.random.uniform(200, 1200, n), # Interaction term
        'Temperature_x_Si': np.random.uniform(40, 600, n),   # Interaction term
        'grain_size': np.random.uniform(10, 50, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for model and metrics output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, "model.joblib")
        metrics_path = os.path.join(tmpdir, "metrics.json")
        yield model_path, metrics_path

def test_save_model_artifacts_creates_files(sample_data, temp_dirs):
    """Verify that save_model_artifacts creates both the model file and the metrics JSON."""
    model_path, metrics_path = temp_dirs

    # Prepare dummy results (simulating output from train_baseline_model)
    # We need to train a quick model to get a real sklearn object
    feature_cols = ['Temperature', 'Mg_pct', 'Si_pct', 'Temperature_x_Mg', 'Temperature_x_Si']
    X = sample_data[feature_cols]
    y = sample_data['grain_size']
    
    from sklearn.linear_model import LinearRegression
    model = LinearRegression().fit(X, y)
    
    results = {
        'model': model,
        'feature_cols': feature_cols,
        'r2_train': 0.8,
        'r2_test': 0.75,
        'mae_test': 2.5,
        'coefficients': {col: float(c) for col, c in zip(feature_cols, model.coef_)},
        'intercept': float(model.intercept_)
    }

    # Execute the function
    save_model_artifacts(results, model_path, metrics_path)

    # Assertions
    assert os.path.exists(model_path), "Model artifact file was not created."
    assert os.path.exists(metrics_path), "Metrics JSON file was not created."

    # Verify JSON content
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    assert 'r2_test' in metrics
    assert metrics['r2_test'] == 0.75
    assert 'coefficients' in metrics
    assert 'intercept' in metrics

def test_save_model_artifacts_overwrites_existing(temp_dirs):
    """Verify that saving a model overwrites existing files without error."""
    model_path, metrics_path = temp_dirs
    
    # Create dummy files first
    Path(model_path).touch()
    Path(metrics_path).touch()
    
    # Prepare minimal results
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    results = {
        'model': model,
        'feature_cols': ['x1'],
        'r2_train': 0.1,
        'r2_test': 0.1,
        'mae_test': 1.0,
        'coefficients': {'x1': 1.0},
        'intercept': 0.0
    }

    # Should not raise an exception
    save_model_artifacts(results, model_path, metrics_path)
    
    assert os.path.getsize(model_path) > 0
    assert os.path.getsize(metrics_path) > 0