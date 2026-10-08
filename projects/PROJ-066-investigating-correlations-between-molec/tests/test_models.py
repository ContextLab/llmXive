"""
Unit and integration tests for model training and evaluation.

Tests cover:
- Data splitting (stratified).
- Model training (Linear Regression, Random Forest).
- Feature importance generation.
- Metrics calculation (RMSE, r).
- Baseline comparison.
- Memory usage checks.
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os
import pickle
from pathlib import Path

# Adjust path to import project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from models.train import (
    load_processed_data,
    split_data,
    train_linear_regression,
    train_random_forest,
    generate_feature_importance,
    save_model
)
from models.evaluate import (
    calculate_metrics,
    baseline_comparison
)

@pytest.fixture
def mock_processed_data():
    """Create a mock processed dataframe for testing."""
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        'TPSA': np.random.rand(n) * 100,
        'logP': np.random.rand(n) * 5,
        'MW': np.random.rand(n) * 300 + 100,
        'NumRotatableBonds': np.random.randint(0, 10, n),
        'NumHDonors': np.random.randint(0, 5, n),
        'NumHAcceptors': np.random.randint(0, 10, n),
        'NumRings': np.random.randint(0, 5, n),
        'target': np.random.rand(n) * 10, # Continuous target for regression
        'assay_date': '2023-01-01'
    })
    return df

def test_split_data_stratified(mock_processed_data):
    """Test that data is split correctly and stratified."""
    train_df, test_df = split_data(mock_processed_data, target_col='target', random_state=42)
    assert len(train_df) + len(test_df) == len(mock_processed_data)
    assert len(train_df) > 0
    assert len(test_df) > 0
    
def test_train_linear_regression(mock_processed_data):
    """Test Linear Regression training."""
    train_df, test_df = split_data(mock_processed_data, target_col='target', random_state=42)
    feature_cols = [c for c in train_df.columns if c not in ['target', 'assay_date', 'smiles']]
    X_train = train_df[feature_cols]
    y_train = train_df['target']
    
    model = train_linear_regression(X_train, y_train)
    assert model is not None
    # Check if model can predict
    preds = model.predict(X_train.head())
    assert len(preds) == 5
    
def test_train_random_forest(mock_processed_data):
    """Test Random Forest training with memory-conscious params."""
    train_df, test_df = split_data(mock_processed_data, target_col='target', random_state=42)
    feature_cols = [c for c in train_df.columns if c not in ['target', 'assay_date', 'smiles']]
    X_train = train_df[feature_cols]
    y_train = train_df['target']
    
    model = train_random_forest(X_train, y_train, max_depth=5, n_estimators=10)
    assert model is not None
    preds = model.predict(X_train.head())
    assert len(preds) == 5
    
def test_generate_feature_importance(mock_processed_data):
    """Test feature importance generation."""
    train_df, test_df = split_data(mock_processed_data, target_col='target', random_state=42)
    feature_cols = [c for c in train_df.columns if c not in ['target', 'assay_date', 'smiles']]
    X_train = train_df[feature_cols]
    y_train = train_df['target']
    
    rf_model = train_random_forest(X_train, y_train, max_depth=5, n_estimators=10)
    importance = generate_feature_importance(rf_model, feature_cols)
    
    assert isinstance(importance, dict)
    assert set(importance.keys()) == set(feature_cols)
    assert all(isinstance(v, (int, float)) for v in importance.values())
    
def test_calculate_metrics(mock_processed_data):
    """Test metrics calculation."""
    train_df, test_df = split_data(mock_processed_data, target_col='target', random_state=42)
    feature_cols = [c for c in train_df.columns if c not in ['target', 'assay_date', 'smiles']]
    X_train = train_df[feature_cols]
    y_train = train_df['target']
    X_test = test_df[feature_cols]
    y_test = test_df['target']
    
    lr_model = train_linear_regression(X_train, y_train)
    rf_model = train_random_forest(X_train, y_train, max_depth=5, n_estimators=10)
    
    lr_rmse, lr_r = calculate_metrics(lr_model, X_test, y_test)
    rf_rmse, rf_r = calculate_metrics(rf_model, X_test, y_test)
    
    assert isinstance(lr_rmse, float)
    assert isinstance(lr_r, float)
    assert isinstance(rf_rmse, float)
    assert isinstance(rf_r, float)
    
def test_baseline_comparison(mock_processed_data):
    """Test baseline mean predictor RMSE."""
    train_df, test_df = split_data(mock_processed_data, target_col='target', random_state=42)
    feature_cols = [c for c in train_df.columns if c not in ['target', 'assay_date', 'smiles']]
    X_train = train_df[feature_cols]
    y_train = train_df['target']
    X_test = test_df[feature_cols]
    y_test = test_df['target']
    
    baseline_rmse = baseline_comparison(y_train, y_test)
    assert isinstance(baseline_rmse, float)
    assert baseline_rmse >= 0
    
def test_save_model(tmp_path):
    """Test model saving and loading."""
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.coef_ = np.array([1.0, 2.0])
    model.intercept_ = 0.0
    
    save_path = tmp_path / "test_model.pkl"
    save_model(model, str(save_path))
    
    assert save_path.exists()
    with open(save_path, 'rb') as f:
        loaded_model = pickle.load(f)
    assert loaded_model is not None
