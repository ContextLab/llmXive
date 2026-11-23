"""
Unit tests for model training.
"""
import os
import sys
import tempfile
import numpy as np
import pandas as pd
import pytest
from src.models.train import train_ridge, train_lasso, train_xgboost, prepare_data

@pytest.fixture
def sample_data():
    np.random.seed(42)
    X = np.random.rand(100, 5)
    y = np.random.rand(100)
    return X, y

@pytest.fixture
def temp_processed_data():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_prepare_data(sample_data):
    """Test data preparation."""
    X, y = sample_data
    X_prep, y_prep, cols = prepare_data(pd.DataFrame(X, columns=["f1", "f2", "f3", "f4", "f5"]), target_column="target")
    assert X_prep.shape[0] == y_prep.shape[0]

def test_train_ridge(sample_data):
    """Test Ridge regression training."""
    X, y = sample_data
    model = train_ridge(X, y)
    assert model is not None
    predictions = model.predict(X)
    assert predictions.shape == y.shape

def test_train_lasso(sample_data):
    """Test Lasso regression training."""
    X, y = sample_data
    model = train_lasso(X, y)
    assert model is not None
    predictions = model.predict(X)
    assert predictions.shape == y.shape

def test_train_xgboost(sample_data):
    """Test XGBoost training."""
    X, y = sample_data
    model = train_xgboost(X, y)
    assert model is not None
    predictions = model.predict(X)
    assert predictions.shape == y.shape
