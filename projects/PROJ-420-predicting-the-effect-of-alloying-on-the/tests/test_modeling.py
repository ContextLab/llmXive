"""
Unit tests for the modeling module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor

from code.modeling import (
    load_features_and_target,
    apply_ilr_transformation,
    save_split_indices,
    load_split_indices,
    split_data,
    train_random_forest_with_cv,
    evaluate_model_on_test,
    save_model,
    load_model,
    save_best_hyperparameters,
    load_best_hyperparameters,
    save_model_metrics,
    save_residuals,
    save_methodological_flags,
    run_modeling_pipeline,
    main
)


class TestILRTransform:
    """Tests for ILR transformation logic."""

    def test_ilr_transform_handles_zero_sum(self):
        """Test that ILR transformation handles zero values correctly."""
        # Create a DataFrame with a zero value
        X = pd.DataFrame({
            'Cu': [0.0, 0.1, 0.2],
            'Mg': [0.1, 0.1, 0.1],
            'Si': [0.1, 0.1, 0.1],
            'Zn': [0.1, 0.1, 0.1],
            'Mn': [0.1, 0.1, 0.1]
        })

        # This should not raise an error
        X_ilr = apply_ilr_transformation(X)

        assert X_ilr.shape[0] == 3
        assert X_ilr.shape[1] == 4  # 5 components -> 4 ILR coordinates

        # Check that no NaN values are present
        assert not X_ilr.isna().any().any()


    def test_ilr_transform_output_shape(self):
        """Test that ILR transformation produces correct output shape."""
        n_samples = 100
        X = pd.DataFrame({
            'Cu': np.random.rand(n_samples) * 0.5,
            'Mg': np.random.rand(n_samples) * 0.5,
            'Si': np.random.rand(n_samples) * 0.5,
            'Zn': np.random.rand(n_samples) * 0.5,
            'Mn': np.random.rand(n_samples) * 0.5
        })

        # Normalize to sum to 1
        X = X.div(X.sum(axis=1), axis=0)

        X_ilr = apply_ilr_transformation(X)

        assert X_ilr.shape == (n_samples, 4)


class TestRFTraining:
    """Tests for Random Forest training logic."""

    def test_rf_training_converges(self):
        """Test that Random Forest training converges without errors."""
        # Create dummy data
        X_train = pd.DataFrame({
            'ilr_0': np.random.rand(50),
            'ilr_1': np.random.rand(50),
            'ilr_2': np.random.rand(50),
            'ilr_3': np.random.rand(50)
        })
        y_train = pd.Series(np.random.rand(50))

        # Train a model
        model, best_params, cv_score = train_random_forest_with_cv(
            X_train, y_train,
            param_grid={'n_estimators': [10, 20], 'max_depth': [5, 10]}
        )

        assert model is not None
        assert isinstance(model, RandomForestRegressor)
        assert 'n_estimators' in best_params
        assert isinstance(cv_score, float)
        assert cv_score >= 0


    def test_rf_training_with_custom_params(self):
        """Test training with custom hyperparameter grid."""
        X_train = pd.DataFrame({
            'ilr_0': np.random.rand(30),
            'ilr_1': np.random.rand(30),
            'ilr_2': np.random.rand(30),
            'ilr_3': np.random.rand(30)
        })
        y_train = pd.Series(np.random.rand(30))

        custom_grid = {
            'n_estimators': [5],
            'max_depth': [3],
            'min_samples_split': [2]
        }

        model, best_params, cv_score = train_random_forest_with_cv(
            X_train, y_train, param_grid=custom_grid
        )

        assert best_params == custom_grid


class TestCVCrossValidation:
    """Tests for cross-validation logic."""

    def test_cv_split_reproducibility(self):
        """Test that CV splits are reproducible with fixed random state."""
        X_train = pd.DataFrame({
            'ilr_0': np.random.rand(50),
            'ilr_1': np.random.rand(50),
            'ilr_2': np.random.rand(50),
            'ilr_3': np.random.rand(50)
        })
        y_train = pd.Series(np.random.rand(50))

        # Run twice with same random state
        _, params1, score1 = train_random_forest_with_cv(
            X_train, y_train,
            param_grid={'n_estimators': [10], 'max_depth': [5]}
        )

        _, params2, score2 = train_random_forest_with_cv(
            X_train, y_train,
            param_grid={'n_estimators': [10], 'max_depth': [5]}
        )

        # Scores should be identical
        assert score1 == score2
        assert params1 == params2


class TestSplitIndices:
    """Tests for split indices serialization."""

    def test_save_and_load_split_indices(self):
        """Test saving and loading split indices."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "split_indices.json"

            train_indices = [1, 2, 3, 4, 5]
            test_indices = [6, 7, 8, 9, 10]

            save_split_indices(train_indices, test_indices, str(output_path))

            loaded_train, loaded_test = load_split_indices(str(output_path))

            assert loaded_train == train_indices
            assert loaded_test == test_indices

            # Verify file content
            with open(output_path, 'r') as f:
                data = json.load(f)
                assert data['train_indices'] == train_indices
                assert data['test_indices'] == test_indices


class TestModelSerialization:
    """Tests for model serialization."""

    def test_save_and_load_model(self):
        """Test saving and loading a Random Forest model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "test_model.pkl"

            # Create a simple model
            model = RandomForestRegressor(n_estimators=10, random_state=42)

            # Save and load
            save_model(model, str(model_path))
            loaded_model = load_model(str(model_path))

            assert loaded_model is not None
            assert isinstance(loaded_model, RandomForestRegressor)
            assert loaded_model.n_estimators == 10


    def test_model_serialization_compression(self):
        """Test that model is saved with compression."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "test_model.pkl"

            model = RandomForestRegressor(n_estimators=10, random_state=42)
            save_model(model, str(model_path), compress=3, protocol=3)

            # Check file exists and has reasonable size
            assert os.path.exists(model_path)
            assert os.path.getsize(model_path) > 0


class TestHyperparameterSaving:
    """Tests for hyperparameter saving."""

    def test_save_and_load_hyperparameters(self):
        """Test saving and loading best hyperparameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "hyperparams.json"

            best_params = {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 2
            }

            save_best_hyperparameters(best_params, str(output_path))
            loaded_params = load_best_hyperparameters(str(output_path))

            assert loaded_params == best_params


class TestMetricsSaving:
    """Tests for metrics and residuals saving."""

    def test_save_model_metrics(self):
        """Test saving model metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metrics.json"

            save_model_metrics(
                cv_mae=0.05,
                cv_ci_lower=0.04,
                cv_ci_upper=0.06,
                test_mae=0.07,
                output_path=str(output_path)
            )

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert data['cv_mae'] == 0.05
            assert data['test_mae'] == 0.07

    def test_save_residuals(self):
        """Test saving residuals."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "residuals.json"

            y_true = [1.0, 2.0, 3.0]
            y_pred = [1.1, 2.1, 2.9]
            indices = [10, 20, 30]

            save_residuals(y_true, y_pred, indices, str(output_path))

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert len(data['residuals']) == 3
            assert data['indices'] == indices

    def test_save_methodological_flags(self):
        """Test saving methodological flags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flags.json"

            save_methodological_flags(mae_flag=True, cv_mae=0.06, output_path=str(output_path))

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert data['mae_flag'] is True
            assert data['cv_mae'] == 0.06


class TestEvaluation:
    """Tests for model evaluation."""

    def test_evaluate_model_on_test(self):
        """Test evaluation on test set."""
        # Create a simple model
        model = RandomForestRegressor(n_estimators=10, random_state=42)

        # Dummy data
        X_test = pd.DataFrame({
            'ilr_0': [0.1, 0.2, 0.3],
            'ilr_1': [0.1, 0.2, 0.3],
            'ilr_2': [0.1, 0.2, 0.3],
            'ilr_3': [0.1, 0.2, 0.3]
        })
        y_test = pd.Series([0.5, 0.6, 0.7])

        # Train model first (to avoid random prediction issues)
        model.fit(X_test, y_test)

        mae = evaluate_model_on_test(model, X_test, y_test)

        assert isinstance(mae, float)
        assert mae >= 0