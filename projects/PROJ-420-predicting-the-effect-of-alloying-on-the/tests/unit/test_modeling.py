"""
Unit tests for modeling logic in code/modeling.py.

These tests verify:
1. Data loading and feature/target separation
2. Random Forest training with cross-validation
3. Test set evaluation metrics
4. Model serialization and deserialization
"""

import pytest
import numpy as np
import pandas as pd
import pickle
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

# Import the module under test
from code.modeling import (
    load_features_and_target,
    train_random_forest_with_cv,
    evaluate_model_on_test,
    run_modeling_pipeline,
    evaluate_model_model_on_test
)
from code.config import get_config


class TestLoadFeaturesAndTarget:
    """Tests for load_features_and_target function."""

    def test_load_features_and_target_with_valid_data(self):
        """Test loading features and target from a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock CSV file with ILR features and target
            csv_path = Path(tmpdir) / "mock_features.csv"
            data = {
                'ilr_1': [0.1, 0.2, 0.3, 0.4, 0.5],
                'ilr_2': [0.2, 0.3, 0.4, 0.5, 0.6],
                'ilr_3': [0.3, 0.4, 0.5, 0.6, 0.7],
                'ilr_4': [0.4, 0.5, 0.6, 0.7, 0.8],
                'poissons_ratio': [0.33, 0.34, 0.35, 0.36, 0.37]
            }
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)

            X, y = load_features_and_target(str(csv_path))

            assert X.shape == (5, 4)
            assert y.shape == (5,)
            assert list(X.columns) == ['ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']
            assert 'poissons_ratio' not in X.columns

    def test_load_features_and_target_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_features_and_target("/nonexistent/path/file.csv")

    def test_load_features_and_target_no_target_column(self):
        """Test that missing target column raises KeyError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "no_target.csv"
            data = {
                'ilr_1': [0.1, 0.2, 0.3],
                'ilr_2': [0.2, 0.3, 0.4]
            }
            pd.DataFrame(data).to_csv(csv_path, index=False)

            with pytest.raises(KeyError):
                load_features_and_target(str(csv_path))


class TestTrainRandomForestWithCV:
    """Tests for train_random_forest_with_cv function."""

    def test_train_random_forest_with_cv_basic(self):
        """Test basic training with cross-validation."""
        # Create mock data
        X = np.random.rand(100, 4)
        y = np.random.rand(100)

        model, cv_results = train_random_forest_with_cv(X, y, cv_folds=3)

        assert model is not None
        assert hasattr(model, 'predict')
        assert isinstance(cv_results, dict)
        assert 'mean_cv_score' in cv_results or 'mean_test_score' in cv_results

    def test_train_random_forest_with_cv_small_dataset(self):
        """Test training with a small dataset."""
        X = np.random.rand(10, 4)
        y = np.random.rand(10)

        model, cv_results = train_random_forest_with_cv(X, y, cv_folds=2)

        assert model is not None
        assert hasattr(model, 'predict')

    def test_train_random_forest_with_cv_custom_params(self):
        """Test training with custom hyperparameters."""
        X = np.random.rand(50, 4)
        y = np.random.rand(50)

        model, cv_results = train_random_forest_with_cv(
            X, y, cv_folds=5, n_estimators=10, max_depth=3
        )

        assert model.n_estimators == 10
        assert model.max_depth == 3


class TestEvaluateModelOnTest:
    """Tests for evaluate_model_on_test function."""

    def test_evaluate_model_on_test_basic(self):
        """Test basic model evaluation on test set."""
        # Create mock model and data
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=5, random_state=42)

        X_test = np.random.rand(20, 4)
        y_test = np.random.rand(20)

        # Train model on some data first
        X_train = np.random.rand(80, 4)
        y_train = np.random.rand(80)
        model.fit(X_train, y_train)

        metrics = evaluate_model_on_test(model, X_test, y_test)

        assert isinstance(metrics, dict)
        assert 'mae' in metrics
        assert 'rmse' in metrics
        assert 'r2' in metrics
        assert metrics['mae'] >= 0
        assert metrics['rmse'] >= 0
        assert metrics['r2'] <= 1.0

    def test_evaluate_model_on_test_perfect_predictions(self):
        """Test evaluation with perfect predictions."""
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=10, random_state=42)

        X_test = np.random.rand(20, 4)
        y_test = np.random.rand(20)

        # Create a mock model that predicts perfectly
        class PerfectModel:
            def predict(self, X):
                return y_test

        perfect_model = PerfectModel()
        metrics = evaluate_model_on_test(perfect_model, X_test, y_test)

        assert metrics['mae'] == 0.0
        assert metrics['rmse'] == 0.0
        assert metrics['r2'] == 1.0


class TestEvaluateModelModelOnTest:
    """Tests for evaluate_model_model_on_test function."""

    def test_evaluate_model_model_on_test_delegation(self):
        """Test that evaluate_model_model_on_test delegates correctly."""
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=5, random_state=42)

        X_test = np.random.rand(20, 4)
        y_test = np.random.rand(20)

        # Train model
        X_train = np.random.rand(80, 4)
        y_train = np.random.rand(80)
        model.fit(X_train, y_train)

        # This function should be an alias or wrapper
        metrics = evaluate_model_model_on_test(model, X_test, y_test)

        assert isinstance(metrics, dict)
        assert 'mae' in metrics


class TestRunModelingPipeline:
    """Tests for run_modeling_pipeline function."""

    def test_run_modeling_pipeline_integration(self):
        """Test the full modeling pipeline with temporary files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock feature file
            features_path = Path(tmpdir) / "features.csv"
            data = {
                'ilr_1': np.random.rand(100),
                'ilr_2': np.random.rand(100),
                'ilr_3': np.random.rand(100),
                'ilr_4': np.random.rand(100),
                'poissons_ratio': np.random.rand(100)
            }
            pd.DataFrame(data).to_csv(features_path, index=False)

            # Create output directories
            model_dir = Path(tmpdir) / "models"
            metrics_dir = Path(tmpdir) / "docs" / "outputs"
            model_dir.mkdir(parents=True)
            metrics_dir.mkdir(parents=True)

            # Run pipeline
            result = run_modeling_pipeline(
                features_path=str(features_path),
                model_output_path=str(model_dir / "rf_model.pkl"),
                metrics_output_path=str(metrics_dir / "model_metrics.json"),
                cv_folds=3
            )

            # Verify outputs
            assert result is not None
            assert 'model' in result
            assert 'cv_results' in result
            assert 'test_metrics' in result

            # Check model file exists
            assert Path(model_dir / "rf_model.pkl").exists()

            # Check metrics file exists and is valid JSON
            assert Path(metrics_dir / "model_metrics.json").exists()
            with open(metrics_dir / "model_metrics.json", 'r') as f:
                metrics_data = json.load(f)
                assert 'mae' in metrics_data
                assert 'rmse' in metrics_data
                assert 'r2' in metrics_data

    def test_run_modeling_pipeline_with_config(self):
        """Test pipeline execution using config paths."""
        config = get_config()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock feature file
            features_path = Path(tmpdir) / "features.csv"
            data = {
                'ilr_1': np.random.rand(50),
                'ilr_2': np.random.rand(50),
                'ilr_3': np.random.rand(50),
                'ilr_4': np.random.rand(50),
                'poissons_ratio': np.random.rand(50)
            }
            pd.DataFrame(data).to_csv(features_path, index=False)

            model_path = Path(tmpdir) / "model.pkl"
            metrics_path = Path(tmpdir) / "metrics.json"

            result = run_modeling_pipeline(
                features_path=str(features_path),
                model_output_path=str(model_path),
                metrics_output_path=str(metrics_path),
                cv_folds=2
            )

            assert result is not None
            assert model_path.exists()
            assert metrics_path.exists()


class TestModelSerialization:
    """Tests for model save/load functionality."""

    def test_model_serialization_round_trip(self):
        """Test that model can be saved and loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from sklearn.ensemble import RandomForestRegressor

            # Create and train a model
            model = RandomForestRegressor(n_estimators=5, random_state=42)
            X = np.random.rand(50, 4)
            y = np.random.rand(50)
            model.fit(X, y)

            # Save model
            model_path = Path(tmpdir) / "test_model.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)

            # Load model
            with open(model_path, 'rb') as f:
                loaded_model = pickle.load(f)

            # Verify predictions match
            X_test = np.random.rand(10, 4)
            original_pred = model.predict(X_test)
            loaded_pred = loaded_model.predict(X_test)

            np.testing.assert_array_almost_equal(original_pred, loaded_pred)

    def test_metrics_serialization(self):
        """Test that metrics can be saved and loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics = {
                'mae': 0.05,
                'rmse': 0.07,
                'r2': 0.95,
                'cv_mean_score': 0.93,
                'cv_std_score': 0.02
            }

            metrics_path = Path(tmpdir) / "metrics.json"
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f)

            with open(metrics_path, 'r') as f:
                loaded_metrics = json.load(f)

            assert loaded_metrics == metrics


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_training_with_very_small_dataset(self):
        """Test training with minimal dataset."""
        X = np.random.rand(5, 4)
        y = np.random.rand(5)

        # Should handle small dataset gracefully
        model, cv_results = train_random_forest_with_cv(X, y, cv_folds=2)
        assert model is not None

    def test_evaluation_with_single_sample(self):
        """Test evaluation with single test sample."""
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=5, random_state=42)

        X_train = np.random.rand(50, 4)
        y_train = np.random.rand(50)
        model.fit(X_train, y_train)

        X_test = np.random.rand(1, 4)
        y_test = np.random.rand(1)

        metrics = evaluate_model_on_test(model, X_test, y_test)
        assert isinstance(metrics, dict)
        assert 'mae' in metrics

    def test_invalid_cv_folds(self):
        """Test behavior with invalid CV folds."""
        X = np.random.rand(10, 4)
        y = np.random.rand(10)

        # Should handle cv_folds > samples gracefully or raise appropriate error
        with pytest.raises(ValueError):
            train_random_forest_with_cv(X, y, cv_folds=20)