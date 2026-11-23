"""
Unit tests for the evaluation module (code/evaluate.py).
"""
import os
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure imports from code/ work
from evaluate import (
    setup_logging,
    load_features,
    load_model_selection,
    load_split_config,
    load_model,
    calculate_metrics,
    calculate_baseline_mae,
    calculate_permutation_pvalue,
    calculate_partial_correlation,
    evaluate_model,
    save_results,
    parse_args,
    main
)

def test_calculate_metrics():
    """Test metrics calculation."""
    y_true = np.array([1, 2, 3, 4, 5])
    y_pred = np.array([1.1, 1.9, 3.1, 3.9, 5.1])

    metrics = calculate_metrics(y_true, y_pred)

    assert "r2" in metrics
    assert "mae" in metrics
    assert metrics["mae"] < 0.2

def test_calculate_baseline_mae():
    """Test baseline MAE calculation using DummyRegressor."""
    y_train = np.array([1, 2, 3, 4, 5])
    y_test = np.array([1.5, 2.5, 3.5, 4.5, 5.5])

    baseline_mae = calculate_baseline_mae(y_train, y_test)

    assert isinstance(baseline_mae, float)
    assert baseline_mae >= 0

def test_calculate_permutation_pvalue():
    """Test permutation test p-value calculation."""
    y_true = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    y_pred = np.array([1.1, 2.2, 2.9, 4.1, 5.0, 6.1, 6.9, 8.2, 8.9, 10.1])
    features = np.random.rand(10, 3)

    p_value = calculate_permutation_pvalue(y_true, y_pred, features, n_permutations=10)

    assert isinstance(p_value, float)
    assert 0 <= p_value <= 1

def test_calculate_partial_correlation():
    """Test partial correlation calculation."""
    # Simple linear relationship
    X = np.array([1, 2, 3, 4, 5])
    Y = np.array([2, 4, 6, 8, 10])
    Controls = np.array([0.5, 1.0, 1.5, 2.0, 2.5])

    corr, p_val = calculate_partial_correlation(X, Y, Controls)

    assert isinstance(corr, float)
    assert isinstance(p_val, float)
    assert np.isclose(corr, 1.0, atol=0.1)  # Perfect correlation in this case
