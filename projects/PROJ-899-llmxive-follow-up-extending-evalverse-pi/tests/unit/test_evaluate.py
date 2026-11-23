import os
import sys
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path if not already
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.evaluate import (
    _create_mean_predictor,
    _create_shuffled_predictor,
    calculate_metrics,
    evaluate_baselines
)
from src.utils import write_csv

class TestBaselinePredictors:
    def test_mean_predictor_returns_constant(self):
        y_true = pd.Series([10.0, 20.0, 30.0, 40.0])
        y_pred = _create_mean_predictor(y_true)
        
        expected_mean = 25.0
        assert all(y_pred == expected_mean)
        assert len(y_pred) == len(y_true)

    def test_shuffled_predictor_permutes_values(self):
        y_true = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = _create_shuffled_predictor(y_true, random_state=42)
        
        # Values must be a permutation of original
        assert sorted(y_pred.values) == sorted(y_true.values)
        # And length must match
        assert len(y_pred) == len(y_true)

class TestMetrics:
    def test_calculate_metrics_perfect(self):
        y_true = pd.Series([1.0, 2.0, 3.0])
        y_pred = pd.Series([1.0, 2.0, 3.0])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        assert metrics["mse"] == 0.0
        assert metrics["mae"] == 0.0
        assert metrics["r2"] == 1.0

    def test_calculate_metrics_mean_baseline(self):
        y_true = pd.Series([0.0, 0.0, 0.0, 10.0])
        y_pred = pd.Series([2.5, 2.5, 2.5, 2.5]) # Mean is 2.5
        
        metrics = calculate_metrics(y_true, y_pred)
        
        # MSE = ((2.5)^2 + (2.5)^2 + (2.5)^2 + (7.5)^2) / 4
        # = (6.25 + 6.25 + 6.25 + 56.25) / 4 = 75 / 4 = 18.75
        assert abs(metrics["mse"] - 18.75) < 1e-6
        
        # R2 should be < 1.0
        assert metrics["r2"] < 1.0

class TestEvaluateBaselines:
    @patch('src.models.evaluate._load_predictions_and_targets')
    @patch('src.models.evaluate.get_data_root')
    @patch('src.models.evaluate.write_csv')
    def test_evaluate_baselines_creates_file(self, mock_write_csv, mock_get_root, mock_load):
        # Mock data
        y_true = pd.Series([10.0, 20.0, 30.0])
        X_dummy = pd.DataFrame({"f1": [1, 2, 3]})
        mock_load.return_value = (X_dummy, y_true)
        mock_get_root.return_value = "/fake/data/root"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_baseline.csv")
            
            # Run
            df = evaluate_baselines(output_path=output_path)
            
            # Assertions
            assert isinstance(df, pd.DataFrame)
            assert "model_type" in df.columns
            assert len(df) == 2 # Mean and Shuffled
            assert "Mean Predictor" in df["model_type"].values
            assert "Shuffled Features" in df["model_type"].values
            
            # Check that write_csv was called (or to_csv on df if implemented that way)
            # In our implementation, we use df.to_csv directly, so we verify the file exists
            assert os.path.exists(output_path)
            
            # Verify content
            saved_df = pd.read_csv(output_path)
            assert len(saved_df) == 2
            assert "mse" in saved_df.columns
            assert "mae" in saved_df.columns
            assert "r2" in saved_df.columns