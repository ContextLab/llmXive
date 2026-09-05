"""
Unit tests for model training functions in train.py
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import tempfile
import pickle

# Ensure we can import from code/
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.train import train_model, run_cross_validation, prepare_data

def test_prepare_data():
    """Test data preparation function."""
    # Create mock features and target
    features = np.random.rand(100, 10)
    target = np.random.rand(100)
    
    X_train, X_test, y_train, y_test = prepare_data(features, target, test_size=0.2, random_state=42)
    
    # Check split sizes
    assert len(X_train) == 80
    assert len(X_test) == 20
    assert len(y_train) == 80
    assert len(y_test) == 20

def test_train_model_ridge():
    """Test Ridge regression training."""
    # Create mock data
    X = np.random.rand(100, 10)
    y = np.random.rand(100)
    
    model = train_model(X, y, model_type="ridge")
    
    # Check model type
    assert model is not None
    # Check that the model has been fitted (has coef_)
    assert hasattr(model, 'coef_')

def test_train_model_random_forest():
    """Test Random Forest training."""
    # Create mock data
    X = np.random.rand(100, 10)
    y = np.random.rand(100)
    
    model = train_model(X, y, model_type="rf")
    
    # Check model type
    assert model is not None
    # Check that the model has been fitted
    assert hasattr(model, 'estimators_')

def test_run_cross_validation():
    """Test cross-validation function."""
    # Create mock data
    X = np.random.rand(100, 10)
    y = np.random.rand(100)
    
    r2_scores, mae_scores = run_cross_validation(X, y, model_type="ridge", cv=3)
    
    # Check output
    assert len(r2_scores) == 3
    assert len(mae_scores) == 3
    assert all(isinstance(score, (int, float)) for score in r2_scores)
    assert all(isinstance(score, (int, float)) for score in mae_scores)

def test_train_model_fail_case():
    """Test model training with insufficient data."""
    # Create mock data with N < 30
    X = np.random.rand(20, 10)
    y = np.random.rand(20)
    
    model = train_model(X, y, model_type="ridge")
    
    # Should still return a model, but pipeline should handle failure later
    assert model is not None
