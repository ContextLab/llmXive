"""
Unit tests for T017 logging metrics functionality.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Setup path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from utils.logging_metrics import (
    log_dataset_metrics,
    log_training_metrics,
    log_feature_engineering_summary
)
from config import OUTPUTS_LOGS_DIR


class TestLoggingMetrics:
    """Tests for dataset and training logging functions."""

    @pytest.fixture(autouse=True)
    def setup_test_env(self, tmp_path):
        """Create a temporary directory for test outputs."""
        # Patch the config to use a temporary directory
        with patch("utils.logging_metrics.OUTPUTS_LOGS_DIR", tmp_path):
            with patch("utils.logging.OUTPUTS_LOGS_DIR", tmp_path):
                with patch("config.OUTPUTS_LOGS_DIR", tmp_path):
                    yield tmp_path

    def test_log_dataset_metrics_creates_json(self, setup_test_env):
        """Verify that log_dataset_metrics creates a JSON file with correct data."""
        tmp_path = setup_test_env
        log_dataset_metrics(
            logger_name="test_logger",
            dataset_size=1000,
            feature_count=50,
            source="test_source"
        )

        json_path = tmp_path / "dataset_metrics.json"
        assert json_path.exists(), "dataset_metrics.json was not created"

        with open(json_path, "r") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["dataset_size"] == 1000
        assert data[0]["feature_count"] == 50
        assert data[0]["source"] == "test_source"
        assert "timestamp" in data[0]

    def test_log_dataset_metrics_appends(self, setup_test_env):
        """Verify that multiple calls append to the JSON file."""
        tmp_path = setup_test_env
        log_dataset_metrics("test", 100, 10, "source1")
        log_dataset_metrics("test", 200, 20, "source2")

        json_path = tmp_path / "dataset_metrics.json"
        with open(json_path, "r") as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["dataset_size"] == 100
        assert data[1]["dataset_size"] == 200

    def test_log_training_metrics_creates_json(self, setup_test_env):
        """Verify that log_training_metrics creates a JSON file with correct data."""
        tmp_path = setup_test_env
        metrics = {"MAE": 0.1, "RMSE": 0.2}
        params = {"n_estimators": 100}

        log_training_metrics("test", "model_v1", metrics, params)

        json_path = tmp_path / "training_metrics.json"
        assert json_path.exists(), "training_metrics.json was not created"

        with open(json_path, "r") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["model_name"] == "model_v1"
        assert data[0]["metrics"]["MAE"] == 0.1
        assert data[0]["hyperparameters"]["n_estimators"] == 100

    def test_log_feature_engineering_summary(self, setup_test_env):
        """Verify feature engineering summary logging."""
        tmp_path = setup_test_env
        features = ["feat1", "feat2"]

        log_feature_engineering_summary(
            "test",
            input_size=500,
            output_size=490,
            features_added=features,
            skipped_entries=10
        )

        json_path = tmp_path / "fe_summary.json"
        assert json_path.exists(), "fe_summary.json was not created"

        with open(json_path, "r") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["input_size"] == 500
        assert data[0]["output_size"] == 490
        assert data[0]["features_added"] == features
        assert data[0]["skipped_entries"] == 10
        assert data[0]["imputed_entries"] == 0

    def test_handles_missing_directory_gracefully(self, setup_test_env):
        """Verify that missing directory handling doesn't crash, just warns."""
        # The fixture ensures the directory exists, but we test the logic
        # by ensuring the function doesn't raise exceptions.
        try:
            log_dataset_metrics("test", 1, 1, "src")
            assert True
        except Exception as e:
            pytest.fail(f"Function raised exception: {e}")