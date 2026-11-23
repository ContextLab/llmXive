"""
Unit tests for metric tracking functionality (T023).

Tests for:
- compute_metrics: RMSE, R², MAE calculations
- log_metric_result: Logging structure and file appending
- track_best_hyperparameters: Best parameter identification
"""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

from metric_logger import (
    compute_metrics,
    log_metric_result,
    track_best_hyperparameters,
    save_metric_summary,
)


class TestComputeMetrics:
    """Tests for the compute_metrics function."""

    def test_compute_metrics_basic(self):
        """Test basic metric computation."""
        y_true = np.array([100, 200, 300, 400, 500])
        y_pred = np.array([110, 190, 310, 390, 510])

        metrics = compute_metrics(y_true, y_pred)

        assert "rmse" in metrics
        assert "r2" in metrics
        assert "mae" in metrics

        # All metrics should be positive
        assert metrics["rmse"] > 0
        assert metrics["mae"] > 0
        # R² should be between 0 and 1 for reasonable predictions
        assert 0 <= metrics["r2"] <= 1

    def test_perfect_prediction(self):
        """Test metrics when prediction is perfect."""
        y_true = np.array([100, 200, 300, 400, 500])
        y_pred = y_true.copy()

        metrics = compute_metrics(y_true, y_pred)

        assert metrics["rmse"] == 0.0
        assert metrics["mae"] == 0.0
        assert metrics["r2"] == 1.0

    def test_constant_target(self):
        """Test R² when all target values are identical."""
        y_true = np.array([100, 100, 100, 100])
        y_pred = np.array([100, 100, 100, 100])

        metrics = compute_metrics(y_true, y_pred)

        # When all y_true are the same, R² is defined as 0
        assert metrics["r2"] == 0.0

    def test_mismatched_lengths(self):
        """Test error on mismatched array lengths."""
        y_true = np.array([100, 200, 300])
        y_pred = np.array([100, 200])

        with pytest.raises(ValueError, match="Length mismatch"):
            compute_metrics(y_true, y_pred)

    def test_empty_arrays(self):
        """Test error on empty arrays."""
        y_true = np.array([])
        y_pred = np.array([])

        with pytest.raises(ValueError, match="empty"):
            compute_metrics(y_true, y_pred)

    def test_single_value(self):
        """Test metrics with single value."""
        y_true = np.array([100])
        y_pred = np.array([105])

        metrics = compute_metrics(y_true, y_pred)

        assert metrics["rmse"] == 5.0
        assert metrics["mae"] == 5.0
        # R² is 0 for single value (ss_tot = 0)
        assert metrics["r2"] == 0.0

    def test_negative_predictions(self):
        """Test metrics with negative predictions."""
        y_true = np.array([100, 200, 300])
        y_pred = np.array([-50, 150, 250])

        metrics = compute_metrics(y_true, y_pred)

        assert metrics["rmse"] > 0
        assert metrics["mae"] > 0

class TestLogMetricResult:
    """Tests for the log_metric_result function."""

    def test_log_metric_result_structure(self):
        """Test that logged result has correct structure."""
        metrics = {"rmse": 15.0, "r2": 0.85, "mae": 12.0}
        hyperparameters = {"n_estimators": 100}

        result = log_metric_result(
            model_type="RandomForest",
            hyperparameters=hyperparameters,
            metrics=metrics,
        )

        assert "timestamp" in result
        assert result["model_type"] == "RandomForest"
        assert result["hyperparameters"] == hyperparameters
        assert result["metrics"] == metrics

    def test_log_metric_result_with_cv(self):
        """Test logging with cross-validation details."""
        metrics = {"rmse": 15.0, "r2": 0.85, "mae": 12.0}
        hyperparameters = {"n_estimators": 100}
        fold_metrics = [
            {"r2": 0.84, "rmse": 15.5, "mae": 12.5},
            {"r2": 0.86, "rmse": 14.5, "mae": 11.5},
        ]

        result = log_metric_result(
            model_type="GradientBoosting",
            hyperparameters=hyperparameters,
            metrics=metrics,
            cv_folds=5,
            fold_metrics=fold_metrics,
        )

        assert result["cv_folds"] == 5
        assert "fold_metrics" in result
        assert "fold_statistics" in result

        stats = result["fold_statistics"]
        assert "r2_mean" in stats
        assert "r2_std" in stats
        assert "rmse_mean" in stats
        assert "rmse_std" in stats
        assert "mae_mean" in stats
        assert "mae_std" in stats

    def test_log_metric_result_file_append(self):
        """Test that results are appended to file correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_results.json"

            metrics1 = {"rmse": 15.0, "r2": 0.85, "mae": 12.0}
            metrics2 = {"rmse": 14.0, "r2": 0.88, "mae": 11.0}

            log_metric_result(
                model_type="Model1",
                hyperparameters={"a": 1},
                metrics=metrics1,
                output_path=output_path,
            )

            log_metric_result(
                model_type="Model2",
                hyperparameters={"b": 2},
                metrics=metrics2,
                output_path=output_path,
            )

            with open(output_path, "r") as f:
                results = json.load(f)

            assert len(results) == 2
            assert results[0]["model_type"] == "Model1"
            assert results[1]["model_type"] == "Model2"

class TestTrackBestHyperparameters:
    """Tests for the track_best_hyperparameters function."""

    def test_track_best_r2_maximize(self):
        """Test tracking best R² (maximize=True)."""
        comparison = []

        # First entry
        best_params, best_metrics = track_best_hyperparameters(
            "RandomForest",
            {"n_estimators": 50},
            {"r2": 0.75, "rmse": 20.0, "mae": 15.0},
            comparison,
            metric_name="r2",
            maximize=True,
        )

        assert best_params == {"n_estimators": 50}
        assert best_metrics["r2"] == 0.75

        # Second entry with worse R²
        best_params, best_metrics = track_best_hyperparameters(
            "RandomForest",
            {"n_estimators": 100},
            {"r2": 0.70, "rmse": 22.0, "mae": 17.0},
            comparison,
            metric_name="r2",
            maximize=True,
        )

        # Best should still be the first entry
        assert best_params == {"n_estimators": 50}
        assert best_metrics["r2"] == 0.75

        # Third entry with better R²
        best_params, best_metrics = track_best_hyperparameters(
            "RandomForest",
            {"n_estimators": 150},
            {"r2": 0.85, "rmse": 15.0, "mae": 12.0},
            comparison,
            metric_name="r2",
            maximize=True,
        )

        # Best should now be the third entry
        assert best_params == {"n_estimators": 150}
        assert best_metrics["r2"] == 0.85

    def test_track_best_rmse_minimize(self):
        """Test tracking best RMSE (maximize=False)."""
        comparison = []

        # First entry
        best_params, best_metrics = track_best_hyperparameters(
            "ElasticNet",
            {"alpha": 0.1},
            {"r2": 0.80, "rmse": 18.0, "mae": 14.0},
            comparison,
            metric_name="rmse",
            maximize=False,
        )

        assert best_params == {"alpha": 0.1}
        assert best_metrics["rmse"] == 18.0

        # Second entry with worse RMSE
        best_params, best_metrics = track_best_hyperparameters(
            "ElasticNet",
            {"alpha": 0.2},
            {"r2": 0.78, "rmse": 20.0, "mae": 16.0},
            comparison,
            metric_name="rmse",
            maximize=False,
        )

        # Best should still be the first entry (lower RMSE is better)
        assert best_params == {"alpha": 0.1}
        assert best_metrics["rmse"] == 18.0

        # Third entry with better RMSE
        best_params, best_metrics = track_best_hyperparameters(
            "ElasticNet",
            {"alpha": 0.05},
            {"r2": 0.82, "rmse": 16.0, "mae": 13.0},
            comparison,
            metric_name="rmse",
            maximize=False,
        )

        # Best should now be the third entry
        assert best_params == {"alpha": 0.05}
        assert best_metrics["rmse"] == 16.0

    def test_invalid_metric_name(self):
        """Test error on invalid metric name."""
        comparison = []

        with pytest.raises(ValueError, match="Invalid metric_name"):
            track_best_hyperparameters(
                "RandomForest",
                {"n_estimators": 100},
                {"r2": 0.85},
                comparison,
                metric_name="invalid_metric",
            )

    def test_missing_metric_in_dict(self):
        """Test error when metric is missing from metrics dict."""
        comparison = []

        with pytest.raises(ValueError, match="not found in metrics"):
            track_best_hyperparameters(
                "RandomForest",
                {"n_estimators": 100},
                {"rmse": 15.0, "mae": 12.0},  # Missing 'r2'
                comparison,
                metric_name="r2",
            )

class TestSaveMetricSummary:
    """Tests for the save_metric_summary function."""

    def test_save_metric_summary(self):
        """Test saving metric summary to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.json"

            results = [
                {
                    "model_type": "RandomForest",
                    "metrics": {"r2": 0.85, "rmse": 15.0},
                },
                {
                    "model_type": "GradientBoosting",
                    "metrics": {"r2": 0.88, "rmse": 14.0},
                },
            ]

            save_metric_summary(results, output_path)

            assert output_path.exists()

            with open(output_path, "r") as f:
                summary = json.load(f)

            assert "generated_at" in summary
            assert summary["total_models"] == 2
            assert len(summary["results"]) == 2

    def test_save_metric_summary_creates_directories(self):
        """Test that save_metric_summary creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir1" / "subdir2" / "summary.json"

            results = [{"model_type": "Test"}]
            save_metric_summary(results, output_path)

            assert output_path.exists()