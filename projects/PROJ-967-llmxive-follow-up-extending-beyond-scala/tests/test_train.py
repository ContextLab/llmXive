"""
Unit tests for the training module (code/train.py).
"""
import os
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure imports from code/ work
from train import (
    setup_directories,
    load_features,
    load_model_selection,
    prepare_data,
    train_model,
    run_cross_validation,
    calculate_permutation_pvalue,
    evaluate_model,
    save_results,
    save_model,
    parse_args,
    main
)

def test_load_model_selection(tmp_path):
    """Test loading model selection configuration."""
    config = {"model_type": "ridge", "n_samples": 100}
    path = tmp_path / "model_selection.json"
    with open(path, "w") as f:
        json.dump(config, f)

    result = load_model_selection(path)
    assert result["model_type"] == "ridge"

def test_prepare_data():
    """Test data preparation for training."""
    features = pd.DataFrame({
        "variance": [1.0, 2.0, 3.0],
        "entropy": [0.5, 0.6, 0.7],
        "fidelity_loss": [0.1, 0.2, 0.3]
    })

    X, y = prepare_data(features)

    assert X.shape == (3, 2)
    assert y.shape == (3,)

def test_train_model_ridge():
    """Test Ridge Regression training."""
    X = np.array([[1, 0], [0, 1], [1, 1]])
    y = np.array([1, 2, 3])

    model = train_model(X, y, "ridge")

    assert model is not None
    assert model.coef_.shape == (2,)

def test_train_model_rf():
    """Test Random Forest training."""
    X = np.array([[1, 0], [0, 1], [1, 1], [0, 0], [1, 0.5]])
    y = np.array([1, 2, 3, 0, 1.5])

    model = train_model(X, y, "rf")

    assert model is not None
    assert model.n_estimators == 100

def test_run_cross_validation():
    """Test cross-validation execution."""
    X = np.array([[1, 0], [0, 1], [1, 1], [0, 0], [1, 0.5], [0.5, 0.5]])
    y = np.array([1, 2, 3, 0, 1.5, 1.0])

    metrics = run_cross_validation(X, y, "ridge", cv=3)

    assert "r2_mean" in metrics
    assert "mae_mean" in metrics
    assert isinstance(metrics["r2_mean"], float)

def test_evaluate_model():
    """Test model evaluation."""
    X = np.array([[1, 0], [0, 1], [1, 1]])
    y = np.array([1, 2, 3])

    model = train_model(X, y, "ridge")
    metrics = evaluate_model(model, X, y)

    assert "r2" in metrics
    assert "mae" in metrics
