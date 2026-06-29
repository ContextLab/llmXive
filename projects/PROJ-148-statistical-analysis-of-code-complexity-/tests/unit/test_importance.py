"""
Unit tests for the ``code/modeling/importance.py`` module.
"""
import pathlib
import tempfile

import numpy as np
import pandas as pd
import joblib

from modeling.importance import get_importance, save_importance


class DummyLogisticRegression:
    """Minimal stub mimicking sklearn's LogisticRegression with L1 regularisation."""

    def __init__(self, coef):
        # sklearn stores coefficients as a 2‑D array (n_classes, n_features)
        self.coef_ = np.atleast_2d(coef)


class DummyRandomForest:
    """Minimal stub mimicking sklearn's RandomForestClassifier feature_importances_."""

    def __init__(self, importances):
        self.feature_importances_ = np.asarray(importances)


def test_get_importance_shapes():
    """Verify that ``get_importance`` returns correctly‑shaped arrays."""
    n_features = 5
    coef = np.arange(n_features) * -0.1  # some negative weights
    importances = np.arange(n_features) * 0.2 + 0.1

    primary = DummyLogisticRegression(coef)
    alternative = DummyRandomForest(importances)
    feature_names = [f"f{i}" for i in range(n_features)]

    importance = get_importance(primary, alternative, feature_names)

    assert "primary_coeff" in importance
    assert "rf_importance" in importance
    np.testing.assert_array_equal(importance["primary_coeff"], coef)
    np.testing.assert_array_equal(importance["rf_importance"], importances)


def test_save_importance_creates_expected_csv():
    """The CSV should contain three columns and retain the feature order."""
    n_features = 3
    coef = np.array([0.3, -0.2, 0.0])
    importances = np.array([0.6, 0.2, 0.2])
    feature_names = ["size", "cyclomatic", "halstead"]

    importance = {
        "primary_coeff": coef,
        "rf_importance": importances,
    }

    with tempfile.TemporaryDirectory() as td:
        out_path = pathlib.Path(td) / "importance.csv"

        # Write the CSV
        save_importance(importance, feature_names, out_path)

        # Read back and validate
        df = pd.read_csv(out_path)
        assert list(df.columns) == ["feature", "primary_coeff", "rf_importance"]
        assert df["feature"].tolist() == feature_names
        np.testing.assert_array_almost_equal(df["primary_coeff"].values, coef)
        np.testing.assert_array_almost_equal(df["rf_importance"].values, importances)


def test_cli_workflow():
    """End‑to‑end test of the CLI using temporary files."""
    n_features = 4
    coef = np.linspace(-0.4, 0.0, n_features)
    importances = np.linspace(0.1, 0.4, n_features)
    feature_names = [f"feat{i}" for i in range(n_features)]

    primary = DummyLogisticRegression(coef)
    alternative = DummyRandomForest(importances)

    with tempfile.TemporaryDirectory() as td:
        td_path = pathlib.Path(td)

        # Persist dummy models
        primary_path = td_path / "primary.pkl"
        alternative_path = td_path / "alternative.pkl"
        joblib.dump(primary, primary_path)
        joblib.dump(alternative, alternative_path)

        # Create a dummy feature CSV (only header is needed)
        features_path = td_path / "features.csv"
        pd.DataFrame(columns=feature_names).to_csv(features_path, index=False)

        # Destination for importance CSV
        out_path = td_path / "out.csv"

        # Run the module as a script
        import subprocess, sys
        cmd = [
            sys.executable,
            "-m",
            "modeling.importance",
            "--primary-model",
            str(primary_path),
            "--alternative-model",
            str(alternative_path),
            "--features",
            str(features_path),
            "--output",
            str(out_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Verify output CSV content
        df = pd.read_csv(out_path)
        assert df.shape[0] == n_features
        np.testing.assert_array_almost_equal(df["primary_coeff"].values, coef)
        np.testing.assert_array_almost_equal(df["rf_importance"].values, importances)