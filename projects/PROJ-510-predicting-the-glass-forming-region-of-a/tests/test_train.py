"""
Unit and integration tests for model training.
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score
from code.train import load_data, train_model


def test_train_model_returns_object():
    """Test that train_model returns a fitted model object."""
    # Create a minimal mock dataset
    data = {
        "mixing_enthalpy": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "atomic_size_mismatch": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
        "electronegativity_variance": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08],
        "critical_cooling_rate": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
    }
    df = pd.DataFrame(data)

    model, metrics = train_model(df)
    assert model is not None
    assert metrics is not None
    assert "mean_rmse" in metrics


def test_cross_validation_splits():
    """Test that cross-validation produces valid splits."""
    # This is implicitly tested by train_model using 5-fold CV
    # We verify the output structure contains fold scores
    data = {
        "mixing_enthalpy": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "atomic_size_mismatch": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
        "electronegativity_variance": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08],
        "critical_cooling_rate": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
    }
    df = pd.DataFrame(data)

    model, metrics = train_model(df)
    assert "fold_scores" in metrics
    assert len(metrics["fold_scores"]) == 5
