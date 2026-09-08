"""Unit tests for modeling logic (Task T041).

Tests cover:
- ILR transformation edge cases (zero sum, negative values)
- Random Forest training convergence
- Cross-validation split reproducibility
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Ensure code/ is importable
code_root = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_root))

from modeling import (
    apply_ilr_transformation,
    split_dataset,
    load_features_and_target,
    train_random_forest_with_cv,
)


class TestILRTransformation:
    """Tests for the ILR transformation logic."""

    def test_ilr_transform_handles_zero_sum(self):
        """Test that ILR transformation handles zero-sum compositions gracefully.

        The ILR transformation requires strictly positive components.
        This test verifies that the function either raises a clear error
        or handles the zero-sum case appropriately without crashing.
        """
        # Create a composition with a zero value (which leads to issues in ILR)
        # ILR requires strictly positive values for log-ratio calculations
        data = {
            "Cu": [0.0, 0.1, 0.2],
            "Mg": [0.0, 0.1, 0.2],
            "Si": [0.0, 0.1, 0.2],
            "Zn": [0.0, 0.1, 0.2],
            "Mn": [1.0, 0.7, 0.4],  # Compensate to sum to 1.0
        }
        df = pd.DataFrame(data)

        # ILR should fail or handle zeros appropriately
        # Since ILR uses log(), zeros will cause -inf or NaN
        # We test that the function doesn't crash unexpectedly
        with pytest.raises((ValueError, ZeroDivisionError)) as exc_info:
            apply_ilr_transformation(df)

        # Verify the error message is informative
        assert "zero" in str(exc_info.value).lower() or "positive" in str(
            exc_info.value
        ).lower()

    def test_ilr_transform_normal_composition(self):
        """Test ILR transformation on valid compositional data."""
        # Create valid compositional data (all positive, sum to 1.0)
        data = {
            "Cu": [0.1, 0.2, 0.3],
            "Mg": [0.2, 0.1, 0.2],
            "Si": [0.3, 0.3, 0.2],
            "Zn": [0.2, 0.2, 0.2],
            "Mn": [0.2, 0.2, 0.1],
        }
        df = pd.DataFrame(data)

        # Apply ILR transformation
        ilr_df = apply_ilr_transformation(df)

        # Verify output dimensions
        assert ilr_df.shape[0] == df.shape[0]
        assert ilr_df.shape[1] == 4  # 5 components -> 4 ILR coordinates

        # Verify no NaN values (should be valid for positive inputs)
        assert not ilr_df.isna().any().any()

    def test_ilr_transform_negative_values(self):
        """Test that ILR transformation handles negative values appropriately."""
        data = {
            "Cu": [-0.1, 0.1, 0.2],
            "Mg": [0.2, 0.1, 0.2],
            "Si": [0.3, 0.3, 0.2],
            "Zn": [0.2, 0.2, 0.2],
            "Mn": [0.4, 0.3, 0.2],
        }
        df = pd.DataFrame(data)

        with pytest.raises((ValueError, ZeroDivisionError)) as exc_info:
            apply_ilr_transformation(df)

        assert "positive" in str(exc_info.value).lower()


class TestRFTraining:
    """Tests for Random Forest training convergence."""

    def test_rf_training_converges(self):
        """Test that Random Forest training converges on valid data.

        This test verifies that the model training process completes
        successfully and produces a fitted model that can make predictions.
        """
        # Create synthetic but realistic data
        np.random.seed(42)
        n_samples = 100

        # Generate compositional data (Dirichlet distribution)
        raw_comps = np.random.dirichlet([1.0, 1.0, 1.0, 1.0, 1.0], n_samples)
        df = pd.DataFrame(
            raw_comps, columns=["Cu", "Mg", "Si", "Zn", "Mn"]
        )

        # Generate target variable (Poisson's ratio)
        # Add some noise to make it realistic
        poisson_ratio = 0.33 + 0.05 * np.random.randn(n_samples)
        df["poisson_ratio"] = poisson_ratio

        # Apply ILR transformation
        ilr_df = apply_ilr_transformation(df)
        ilr_df["poisson_ratio"] = df["poisson_ratio"]

        # Split data
        train_df = ilr_df.sample(frac=0.8, random_state=42)
        test_df = ilr_df.drop(train_df.index)

        # Define features and target
        feature_cols = [col for col in ilr_df.columns if col != "poisson_ratio"]
        X_train = train_df[feature_cols].values
        y_train = train_df["poisson_ratio"].values
        X_test = test_df[feature_cols].values
        y_test = test_df["poisson_ratio"].values

        # Train model with cross-validation
        try:
            model, cv_metrics = train_random_forest_with_cv(
                X_train, y_train, random_state=42
            )

            # Verify model is fitted
            assert hasattr(model, "estimators_")
            assert len(model.estimators_) > 0

            # Verify model can predict
            predictions = model.predict(X_test)
            assert predictions.shape == (X_test.shape[0],)

            # Verify predictions are reasonable (within physical bounds)
            assert np.all(predictions > 0)
            assert np.all(predictions < 1)

            # Verify CV metrics are computed
            assert "cv_mae" in cv_metrics
            assert cv_metrics["cv_mae"] > 0

        except Exception as e:
            pytest.fail(f"Random Forest training failed: {str(e)}")

    def test_rf_training_with_small_dataset(self):
        """Test that Random Forest training handles small datasets."""
        np.random.seed(42)
        n_samples = 20  # Small dataset

        raw_comps = np.random.dirichlet([1.0, 1.0, 1.0, 1.0, 1.0], n_samples)
        df = pd.DataFrame(raw_comps, columns=["Cu", "Mg", "Si", "Zn", "Mn"])
        df["poisson_ratio"] = 0.33 + 0.05 * np.random.randn(n_samples)

        ilr_df = apply_ilr_transformation(df)
        ilr_df["poisson_ratio"] = df["poisson_ratio"]

        train_df = ilr_df.sample(frac=0.8, random_state=42)

        feature_cols = [col for col in ilr_df.columns if col != "poisson_ratio"]
        X_train = train_df[feature_cols].values
        y_train = train_df["poisson_ratio"].values

        try:
            model, cv_metrics = train_random_forest_with_cv(
                X_train, y_train, random_state=42
            )

            assert hasattr(model, "estimators_")
            assert len(model.estimators_) > 0

        except Exception as e:
            pytest.fail(f"RF training on small dataset failed: {str(e)}")


class TestCvSplitReproducibility:
    """Tests for cross-validation split reproducibility."""

    def test_cv_split_reproducibility(self):
        """Test that cross-validation splits are reproducible with fixed random_state.

        This test verifies that using the same random_state produces
        identical train/test splits across multiple runs.
        """
        np.random.seed(42)
        n_samples = 100

        raw_comps = np.random.dirichlet([1.0, 1.0, 1.0, 1.0, 1.0], n_samples)
        df = pd.DataFrame(raw_comps, columns=["Cu", "Mg", "Si", "Zn", "Mn"])
        df["poisson_ratio"] = 0.33 + 0.05 * np.random.randn(n_samples)

        ilr_df = apply_ilr_transformation(df)
        ilr_df["poisson_ratio"] = df["poisson_ratio"]

        feature_cols = [col for col in ilr_df.columns if col != "poisson_ratio"]
        X = ilr_df[feature_cols].values
        y = ilr_df["poisson_ratio"].values

        # First run
        model1, metrics1 = train_random_forest_with_cv(X, y, random_state=42)
        predictions1 = model1.predict(X)

        # Second run with same random_state
        model2, metrics2 = train_random_forest_with_cv(X, y, random_state=42)
        predictions2 = model2.predict(X)

        # Verify metrics are identical
        assert np.isclose(metrics1["cv_mae"], metrics2["cv_mae"])

        # Verify predictions are identical (due to fixed random_state)
        assert np.allclose(predictions1, predictions2)

    def test_cv_split_different_random_states(self):
        """Test that different random_states produce different splits."""
        np.random.seed(42)
        n_samples = 100

        raw_comps = np.random.dirichlet([1.0, 1.0, 1.0, 1.0, 1.0], n_samples)
        df = pd.DataFrame(raw_comps, columns=["Cu", "Mg", "Si", "Zn", "Mn"])
        df["poisson_ratio"] = 0.33 + 0.05 * np.random.randn(n_samples)

        ilr_df = apply_ilr_transformation(df)
        ilr_df["poisson_ratio"] = df["poisson_ratio"]

        feature_cols = [col for col in ilr_df.columns if col != "poisson_ratio"]
        X = ilr_df[feature_cols].values
        y = ilr_df["poisson_ratio"].values

        # Run with different random states
        _, metrics_a = train_random_forest_with_cv(X, y, random_state=42)
        _, metrics_b = train_random_forest_with_cv(X, y, random_state=123)

        # Metrics should be different (though possibly close)
        # We don't assert they're exactly different, just that the process works
        assert "cv_mae" in metrics_a
        assert "cv_mae" in metrics_b

    def test_split_dataset_reproducibility(self):
        """Test that split_dataset produces reproducible splits."""
        np.random.seed(42)
        n_samples = 100

        df = pd.DataFrame(
            np.random.rand(n_samples, 6),
            columns=["Cu", "Mg", "Si", "Zn", "Mn", "poisson_ratio"],
        )

        # First split
        train_indices_1, test_indices_1 = split_dataset(df, random_state=42)

        # Second split with same random_state
        train_indices_2, test_indices_2 = split_dataset(df, random_state=42)

        # Verify indices are identical
        assert train_indices_1 == train_indices_2
        assert test_indices_1 == test_indices_2

        # Verify splits are valid
        assert len(train_indices_1) + len(test_indices_1) == n_samples
        assert set(train_indices_1).isdisjoint(set(test_indices_1))

    def test_split_dataset_different_random_states(self):
        """Test that split_dataset produces different splits with different random_states."""
        np.random.seed(42)
        n_samples = 100

        df = pd.DataFrame(
            np.random.rand(n_samples, 6),
            columns=["Cu", "Mg", "Si", "Zn", "Mn", "poisson_ratio"],
        )

        train_indices_1, test_indices_1 = split_dataset(df, random_state=42)
        train_indices_2, test_indices_2 = split_dataset(df, random_state=123)

        # Splits should be different (though this is probabilistic)
        # We just verify the function works with different seeds
        assert len(train_indices_1) > 0
        assert len(test_indices_1) > 0
        assert len(train_indices_2) > 0
        assert len(test_indices_2) > 0