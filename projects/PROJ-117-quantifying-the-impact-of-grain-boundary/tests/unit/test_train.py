"""
Unit tests for code/train.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest
import xgboost as xgb

# Mock imports for testing
from train import (
    load_and_prepare_data,
    split_data,
    tune_hyperparameters,
    evaluate_model,
    save_model_and_metrics,
    FEATURE_COLS,
    TARGET_COL,
    MIN_RECORDS
)

@pytest.fixture
def sample_data():
    """Create sample cleaned dataset for testing."""
    data = {
        "misorientation_angle": np.random.rand(100) * 90,
        "sigma_value": np.random.randint(3, 50, 100),
        "boundary_plane_normal_h": np.random.rand(100),
        "boundary_plane_normal_k": np.random.rand(100),
        "boundary_plane_normal_l": np.random.rand(100),
        "boundary_width": np.random.rand(100) * 10,
        "excess_volume": np.random.rand(100) * 5,
        "temperature": np.random.rand(100) * 1000 + 300,
        "simulation_method_dft": np.random.randint(0, 2, 100),
        "simulation_method_md": np.random.randint(0, 2, 100),
        "simulation_method_kmc": np.random.randint(0, 2, 100),
        "potential_id_encoded": np.random.randint(0, 10, 100),
        "diffusivity": np.random.rand(100) * 1e-10
    }
    return pd.DataFrame(data)

def test_load_and_prepare_data_missing_file(sample_data, tmp_path, monkeypatch):
    """Test error handling when data file is missing."""
    # Create a temporary directory and set DATA_PATH
    monkeypatch.setattr("train.DATA_PATH", Path(tmp_path) / "nonexistent.parquet")
    
    with pytest.raises(SystemExit):
        load_and_prepare_data()

def test_load_and_prepare_data_insufficient_records(sample_data, tmp_path, monkeypatch):
    """Test error handling for insufficient records."""
    # Create a small dataset
    small_df = sample_data.head(10)
    data_path = Path(tmp_path) / "cleaned_dataset.parquet"
    small_df.to_parquet(data_path)
    
    monkeypatch.setattr("train.DATA_PATH", data_path)
    
    with pytest.raises(SystemExit):
        load_and_prepare_data()

def test_split_data_shapes(sample_data):
    """Test data splitting proportions."""
    X = sample_data[FEATURE_COLS]
    y = sample_data[TARGET_COL]
    
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
    
    total = len(X)
    assert len(X_train) == int(total * 0.70)
    assert len(X_val) == int(total * 0.15)
    assert len(X_test) == int(total * 0.15)

def test_tune_hyperparameters(sample_data):
    """Test hyperparameter tuning returns a model."""
    X_train = sample_data[FEATURE_COLS].head(50)
    y_train = sample_data[TARGET_COL].head(50)
    X_val = sample_data[FEATURE_COLS].tail(50)
    y_val = sample_data[TARGET_COL].tail(50)
    
    model = tune_hyperparameters(X_train, y_train, X_val, y_val)
    
    assert isinstance(model, xgb.XGBRegressor)
    assert hasattr(model, 'get_params')

def test_evaluate_model(sample_data):
    """Test model evaluation returns correct metrics."""
    X_test = sample_data[FEATURE_COLS].tail(20)
    y_test = sample_data[TARGET_COL].tail(20)
    
    # Create a dummy model
    model = xgb.XGBRegressor(n_estimators=10, max_depth=3, random_state=42)
    model.fit(sample_data[FEATURE_COLS].head(80), sample_data[TARGET_COL].head(80))
    
    metrics = evaluate_model(model, X_test, y_test)
    
    assert "r2" in metrics
    assert "rmse" in metrics
    assert "mape" in metrics
    assert isinstance(metrics["r2"], float)
    assert metrics["r2"] <= 1.0  # R2 cannot exceed 1

def test_save_model_and_metrics(sample_data, tmp_path, monkeypatch):
    """Test model and metrics saving."""
    model = xgb.XGBRegressor(n_estimators=10, max_depth=3)
    model.fit(sample_data[FEATURE_COLS].head(50), sample_data[TARGET_COL].head(50))
    
    metrics = {"r2": 0.85, "rmse": 0.1, "mape": 5.2}
    
    model_path = Path(tmp_path) / "test_model.json"
    metrics_path = Path(tmp_path) / "test_metrics.json"
    
    monkeypatch.setattr("train.MODEL_PATH", model_path)
    monkeypatch.setattr("train.METRICS_PATH", metrics_path)
    
    save_model_and_metrics(model, metrics)
    
    assert model_path.exists()
    assert metrics_path.exists()
    
    with open(metrics_path) as f:
        saved_metrics = json.load(f)
    
    assert saved_metrics == metrics
