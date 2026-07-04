import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

from code.utils.metrics import paired_t_test, bonferroni_correct


def _create_dummy_model_and_data():
    """
    Helper to create a deterministic Random Forest model and a small
    synthetic dataset for LOFO testing.
    """
    np.random.seed(42)
    n_samples = 100
    n_features = 5

    # Generate features
    X = np.random.randn(n_samples, n_features)
    # Target is a function of all features + noise
    y = 2 * X[:, 0] - 1.5 * X[:, 1] + 0.5 * X[:, 2] + np.random.randn(n_samples) * 0.1

    # Split into train/test
    split_idx = 80
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # Train a model
    model = RandomForestRegressor(n_estimators=10, random_state=42, max_depth=3)
    model.fit(X_train, y_train)

    # Calculate baseline R2
    y_pred_base = model.predict(X_test)
    r2_base = r2_score(y_test, y_pred_base)

    return model, X_train, y_train, X_test, y_test, r2_base


def test_lofo_sensitivity_single_feature_removal():
    """
    Test that LOFO analysis correctly identifies the change in R2
    when removing one feature at a time.
    """
    model, X_train, y_train, X_test, y_test, r2_base = _create_dummy_model_and_data()
    n_features = X_train.shape[1]

    r2_deltas = []
    removed_indices = []

    # Perform LOFO
    for i in range(n_features):
        # Create mask for features to keep (exclude index i)
        keep_indices = [j for j in range(n_features) if j != i]
        X_train_subset = X_train[:, keep_indices]
        X_test_subset = X_test[:, keep_indices]

        # Retrain model on subset
        subset_model = RandomForestRegressor(n_estimators=10, random_state=42, max_depth=3)
        subset_model.fit(X_train_subset, y_train)

        # Evaluate
        y_pred_subset = subset_model.predict(X_test_subset)
        r2_subset = r2_score(y_test, y_pred_subset)

        delta = r2_base - r2_subset
        r2_deltas.append(delta)
        removed_indices.append(i)

    # Assertions
    assert len(r2_deltas) == n_features
    assert len(removed_indices) == n_features

    # Check that removing the most important feature (index 0 in our synthetic data)
    # causes a significant drop (largest positive delta)
    # Note: In our synthetic data, feature 0 has the highest coefficient (2.0)
    # so removing it should yield the largest drop in performance.
    max_delta_idx = np.argmax(r2_deltas)
    assert removed_indices[max_delta_idx] == 0, "Expected feature 0 to be the most important"

    # Ensure deltas are non-negative (removing info shouldn't improve R2 significantly on this noise)
    # Allow small floating point tolerance
    assert all(d >= -1e-5 for d in r2_deltas), "R2 should not increase significantly when removing features"


def test_lofo_empty_feature_set_fails_gracefully():
    """
    Test that LOFO handles the edge case where only one feature exists
    (removing it leaves an empty set).
    """
    np.random.seed(42)
    X_train = np.random.randn(20, 1)
    y_train = np.random.randn(20)
    X_test = np.random.randn(10, 1)
    y_test = np.random.randn(10)

    model = RandomForestRegressor(n_estimators=5, random_state=42)
    model.fit(X_train, y_train)
    r2_base = r2_score(y_test, model.predict(X_test))

    # Try to remove the only feature
    keep_indices = []
    X_train_subset = X_train[:, keep_indices]
    X_test_subset = X_test[:, keep_indices]

    # This should raise an error or handle empty input
    # scikit-learn raises ValueError for empty feature sets
    subset_model = RandomForestRegressor(n_estimators=5, random_state=42)
    with pytest.raises(ValueError):
        subset_model.fit(X_train_subset, y_train)


def test_lofo_statistical_significance_check():
    """
    Test that the LOFO deltas can be subjected to statistical tests
    (e.g., comparing against a baseline of zero or comparing two features).
    """
    model, X_train, y_train, X_test, y_test, r2_base = _create_dummy_model_and_data()
    n_features = X_train.shape[1]

    deltas = []
    for i in range(n_features):
        keep_indices = [j for j in range(n_features) if j != i]
        X_train_sub = X_train[:, keep_indices]
        X_test_sub = X_test[:, keep_indices]

        sub_model = RandomForestRegressor(n_estimators=10, random_state=42, max_depth=3)
        sub_model.fit(X_train_sub, y_train)
        r2_sub = r2_score(y_test, sub_model.predict(X_test_sub))
        deltas.append(r2_base - r2_sub)

    # Test that the mean delta is significantly different from 0
    # Using a one-sample t-test concept (manually or via paired_t_test if adapted)
    # Here we just verify the calculation logic and that we can compute stats
    mean_delta = np.mean(deltas)
    std_delta = np.std(deltas)

    assert mean_delta > 0, "Mean performance drop should be positive"
    assert std_delta >= 0, "Std deviation must be non-negative"

    # Verify we can run a paired test if we had a second set of deltas
    # (e.g., comparing LOFO on two different random seeds)
    deltas_copy = deltas.copy()
    # Simulate a second run with slight noise
    deltas_noise = [d + np.random.normal(0, 0.01) for d in deltas]

    t_stat, p_val = paired_t_test(deltas, deltas_noise)
    assert isinstance(t_stat, float)
    assert isinstance(p_val, float)
    assert 0 <= p_val <= 1

    # Test Bonferroni correction
    corrected_p = bonferroni_correct([p_val], n_comparisons=1)
    assert corrected_p[0] <= p_val