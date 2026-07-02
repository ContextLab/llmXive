"""
Unit tests for feature_selection.py
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.analysis.feature_selection import (
    run_lasso_selection,
    run_rf_selection,
    run_sensitivity_sweep,
    save_selection_frequency
)

@pytest.fixture
def synthetic_data():
    """Create synthetic data for testing."""
    np.random.seed(42)
    n_samples = 200
    n_features = 50

    # Create features with some correlation structure
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"feature_{i}" for i in range(n_features)]
    )

    # Create binary labels with signal from first 5 features
    y = pd.Series(
        np.where(X.iloc[:, :5].sum(axis=1) > 0, 1, 0),
        name="resistance"
    )

    return X, y

def test_lasso_selection_basic(synthetic_data):
    """Test LASSO selection returns a list of features."""
    X, y = synthetic_data
    selected = run_lasso_selection(X, y)

    assert isinstance(selected, list)
    assert len(selected) > 0
    assert all(isinstance(f, str) for f in selected)

def test_rf_selection_basic(synthetic_data):
    """Test Random Forest selection returns a list of features."""
    X, y = synthetic_data
    selected = run_rf_selection(X, y, threshold=0.05)

    assert isinstance(selected, list)
    assert len(selected) > 0
    assert all(isinstance(f, str) for f in selected)

def test_sensitivity_sweep_output_shape(synthetic_data):
    """Test sensitivity sweep returns correct DataFrame shape."""
    X, y = synthetic_data
    thresholds = [0.01, 0.05]
    iterations = 2

    df = run_sensitivity_sweep(X, y, thresholds=thresholds, iterations=iterations, method="lasso")

    expected_rows = len(X.columns) * len(thresholds)
    assert df.shape[0] == expected_rows
    assert list(df.columns) == ["feature_id", "threshold", "frequency"]

def test_sensitivity_sweep_frequency_range(synthetic_data):
    """Test that frequencies are between 0 and 1."""
    X, y = synthetic_data
    df = run_sensitivity_sweep(X, y, iterations=3, method="lasso")

    assert (df["frequency"] >= 0).all()
    assert (df["frequency"] <= 1).all()

def test_save_selection_frequency(tmp_path):
    """Test that save_selection_frequency writes a valid CSV."""
    df = pd.DataFrame({
        "feature_id": ["f1", "f2"],
        "threshold": [0.01, 0.01],
        "frequency": [0.5, 0.8]
    })

    output_path = tmp_path / "test_selection.csv"
    saved_path = save_selection_frequency(df, output_path)

    assert saved_path.exists()
    loaded_df = pd.read_csv(saved_path)
    assert loaded_df.shape == df.shape
    assert list(loaded_df.columns) == ["feature_id", "threshold", "frequency"]

def test_lasso_with_null_signal():
    """Test LASSO with no signal (random y) returns few/no features."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(100, 20), columns=[f"f{i}" for i in range(20)])
    y = pd.Series(np.random.randint(0, 2, 100))

    selected = run_lasso_selection(X, y)
    # With no signal, LASSO should select very few or no features
    assert len(selected) < 10

def test_rf_with_null_signal():
    """Test RF with no signal (random y) returns few/no features."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(100, 20), columns=[f"f{i}" for i in range(20)])
    y = pd.Series(np.random.randint(0, 2, 100))

    selected = run_rf_selection(X, y, threshold=0.05)
    # With no signal, RF importance should be low
    assert len(selected) < 10
