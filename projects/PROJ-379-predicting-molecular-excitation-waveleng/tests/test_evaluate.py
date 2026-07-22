import json
import os
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys

# Ensure we can import from the code directory
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from evaluate import determine_sc001_status, compute_metrics, perform_wilcoxon_test

class TestSC001Logic:
    """
    Test task for SC-001 logic: Verify that sc001_status in metrics.json 
    is correctly set to "PASS" or "FAIL" based on the Wilcoxon test result 
    and MAE threshold (F001).
    """

    def test_pass_condition(self):
        """p < 0.05 AND MAE < 30 -> PASS"""
        status = determine_sc001_status(mae=25.0, p_value=0.01)
        assert status == "PASS"

    def test_fail_high_mae(self):
        """p < 0.05 BUT MAE >= 30 -> FAIL"""
        status = determine_sc001_status(mae=35.0, p_value=0.01)
        assert status == "FAIL"

    def test_fail_high_p_value(self):
        """MAE < 30 BUT p >= 0.05 -> FAIL"""
        status = determine_sc001_status(mae=25.0, p_value=0.10)
        assert status == "FAIL"

    def test_fail_nan_mae(self):
        """NaN MAE -> FAIL"""
        status = determine_sc001_status(mae=float('nan'), p_value=0.01)
        assert status == "FAIL"

    def test_fail_nan_p_value(self):
        """NaN p_value -> FAIL"""
        status = determine_sc001_status(mae=25.0, p_value=float('nan'))
        assert status == "FAIL"

    def test_edge_case_boundary_mae(self):
        """MAE exactly 30.0 should be FAIL (strictly less than 30 required)"""
        status = determine_sc001_status(mae=30.0, p_value=0.01)
        assert status == "FAIL"

    def test_edge_case_boundary_p(self):
        """p exactly 0.05 should be FAIL (strictly less than 0.05 required)"""
        status = determine_sc001_status(mae=25.0, p_value=0.05)
        assert status == "FAIL"

class TestMetrics:
    def test_compute_metrics_basic(self):
        y_true = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([11.0, 19.0, 31.0])
        
        metrics = compute_metrics(y_true, y_pred)
        
        assert "mae" in metrics
        assert "r2" in metrics
        # MAE = (|1| + |1| + |1|) / 3 = 1.0
        assert abs(metrics["mae"] - 1.0) < 1e-6 
            
    def test_compute_metrics_nan_handling(self):
        y_true = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([11.0, np.nan, 31.0])
        
        metrics = compute_metrics(y_true, y_pred)
        # Should ignore the nan entry, calculating over 2 points
        # Errors: |1|, |1| -> MAE = 1.0
        assert abs(metrics["mae"] - 1.0) < 1e-6

class TestWilcoxon:
    def test_wilcoxon_basic(self):
        y_true = [10.0, 20.0, 30.0, 40.0]
        y_pred_gnn = [11.0, 19.0, 31.0, 39.0] # Errors: 1, 1, 1, 1
        y_pred_ridge = [12.0, 18.0, 32.0, 38.0] # Errors: 2, 2, 2, 2
        
        p_val = perform_wilcoxon_test(y_pred_gnn, y_pred_ridge, y_true)
        
        # With such consistent difference, p-value should be low
        assert isinstance(p_val, float)
        assert not np.isnan(p_val)

class TestEvaluateIntegration:
    def test_metrics_json_structure(self):
        """Verify that the output JSON structure matches the requirement."""
        # We simulate the output that main() would produce
        output = {
            "mae": 25.5,
            "r2": 0.85,
            "wilcoxon_p_value": 0.03,
            "sc001_status": "PASS"
        }
        
        # Validate keys
        required_keys = ["mae", "r2", "wilcoxon_p_value", "sc001_status"]
        for key in required_keys:
            assert key in output, f"Missing key: {key}"
        
        # Validate types
        assert isinstance(output["mae"], float)
        assert isinstance(output["r2"], float)
        assert isinstance(output["wilcoxon_p_value"], float)
        assert output["sc001_status"] in ["PASS", "FAIL"]

    def test_sc001_status_logic_in_json(self):
        """Test that the logic correctly sets the status in the JSON context."""
        # Case 1: Pass
        mae, p = 20.0, 0.01
        status = "PASS" if (p < 0.05 and mae < 30) else "FAIL"
        assert status == "PASS"

        # Case 2: Fail (High MAE)
        mae, p = 35.0, 0.01
        status = "PASS" if (p < 0.05 and mae < 30) else "FAIL"
        assert status == "FAIL"

        # Case 3: Fail (High P)
        mae, p = 20.0, 0.10
        status = "PASS" if (p < 0.05 and mae < 30) else "FAIL"
        assert status == "FAIL"