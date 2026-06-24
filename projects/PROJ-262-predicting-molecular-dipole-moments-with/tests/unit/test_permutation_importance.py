"""Unit tests for the permutation importance implementation."""

from __future__ import annotations

import pathlib
import json

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from code.attribution.permutation_importance import compute_permutation_importance, main

def test_compute_permutation_importance_returns_dict(tmp_path: pathlib.Path) -> None:
    # Create a tiny synthetic dataset.
    X = pd.DataFrame(
        {
            "feat_a": [0, 1, 0, 1, 0, 1],
            "feat_b": [1, 1, 1, 0, 0, 0],
        }
    )
    y = pd.Series([0, 1, 0, 1, 0, 1])

    # Train a simple RandomForestRegressor.
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)

    # Compute permutation importance.
    importances = compute_permutation_importance(model, X, y, n_repeats=5, random_state=0)

    # The result should be a dict with both feature names.
    assert isinstance(importances, dict)
    assert set(importances.keys()) == {"feat_a", "feat_b"}
    # Importances are non‑negative floats.
    for value in importances.values():
        assert isinstance(value, float)
        assert value >= 0.0

def test_cli_writes_json(tmp_path: pathlib.Path) -> None:
    # Prepare synthetic data.
    X = pd.DataFrame(
        {
            "f1": [0, 1, 0, 1],
            "f2": [1, 0, 1, 0],
        }
    )
    y = pd.Series([0.1, 0.9, 0.2, 0.8])
    df = X.copy()
    df["dipole_moment"] = y
    features_path = tmp_path / "features.parquet"
    df.to_parquet(features_path)

    # Train and save a model.
    model = RandomForestRegressor(n_estimators=5, random_state=0)
    model.fit(X, y)
    model_path = tmp_path / "rf.pkl"
    import joblib

    joblib.dump(model, model_path)

    # Run the CLI entry point.
    output_path = tmp_path / "attributions.json"

    # Simulate command‑line arguments.
    import sys

    argv_backup = sys.argv
    try:
        sys.argv = [
            "permutation_importance.py",
            "--model-path",
            str(model_path),
            "--features-path",
            str(features_path),
            "--output-path",
            str(output_path),
        ]
        main()
    finally:
        sys.argv = argv_backup

    # Verify output file exists and contains valid JSON.
    assert output_path.is_file()
    with output_path.open() as f:
        data = json.load(f)
    assert set(data.keys()) == {"f1", "f2"}
    for v in data.values():
        assert isinstance(v, float)