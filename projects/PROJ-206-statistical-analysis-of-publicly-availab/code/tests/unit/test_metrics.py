"""
Unit tests for src/evaluation/metrics.py
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path

from src.evaluation.metrics import calculate_rmse, calculate_mae, evaluate_frequentist_forecasts


class TestRMSE:
    def test_rmse_perfect_prediction(self):
        preds = np.array([1.0, 2.0, 3.0])
        actuals = np.array([1.0, 2.0, 3.0])
        assert calculate_rmse(preds, actuals) == 0.0

    def test_rmse_constant_error(self):
        preds = np.array([1.0, 2.0, 3.0])
        actuals = np.array([2.0, 3.0, 4.0])
        # Errors: [-1, -1, -1], Squared: [1, 1, 1], Mean: 1, Sqrt: 1
        assert calculate_rmse(preds, actuals) == 1.0

    def test_rmse_mismatched_lengths(self):
        preds = np.array([1.0, 2.0])
        actuals = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            calculate_rmse(preds, actuals)

    def test_rmse_empty_arrays(self):
        preds = np.array([])
        actuals = np.array([])
        assert np.isnan(calculate_rmse(preds, actuals))


class TestMAE:
    def test_mae_perfect_prediction(self):
        preds = np.array([1.0, 2.0, 3.0])
        actuals = np.array([1.0, 2.0, 3.0])
        assert calculate_mae(preds, actuals) == 0.0

    def test_mae_constant_error(self):
        preds = np.array([1.0, 2.0, 3.0])
        actuals = np.array([2.0, 3.0, 4.0])
        # Errors: [-1, -1, -1], Abs: [1, 1, 1], Mean: 1
        assert calculate_mae(preds, actuals) == 1.0

    def test_mae_mismatched_lengths(self):
        preds = np.array([1.0, 2.0])
        actuals = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            calculate_mae(preds, actuals)

    def test_mae_empty_arrays(self):
        preds = np.array([])
        actuals = np.array([])
        assert np.isnan(calculate_mae(preds, actuals))


class TestEvaluateFrequentistForecasts:
    def setup_method(self):
        # Create temporary directory and files for testing
        self.temp_dir = tempfile.mkdtemp()
        self.forecasts_path = os.path.join(self.temp_dir, "forecasts.csv")
        self.outcomes_path = os.path.join(self.temp_dir, "outcomes.csv")
        self.metrics_path = os.path.join(self.temp_dir, "metrics.csv")

        # Create mock forecasts
        forecasts_data = {
            'race_id': ['A', 'B', 'C'],
            'simple_avg_forecast': [45.0, 50.0, 55.0],
            'weighted_avg_forecast': [46.0, 51.0, 54.0]
        }
        pd.DataFrame(forecasts_data).to_csv(self.forecasts_path, index=False)

        # Create mock outcomes
        outcomes_data = {
            'race_id': ['A', 'B', 'C'],
            'actual_winner_share': [45.0, 52.0, 53.0]
        }
        pd.DataFrame(outcomes_data).to_csv(self.outcomes_path, index=False)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_evaluate_returns_correct_structure(self):
        metrics = evaluate_frequentist_forecasts(
            self.forecasts_path,
            self.outcomes_path,
            self.metrics_path
        )
        assert "simple_avg" in metrics
        assert "weighted_avg" in metrics
        assert "rmse" in metrics["simple_avg"]
        assert "mae" in metrics["simple_avg"]
        assert "rmse" in metrics["weighted_avg"]
        assert "mae" in metrics["weighted_avg"]

    def test_evaluate_calculates_correct_metrics(self):
        # Simple: |45-45|=0, |50-52|=2, |55-53|=2 -> MAE = 4/3 = 1.333
        # Simple: (0^2 + 2^2 + 2^2)/3 = 8/3 -> RMSE = sqrt(8/3) = 1.633
        # Weighted: |46-45|=1, |51-52|=1, |54-53|=1 -> MAE = 1
        # Weighted: (1^2 + 1^2 + 1^2)/3 = 1 -> RMSE = 1

        metrics = evaluate_frequentist_forecasts(
            self.forecasts_path,
            self.outcomes_path,
            self.metrics_path
        )

        simple_mae = metrics["simple_avg"]["mae"]
        simple_rmse = metrics["simple_avg"]["rmse"]
        weighted_mae = metrics["weighted_avg"]["mae"]
        weighted_rmse = metrics["weighted_avg"]["rmse"]

        assert np.isclose(simple_mae, 4/3, atol=1e-4)
        assert np.isclose(simple_rmse, np.sqrt(8/3), atol=1e-4)
        assert np.isclose(weighted_mae, 1.0, atol=1e-4)
        assert np.isclose(weighted_rmse, 1.0, atol=1e-4)

    def test_evaluate_saves_output_file(self):
        evaluate_frequentist_forecasts(
            self.forecasts_path,
            self.outcomes_path,
            self.metrics_path
        )
        assert os.path.exists(self.metrics_path)
        df = pd.read_csv(self.metrics_path)
        assert len(df) == 2
        assert set(df['method']) == {'simple_avg', 'weighted_avg'}

    def test_evaluate_missing_forecast_columns(self):
        bad_forecasts = os.path.join(self.temp_dir, "bad_forecasts.csv")
        pd.DataFrame({'race_id': ['A'], 'other_col': [1]}).to_csv(bad_forecasts, index=False)

        with pytest.raises(ValueError, match="Forecasts CSV must contain"):
            evaluate_frequentist_forecasts(
                bad_forecasts,
                self.outcomes_path,
                self.metrics_path
            )

    def test_evaluate_missing_merge_key(self):
        bad_outcomes = os.path.join(self.temp_dir, "bad_outcomes.csv")
        pd.DataFrame({'wrong_id': ['A'], 'actual_winner_share': [45]}).to_csv(bad_outcomes, index=False)

        with pytest.raises(ValueError, match="Could not find a common key"):
            evaluate_frequentist_forecasts(
                self.forecasts_path,
                bad_outcomes,
                self.metrics_path
            )