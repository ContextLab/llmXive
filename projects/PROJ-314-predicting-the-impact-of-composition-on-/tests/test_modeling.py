import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import StratifiedKFold, train_test_split
import json
import os
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from modeling import prepare_splits, train_models, evaluate_models

@pytest.fixture
def sample_data():
    """Create a synthetic but realistic sample dataset for testing logic."""
    np.random.seed(42)
    n = 100
    # Create features
    X = pd.DataFrame({
        "mean_atomic_radius": np.random.normal(1.5, 0.2, n),
        "electronegativity_std": np.random.normal(0.5, 0.1, n),
        "valence_electron_concentration": np.random.normal(2.0, 0.3, n),
        "cation_size_variance": np.random.normal(0.1, 0.02, n),
        "sintering_temp": np.random.normal(1200, 100, n)
    })
    # Create target
    y = pd.Series(np.random.normal(10, 2, n))
    # Create stratification column with 3 classes
    groups = np.random.choice(["Group A", "Group B", "Group C"], n)
    X["primary_anion_cation_group"] = groups
    return X, y, "primary_anion_cation_group"

def test_prepare_splits_stratified(sample_data):
    """Test that prepare_splits performs stratified split correctly."""
    X, y, strat_col = sample_data
    X_train, X_test, y_train, y_test, strat_train, strat_test = prepare_splits(X, y, strat_col)
    
    # Check sizes
    assert len(X_train) + len(X_test) == len(X)
    assert len(y_train) + len(y_test) == len(y)
    
    # Check that classes are preserved in both splits (approximate due to randomness)
    train_dist = strat_train.value_counts(normalize=True)
    test_dist = strat_test.value_counts(normalize=True)
    
    # Distribution should be roughly similar
    for group in strat_train.unique():
        if group in strat_test.unique():
            assert abs(train_dist.get(group, 0) - test_dist.get(group, 0)) < 0.15

def test_prepare_splits_holdout_if_few_classes(sample_data):
    """Test that prepare_splits falls back to hold-out if classes < 5 (simulated)."""
    X, y, strat_col = sample_data
    # Force a scenario with few samples per class (simulating the logic in T026)
    # We can't easily force the internal logic without mocking, but we can test the function's robustness
    # The actual logic in T026 checks class counts. Here we verify the function doesn't crash.
    X_small = X.head(10)
    y_small = y.head(10)
    strat_small = X_small[strat_col]
    
    # This should not raise an error even with small data
    try:
        X_tr, X_te, y_tr, y_te, st_tr, st_te = prepare_splits(X_small, y_small, strat_col)
        assert len(X_tr) > 0 and len(X_te) > 0
    except Exception as e:
        # If it fails, it should be due to stratification constraints, not code errors
        # But our implementation should handle it gracefully
        pytest.fail(f"prepare_splits failed on small data: {e}")

def test_train_models_output(sample_data):
    """Test that train_models returns a dictionary of trained models."""
    X, y, strat_col = sample_data
    models = train_models(X, y)
    
    assert isinstance(models, dict)
    assert "RandomForest" in models
    assert "GradientBoosting" in models
    
    # Check types
    assert isinstance(models["RandomForest"], RandomForestRegressor)
    assert isinstance(models["GradientBoosting"], GradientBoostingRegressor)

def test_evaluate_models_metrics(sample_data):
    """Test that evaluate_models returns correct structure."""
    X, y, strat_col = sample_data
    models = train_models(X, y)
    
    metrics, results_df = evaluate_models(X, y, strat_col, models)
    
    assert isinstance(metrics, dict)
    assert "RandomForest" in metrics
    assert "GradientBoosting" in metrics
    
    # Check metric keys
    for model_name, model_metrics in metrics.items():
        assert "mae" in model_metrics
        assert "r2" in model_metrics
        assert isinstance(model_metrics["mae"], float)
        assert isinstance(model_metrics["r2"], float)
    
    # Check results_df
    assert isinstance(results_df, pd.DataFrame)
    assert "model" in results_df.columns
    assert "actual" in results_df.columns
    assert "predicted" in results_df.columns
    assert len(results_df) == 2 * len(X) // 5 # 2 models * 20% test size approx