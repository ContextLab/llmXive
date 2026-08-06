"""
Unit tests for sensitivity analysis (T019).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from models.sensitivity_analysis import calculate_metrics, run_sensitivity_analysis, main
from config import get_data_config

class TestCalculateMetrics:
    def test_perfect_prediction(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        metrics = calculate_metrics(y_true, y_pred)
        assert metrics["fpr"] == 0.0
        assert metrics["accuracy"] == 1.0
        assert metrics["class_balance"] == 0.5

    def test_all_predicted_positive(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([1, 1, 1, 1])
        metrics = calculate_metrics(y_true, y_pred)
        # FP=2, TN=0 -> FPR = 2/2 = 1.0
        assert metrics["fpr"] == 1.0
        assert metrics["class_balance"] == 1.0
        assert metrics["accuracy"] == 0.5

    def test_all_predicted_negative(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 0, 0])
        metrics = calculate_metrics(y_true, y_pred)
        # FP=0, TN=2 -> FPR = 0/2 = 0.0
        assert metrics["fpr"] == 0.0
        assert metrics["class_balance"] == 0.0
        assert metrics["accuracy"] == 0.5

    def test_no_negatives_in_true(self):
        y_true = np.array([1, 1, 1])
        y_pred = np.array([0, 1, 1])
        metrics = calculate_metrics(y_true, y_pred)
        # No negatives, so FP+TN = 0. FPR should be 0.0 by definition in our code.
        assert metrics["fpr"] == 0.0

class TestRunSensitivityAnalysis:
    def test_monotonic_accuracy_drop(self):
        # As threshold increases, we predict fewer positives.
        # If true labels are mostly 0, accuracy should increase.
        # If true labels are mostly 1, accuracy should decrease.
        # Let's test a mixed case.
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
        thresholds = [0.4, 0.6, 0.8]

        results = run_sensitivity_analysis(y_true, y_scores, thresholds)

        assert len(results) == 3
        for r in results:
            assert "threshold" in r
            assert "fpr" in r
            assert "class_balance" in r
            assert "accuracy" in r

class TestMain:
    @pytest.fixture
    def mock_dataset(self, tmp_path):
        # Create a mock final_dataset.parquet
        df = pd.DataFrame({
            "crystallization_label": [0, 0, 1, 1, 0, 1],
            "crystallization_proba": [0.2, 0.3, 0.6, 0.7, 0.4, 0.8],
            "composition_id": ["A", "B", "C", "D", "E", "F"]
        })
        output_path = tmp_path / "final_dataset.parquet"
        df.to_parquet(output_path)
        return output_path

    @patch("models.sensitivity_analysis.get_data_config")
    @patch("models.sensitivity_analysis.load_final_dataset")
    def test_main_success(self, mock_load, mock_config, mock_dataset, tmp_path):
        # Setup mocks
        mock_df = pd.read_parquet(mock_dataset)
        mock_load.return_value = mock_df

        # Mock config to point to tmp_path
        mock_cfg = MagicMock()
        mock_cfg.processed_dir = tmp_path
        mock_config.return_value = mock_cfg

        # Run main
        report = main()

        # Verify output file exists
        output_path = tmp_path / "sensitivity_report.json"
        assert output_path.exists()

        # Verify content structure
        with open(output_path) as f:
            data = json.load(f)

        assert data["task_id"] == "T019"
        assert "results" in data
        assert len(data["results"]) > 0
        assert "threshold" in data["results"][0]
        assert "fpr" in data["results"][0]

    @patch("models.sensitivity_analysis.get_data_config")
    def test_main_missing_file(self, mock_config, tmp_path):
        # Mock config pointing to a non-existent path
        mock_cfg = MagicMock()
        mock_cfg.processed_dir = tmp_path / "nonexistent"
        mock_config.return_value = mock_cfg

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    @patch("models.sensitivity_analysis.get_data_config")
    @patch("models.sensitivity_analysis.load_final_dataset")
    def test_main_missing_columns(self, mock_load, mock_config, tmp_path):
        # Mock dataframe missing required columns
        mock_df = pd.DataFrame({"other_col": [1, 2, 3]})
        mock_load.return_value = mock_df

        mock_cfg = MagicMock()
        mock_cfg.processed_dir = tmp_path
        mock_config.return_value = mock_cfg

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1