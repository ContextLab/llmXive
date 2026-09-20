import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.modeling.train import (
    load_target_data,
    normalize_target,
    train_xgboost_model,
    run_training_pipeline,
    main,
)
from src.utils.logging import get_logger


@pytest.fixture
def temp_feature_file():
    """Create a temporary feature matrix file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        feature_path = Path(tmpdir) / "features.parquet"
        features = pd.DataFrame({
            "feat1": np.random.randn(100),
            "feat2": np.random.randn(100),
            "feat3": np.random.randn(100),
            "target": np.random.randn(100),
        })
        features.to_parquet(feature_path)
        yield str(feature_path)


@pytest.fixture
def mock_config():
    """Return a mock configuration dictionary."""
    return {
        "model": {
            "xgboost": {
                "n_estimators": 10,
                "max_depth": 3,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": 42,
            }
        }
    }


def test_load_target_data(temp_feature_file):
    """Test loading target data from feature file."""
    features, target = load_target_data(temp_feature_file)
    assert features.shape[0] == 100
    assert "target" not in features.columns
    assert len(target) == 100


def test_normalize_target():
    """Test target normalization."""
    target = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    normalized, params = normalize_target(target)

    assert abs(normalized.mean()) < 1e-6
    assert abs(normalized.std() - 1.0) < 1e-6
    assert "mean" in params
    assert "std" in params


@patch("src.modeling.train.xgb.XGBRegressor")
def test_train_xgboost_model(mock_xgb, temp_feature_file, mock_config):
    """Test XGBoost model training."""
    features, target = load_target_data(temp_feature_file)

    # Mock the model
    mock_model = MagicMock()
    mock_model.predict.return_value = np.random.randn(100)
    mock_xgb.return_value = mock_model

    model, metrics = train_xgboost_model(features, target, mock_config)

    assert model is not None
    assert "mean_spearman_rho" in metrics
    assert "overall_spearman_rho" in metrics
    assert "runtime_seconds" in metrics


def test_run_training_pipeline_saves_artifacts(temp_feature_file, mock_config):
    """Test that the training pipeline saves model and log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = Path(tmpdir) / "model.json"
        log_path = Path(tmpdir) / "training_log.json"
        config_path = Path(tmpdir) / "config.yaml"
        cv_path = Path(tmpdir) / "cv_results.csv"

        # Create a minimal config file
        with open(config_path, "w") as f:
            f.write("model:\n  xgboost:\n    n_estimators: 10\n    max_depth: 3\n")

        # Mock the config loader to return our mock config
        with patch("src.modeling.train.load_config", return_value=mock_config):
            # Mock the XGBoost model to avoid actual training
            with patch("src.modeling.train.xgb.XGBRegressor") as mock_xgb:
                mock_model = MagicMock()
                mock_model.predict.return_value = np.random.randn(100)
                mock_xgb.return_value = mock_model

                # Mock state manager functions
                with patch("src.modeling.train.register_artifact"), \
                     patch("src.modeling.train.update_stage_status"):

                    result = run_training_pipeline(
                        feature_path=temp_feature_file,
                        model_output_path=str(model_path),
                        log_output_path=str(log_path),
                        config_path=str(config_path),
                        cv_results_path=str(cv_path),
                    )

                    # Verify files were created
                    assert model_path.exists(), "Model file not created"
                    assert log_path.exists(), "Log file not created"
                    assert cv_path.exists(), "CV results file not created"

                    # Verify log content
                    with open(log_path) as f:
                        log_data = json.load(f)
                    assert "timestamp" in log_data
                    assert "metrics" in log_data
                    assert log_data["n_samples"] == 100


def test_main_integration(temp_feature_file, mock_config):
    """Test the main function with command line arguments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = Path(tmpdir) / "model.json"
        log_path = Path(tmpdir) / "training_log.json"
        config_path = Path(tmpdir) / "config.yaml"
        cv_path = Path(tmpdir) / "cv_results.csv"

        # Create config file
        with open(config_path, "w") as f:
            f.write("model:\n  xgboost:\n    n_estimators: 5\n    max_depth: 2\n")

        # Mock dependencies
        with patch("src.modeling.train.load_config", return_value=mock_config), \
             patch("src.modeling.train.xgb.XGBRegressor") as mock_xgb, \
             patch("src.modeling.train.register_artifact"), \
             patch("src.modeling.train.update_stage_status"):

            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.randn(100)
            mock_xgb.return_value = mock_model

            # Run main with args
            import sys
            original_argv = sys.argv
            try:
                sys.argv = [
                    "test",
                    "--config", str(config_path),
                    "--features", temp_feature_file,
                    "--model-output", str(model_path),
                    "--log-output", str(log_path),
                    "--cv-results", str(cv_path),
                ]
                main()

                assert model_path.exists()
                assert log_path.exists()
                assert cv_path.exists()
            finally:
                sys.argv = original_argv
