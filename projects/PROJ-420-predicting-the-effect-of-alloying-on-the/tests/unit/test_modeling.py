import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Import the functions to test
# We need to ensure the path is correct relative to the test runner
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling import (
    load_features_and_target,
    train_random_forest_with_cv,
    evaluate_model_on_test,
    save_model,
    save_model_metrics,
    run_modeling_pipeline
)
from schemas.alloy_record import ModelMetrics

@pytest.fixture
def mock_config(tmp_path):
    """Create a mock config with temporary directories."""
    with patch('modeling.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_config.data_processed = tmp_path / "data" / "processed"
        mock_config.data_processed.mkdir(parents=True, exist_ok=True)
        mock_config.models_dir = tmp_path / "models"
        mock_config.models_dir.mkdir(parents=True, exist_ok=True)
        mock_config.docs_outputs = tmp_path / "docs" / "outputs"
        mock_config.docs_outputs.mkdir(parents=True, exist_ok=True)
        mock_config.random_seed = 42
        mock_get_config.return_value = mock_config
        yield mock_config

@pytest.fixture
def sample_data(mock_config):
    """Create a sample filtered_alloys.csv for testing."""
    data_path = mock_config.data_processed / "filtered_alloys.csv"
    # Create dummy data with ILR columns and target
    n_samples = 100
    data = {
        'material_id': [f'mat_{i}' for i in range(n_samples)],
        'ilr_0': np.random.rand(n_samples),
        'ilr_1': np.random.rand(n_samples),
        'ilr_2': np.random.rand(n_samples),
        'poissons_ratio': np.random.rand(n_samples)
    }
    df = pd.DataFrame(data)
    df.to_csv(data_path, index=False)
    return data_path

def test_load_features_and_target(sample_data, mock_config):
    X, y = load_features_and_target()
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert len(X) == 100
    assert 'poissons_ratio' not in X.columns
    assert 'poissons_ratio' in y.name or y.name is not None # Check target

def test_train_random_forest_with_cv(sample_data, mock_config):
    X, y = load_features_and_target()
    model = train_random_forest_with_cv(X, y, cv_folds=3)
    assert model is not None
    assert hasattr(model, 'predict')

def test_evaluate_model_on_test(sample_data, mock_config):
    X, y = load_features_and_target()
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = train_random_forest_with_cv(X_train, y_train, cv_folds=3)
    mae = evaluate_model_on_test(model, X_test, y_test)
    assert isinstance(mae, float)
    assert mae >= 0

def test_save_model(sample_data, mock_config):
    X, y = load_features_and_target()
    model = train_random_forest_with_cv(X, y, cv_folds=3)
    
    output_path = mock_config.models_dir / "test_rf_model.pkl"
    saved_path = save_model(model, output_path)
    
    assert saved_path.exists()
    assert saved_path.suffix == '.pkl'

def test_save_model_metrics(mock_config):
    metrics_dict = {
        "model_type": "RandomForestRegressor",
        "cv_folds": 5,
        "cv_mae_mean": 0.05,
        "cv_mae_std": 0.01,
        "test_mae": 0.06,
        "n_train_samples": 80,
        "n_test_samples": 20,
        "random_seed": 42,
        "timestamp": "2023-01-01T00:00:00Z"
    }
    
    output_path = mock_config.docs_outputs / "test_metrics.json"
    saved_path = save_model_metrics(metrics_dict, output_path)
    
    assert saved_path.exists()
    
    with open(saved_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded['model_type'] == "RandomForestRegressor"
    assert loaded['test_mae'] == 0.06

def test_run_modeling_pipeline(sample_data, mock_config):
    """Test the full pipeline end-to-end."""
    result = run_modeling_pipeline()
    
    assert isinstance(result, dict)
    assert 'test_mae' in result
    assert 'cv_mae_mean' in result
    assert 'model_type' in result
    
    # Verify files were created
    assert (mock_config.models_dir / "rf_model.pkl").exists()
    assert (mock_config.docs_outputs / "model_metrics.json").exists()
    
    # Verify JSON content
    with open(mock_config.docs_outputs / "model_metrics.json", 'r') as f:
        metrics = json.load(f)
    assert metrics['test_mae'] > 0
    assert metrics['n_train_samples'] > 0
    assert metrics['n_test_samples'] > 0
