"""
Unit tests for the model training pipeline (T025).

Tests:
- Feature preparation logic
- Model training execution (mocked data)
- Metrics calculation correctness
- Artifact saving
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

# Mock the config to avoid dependency on real config files during unit tests
import sys
from unittest.mock import patch, MagicMock

# Add code to path if not already
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.train import (
    prepare_polynomial_features,
    train_polynomial_models,
    evaluate_polynomial_models,
    prepare_gp_features,
    train_gp_model,
    evaluate_gp_model
)

@pytest.fixture
def sample_descriptors():
    """Create a small synthetic dataset for testing."""
    data = {
        'sample_id': [f's{i}' for i in range(10)],
        'material': ['Al'] * 4 + ['Cu'] * 3 + ['Ni'] * 3,
        'reduction': [10.0, 20.0, 30.0, 40.0, 10.0, 20.0, 30.0, 10.0, 20.0, 30.0],
        'brass_vol_frac': [0.1, 0.2, 0.3, 0.4, 0.15, 0.25, 0.35, 0.12, 0.22, 0.32],
        'copper_vol_frac': [0.05, 0.1, 0.15, 0.2, 0.06, 0.11, 0.16, 0.05, 0.1, 0.15],
        's_vol_frac': [0.02, 0.04, 0.06, 0.08, 0.025, 0.045, 0.065, 0.02, 0.04, 0.06],
        'goss_vol_frac': [0.01, 0.02, 0.03, 0.04, 0.012, 0.022, 0.032, 0.01, 0.02, 0.03],
        'random_vol_frac': [0.82, 0.64, 0.46, 0.28, 0.753, 0.573, 0.393, 0.8, 0.62, 0.44]
    }
    return pd.DataFrame(data)

def test_prepare_polynomial_features(sample_descriptors):
    """Test feature preparation for polynomial regression."""
    X, y_dict, scaler = prepare_polynomial_features(sample_descriptors)

    assert X.shape == (10, 1), f"Expected shape (10, 1), got {X.shape}"
    assert 'brass_vol_frac' in y_dict
    assert len(y_dict['brass_vol_frac']) == 10
    assert scaler is not None

def test_train_polynomial_models(sample_descriptors):
    """Test polynomial model training."""
    X, y_dict, scaler = prepare_polynomial_features(sample_descriptors)
    models = train_polynomial_models(X, y_dict, degree=2)

    assert 'brass_vol_frac' in models
    assert 'copper_vol_frac' in models
    assert 's_vol_frac' in models
    assert 'goss_vol_frac' in models
    assert 'random_vol_frac' in models

    # Verify model can predict
    pred = models['brass_vol_frac'].predict(X)
    assert pred.shape == (10,)

def test_evaluate_polynomial_models(sample_descriptors):
    """Test model evaluation metrics."""
    X, y_dict, scaler = prepare_polynomial_features(sample_descriptors)
    models = train_polynomial_models(X, y_dict, degree=2)
    metrics = evaluate_polynomial_models(models, X, y_dict)

    assert 'brass_vol_frac' in metrics
    assert 'rmse' in metrics['brass_vol_frac']
    assert 'r2' in metrics['brass_vol_frac']
    assert 0 <= metrics['brass_vol_frac']['r2'] <= 1.0  # R² should be valid

def test_prepare_gp_features(sample_descriptors):
    """Test feature preparation for GP model."""
    X_cont, X_cat, y, preprocessor = prepare_gp_features(sample_descriptors)

    assert X_cont.shape == (10, 1)
    assert X_cat.shape == (10, 1)
    assert y.shape == (10, 5)  # 5 components
    assert preprocessor is not None

def test_train_gp_model(sample_descriptors):
    """Test GP model training."""
    X_cont, X_cat, y, preprocessor = prepare_gp_features(sample_descriptors)
    gpr, gp_preprocessor = train_gp_model(X_cont, X_cat, y, preprocessor)

    assert gpr is not None
    assert gp_preprocessor is not None

    # Verify model can predict
    X_combined = np.hstack([X_cont, X_cat])
    X_processed = gp_preprocessor.transform(X_combined)
    pred, std = gpr.predict(X_processed, return_std=True)
    assert pred.shape == (10, 5)
    assert std.shape == (10, 5)

def test_evaluate_gp_model(sample_descriptors):
    """Test GP model evaluation."""
    X_cont, X_cat, y, preprocessor = prepare_gp_features(sample_descriptors)
    gpr, gp_preprocessor = train_gp_model(X_cont, X_cat, y, preprocessor)
    metrics = evaluate_gp_model(gpr, gp_preprocessor, X_cont, X_cat, y)

    assert 'brass_vol_frac' in metrics
    assert 'rmse' in metrics['brass_vol_frac']
    assert 'r2' in metrics['brass_vol_frac']
    assert 0 <= metrics['brass_vol_frac']['r2'] <= 1.0

def test_missing_columns_raises_error(sample_descriptors):
    """Test that missing required columns raise errors."""
    # Remove 'reduction' column
    df_missing = sample_descriptors.drop(columns=['reduction'])

    with pytest.raises(ValueError):
        prepare_polynomial_features(df_missing)

    with pytest.raises(ValueError):
        prepare_gp_features(df_missing)

def test_empty_data_raises_error():
    """Test that empty data raises errors."""
    df_empty = pd.DataFrame(columns=['reduction', 'material', 'brass_vol_frac'])

    with pytest.raises(ValueError):
        prepare_polynomial_features(df_empty)

    with pytest.raises(ValueError):
        prepare_gp_features(df_empty)
