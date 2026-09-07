"""
Unit Tests for Sensitivity Analysis (T031)

Tests the FNR calculation logic and the sweep functionality with mock data.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
import json
from pathlib import Path

# Import the functions from the script
# We need to import the specific functions, not just main
import sys
import os
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.sensitivity_analysis import calculate_fnr, run_sensitivity_analysis

class TestFNR:
    def test_fnr_basic(self):
        # y_true: [1, 1, 1, 0, 0] -> 3 positives
        # y_pred: [0, 0, 1, 0, 0] -> FN=2, TP=1
        y_true = np.array([1, 1, 1, 0, 0])
        y_pred = np.array([0, 0, 1, 0, 0])
        
        fnr = calculate_fnr(y_true, y_pred)
        # FN = 2, Total Pos = 3 -> 2/3
        assert abs(fnr - 2/3) < 1e-6

    def test_fnr_zero_fn(self):
        y_true = np.array([1, 1, 0])
        y_pred = np.array([1, 1, 0])
        fnr = calculate_fnr(y_true, y_pred)
        assert fnr == 0.0

    def test_fnr_no_positives(self):
        y_true = np.array([0, 0, 0])
        y_pred = np.array([0, 0, 0])
        fnr = calculate_fnr(y_true, y_pred)
        assert fnr == 0.0

    def test_fnr_all_missed(self):
        y_true = np.array([1, 1, 1])
        y_pred = np.array([0, 0, 0])
        fnr = calculate_fnr(y_true, y_pred)
        assert fnr == 1.0

class TestSensitivityAnalysis:
    @pytest.fixture
    def mock_model(self):
        model = MagicMock()
        # Mock predict_proba to return specific probabilities
        # We will control the output to test thresholding
        model.predict_proba = MagicMock()
        return model

    def test_run_sweep_logic(self, mock_model):
        # Create mock features
        data = {
            'task_id': ['t1', 't2', 't3', 't4'],
            'dynamic_execution_outcome': ['Fail', 'Fail', 'Pass', 'Fail'], # 3 Positives
            'metric_a': [0.1, 0.2, 0.3, 0.4]
        }
        df = pd.DataFrame(data)
        
        # Mock model output probabilities
        # We want to test threshold 0.05
        # If probs are [0.02, 0.06, 0.08, 0.01]
        # Threshold 0.05:
        # t1 (0.02) -> 0 (FN)
        # t2 (0.06) -> 1 (TP)
        # t3 (0.08) -> 1 (FP - but outcome is Pass, so 0, so FP)
        # t4 (0.01) -> 0 (FN)
        # Positives: t1, t2, t4.
        # FN: t1, t4 (2)
        # FNR = 2/3
        
        probs = np.array([
            [0.98, 0.02], # t1: 0.02 prob of positive
            [0.94, 0.06], # t2: 0.06
            [0.92, 0.08], # t3: 0.08
            [0.99, 0.01]  # t4: 0.01
        ])
        mock_model.predict_proba.return_value = probs

        thresholds = [0.05]
        model_data = {}
        
        result = run_sensitivity_analysis(mock_model, df, model_data, thresholds)
        
        assert len(result['results']) == 1
        assert result['results'][0]['threshold'] == 0.05
        # Expected FNR: 2/3 = 0.666...
        assert abs(result['results'][0]['fnr'] - (2/3)) < 1e-4

    def test_safety_flag_logic(self, mock_model):
        # Create data where FNR > 0.1%
        # 100 positives, all predicted 0 -> FNR 1.0
        n_pos = 100
        y_true_list = [1] * n_pos
        y_pred_list = [0] * n_pos
        
        # Create a mock dataframe
        data = {
            'task_id': [f't{i}' for i in range(n_pos)],
            'dynamic_execution_outcome': ['Fail'] * n_pos,
            'metric_a': [0.5] * n_pos
        }
        df = pd.DataFrame(data)
        
        # Mock probs all < 0.01
        probs = np.array([[0.99, 0.005]] * n_pos)
        mock_model.predict_proba.return_value = probs

        result = run_sensitivity_analysis(mock_model, df, {}, [0.01])
        
        assert result['is_safe'] == False
        assert result['safety_status'] == 'UNSAFE'
        assert result['results'][0]['fnr'] == 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])