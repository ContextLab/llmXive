"""Unit tests for the nested CV pipeline in ``code/04_train_model.py``."""

import pathlib
import pandas as pd
import numpy as np

from code._04_train_model import (
    define_decline_label,
    CollinearityTransformer,
    make_inner_pipeline,
    train_and_evaluate_nested_cv,
)

# Helper to create a tiny synthetic dataset – this test does NOT rely on real data.
def _create_dummy_data():
    rng = np.random.default_rng(42)
    # 30 subjects, 10 synthetic graph‑metric features
    X = pd.DataFrame(rng.normal(size=(30, 10)), columns=[f"f{i}" for i in range(10)])
    # Create a simple label with some drops
    y = pd.Series(rng.integers(0, 2, size=30))
    return X, y

def test_define_decline_label():
    df = pd.DataFrame({
        "mmse_baseline": [30, 28, 27],
        "mmse_followup": [27, 28, 23],
        "moca_baseline": [28, 27, 30],
        "moca_followup": [27, 24, 30],
    })
    labels = define_decline_label(df)
    # First subject drops 3 on MMSE -> 1
    # Second drops 0 on MMSE, 3 on MoCA -> 1
    # Third drops 0 on both -> 0
    assert list(labels) == [1, 1, 0]

def test_collinearity_transformer():
    # Create perfectly correlated columns
    X = pd.DataFrame({
        "a": np.arange(10),
        "b": np.arange(10) * 2,  # perfectly correlated with a
        "c": np.random.rand(10),
    })
    transformer = CollinearityTransformer(threshold=0.95)
    transformer.fit(X)
    X_t = transformer.transform(X)
    # One of a or b must be dropped; c must remain.
    assert "c" in X_t.columns
    assert len(X_t.columns) == 2

def test_make_inner_pipeline():
    pipeline = make_inner_pipeline()
    assert hasattr(pipeline, "fit")
    assert hasattr(pipeline, "predict_proba")

def test_train_and_evaluate_nested_cv():
    X, y = _create_dummy_data()
    model, perf = train_and_evaluate_nested_cv(X, y)
    # Model should be a RandomForestClassifier
    from sklearn.ensemble import RandomForestClassifier
    assert isinstance(model, RandomForestClassifier)
    # Performance dict must contain expected keys
    for key in ["roc_auc_mean", "accuracy_mean", "f1_mean", "best_params"]:
        assert key in perf

# The tests are deliberately lightweight to run quickly in CI.  They verify
# that the core functions exist and behave plausibly.