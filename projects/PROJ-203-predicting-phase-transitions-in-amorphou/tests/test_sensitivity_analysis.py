"""
Tests for code/models/sensitivity_analysis.py
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.sensitivity_analysis import compute_metrics, load_final_dataset, run_sensitivity_analysis

class TestComputeMetrics:
    def test_metrics_at_standard_threshold(self):
        """
        If threshold == 50 (standard), then Y_pred == Y_true.
        FPR should be 0, Accuracy should be 1.0.
        """
        # Create mock dataframe
        data = {
            'Tg_exp': [300.0, 350.0, 400.0],
            'Tx_exp': [400.0, 420.0, 430.0], # Gaps: 100, 70, 30
            'chemical_family': ['A', 'B', 'C']
        }
        df = pd.DataFrame(data)
        
        # Standard threshold is 50
        # Y_true: [0, 0, 1] (Gap 100>50, 70>50, 30<=50)
        # Y_pred (thresh=50): [0, 0, 1]
        # Confusion: TN=2, FP=0, FN=0, TP=1
        
        metrics = compute_metrics(df, 50.0)
        
        assert metrics['fpr'] == 0.0
        assert metrics['accuracy'] == 1.0
        assert metrics['tp'] == 1
        assert metrics['tn'] == 2
        assert metrics['fp'] == 0
        assert metrics['fn'] == 0

    def test_metrics_at_low_threshold(self):
        """
        Threshold 25.
        Y_true (50): [0, 0, 1]
        Y_pred (25): [0, 0, 0] (Gap 30 > 25)
        TP=0, TN=2, FP=0, FN=1
        FPR = 0 / (0+2) = 0
        Accuracy = 2/3
        """
        data = {
            'Tg_exp': [300.0, 350.0, 400.0],
            'Tx_exp': [400.0, 420.0, 430.0], # Gaps: 100, 70, 30
            'chemical_family': ['A', 'B', 'C']
        }
        df = pd.DataFrame(data)
        
        metrics = compute_metrics(df, 25.0)
        
        assert metrics['fpr'] == 0.0
        assert metrics['accuracy'] == pytest.approx(2/3)
        assert metrics['fn'] == 1
        assert metrics['tp'] == 0

    def test_metrics_at_high_threshold(self):
        """
        Threshold 100.
        Y_true (50): [0, 0, 1]
        Y_pred (100): [0, 1, 1] (Gap 70 <= 100, Gap 100 <= 100)
        TP=1, TN=1, FP=1, FN=0
        FPR = 1 / (1+1) = 0.5
        Accuracy = 2/3
        """
        data = {
            'Tg_exp': [300.0, 350.0, 400.0],
            'Tx_exp': [400.0, 420.0, 430.0], # Gaps: 100, 70, 30
            'chemical_family': ['A', 'B', 'C']
        }
        df = pd.DataFrame(data)
        
        metrics = compute_metrics(df, 100.0)
        
        assert metrics['fpr'] == pytest.approx(0.5)
        assert metrics['accuracy'] == pytest.approx(2/3)
        assert metrics['fp'] == 1
        assert metrics['tn'] == 1

class TestLoadFinalDataset:
    def test_missing_file_raises_error(self):
        with patch('models.sensitivity_analysis.get_paths') as mock_paths:
            mock_paths.return_value = {"processed_dataset": "/nonexistent/path.parquet"}
            with pytest.raises(FileNotFoundError, match="FATAL"):
                load_final_dataset()

    def test_missing_columns_raises_error(self, tmp_path):
        # Create a dummy parquet with wrong columns
        df = pd.DataFrame({'A': [1], 'B': [2]})
        fake_path = tmp_path / "fake.parquet"
        df.to_parquet(fake_path)
        
        with patch('models.sensitivity_analysis.get_paths') as mock_paths:
            mock_paths.return_value = {"processed_dataset": str(fake_path)}
            with pytest.raises(ValueError, match="missing required columns"):
                load_final_dataset()

class TestRunSensitivityAnalysis:
    def test_integration_with_mock_data(self, tmp_path):
        # Setup fake data
        data = {
            'Tg_exp': [300.0, 350.0, 400.0, 450.0],
            'Tx_exp': [400.0, 420.0, 430.0, 510.0], # Gaps: 100, 70, 30, 60
            'chemical_family': ['A', 'B', 'C', 'D']
        }
        df = pd.DataFrame(data)
        fake_data_path = tmp_path / "final_dataset.parquet"
        df.to_parquet(fake_data_path)
        
        # Setup paths
        mock_paths = {
            "processed_dataset": str(fake_data_path),
            "sensitivity_report": str(tmp_path / "sensitivity_report.json")
        }
        
        with patch('models.sensitivity_analysis.get_paths', return_value=mock_paths):
            with patch('models.sensitivity_analysis.setup_pipeline_logging'):
                report = run_sensitivity_analysis()
                
        assert "results" in report
        assert len(report["results"]) == 16 # (100-25)/5 + 1 = 16
        
        # Check specific threshold results
        res_50 = next(r for r in report["results"] if r["threshold"] == 50.0)
        assert res_50["accuracy"] == 1.0
        assert res_50["fpr"] == 0.0
        
        # Check file was written
        assert os.path.exists(mock_paths["sensitivity_report"])
        with open(mock_paths["sensitivity_report"]) as f:
            saved_report = json.load(f)
        assert saved_report == report