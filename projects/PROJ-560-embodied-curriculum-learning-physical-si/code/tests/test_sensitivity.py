import pytest
import numpy as np
import os
import sys
import json
import tempfile
from src.sensitivity import run_sensitivity_sweep, check_robustness_warning, aggregate_results_for_report
from src.models import SensitivitySweep

class TestSensitivitySweepLogic:
    """Unit tests for sensitivity sweep logic."""

    def test_robustness_warning_detection(self):
        """Test that check_robustness_warning flags when effect size drops."""
        # Normal effect sizes
        normal_sizes = [0.5, 0.6, 0.7]
        assert check_robustness_warning(normal_sizes, meaningful_threshold=0.2) is False

        # Small effect size that triggers warning
        small_sizes = [0.5, 0.1, 0.7]
        assert check_robustness_warning(small_sizes, meaningful_threshold=0.2) is True

        # Empty list
        assert check_robustness_warning([], meaningful_threshold=0.2) is True

    def test_aggregate_results_for_report_insufficient_data(self):
        """Test aggregation when data is insufficient."""
        sweep_data = {
            "insufficient_data": True,
            "message": "Insufficient data for robustness check: N=20 < 30.",
            "n_observed": 20,
            "sweep_results": []
        }
        
        report = aggregate_results_for_report(sweep_data)
        
        assert report["robustness_check"]["status"] == "skipped"
        assert "insufficient data" in report["robustness_check"]["reason"].lower()
        assert report["robustness_check"]["n_observed"] == 20

    def test_aggregate_results_for_report_completed(self):
        """Test aggregation when sweep completes successfully."""
        sweep_data = {
            "insufficient_data": False,
            "n_observed": 50,
            "sweep_results": [
                SensitivitySweep(threshold_value=0.01, t_statistic=2.5, p_value=0.01, effect_size=0.5, n_a=25, n_b=25),
                SensitivitySweep(threshold_value=0.05, t_statistic=2.6, p_value=0.01, effect_size=0.5, n_a=25, n_b=25)
            ]
        }
        
        report = aggregate_results_for_report(sweep_data)
        
        assert report["robustness_check"]["status"] == "completed"
        assert report["robustness_check"]["n_observed"] == 50
        assert "sweep_details" in report["robustness_check"]
        assert len(report["robustness_check"]["sweep_details"]) == 2

    def test_run_sensitivity_sweep_with_real_data_simulation(self):
        """
        Simulate a run with enough data to ensure the t-test logic works 
        and the sweep produces results.
        """
        # Generate synthetic data that mimics real data structure
        np.random.seed(42)
        n = 100
        data = []
        
        # Group A: Embodied (Mean gain = 5, Std = 2)
        for i in range(n // 2):
            data.append({
                "instruction_type": "embodied",
                "gain_score": np.random.normal(5, 2)
            })
        
        # Group B: Static (Mean gain = 3, Std = 2)
        for i in range(n - n // 2):
            data.append({
                "instruction_type": "static",
                "gain_score": np.random.normal(3, 2)
            })
        
        result = run_sensitivity_sweep(
            data=data,
            instruction_column="instruction_type",
            outcome_column="gain_score",
            thresholds=[0.01, 0.05, 0.10]
        )
        
        assert result["insufficient_data"] is False
        assert len(result["sweep_results"]) == 3
        
        # Verify effect sizes are positive (Embodied > Static)
        for sweep in result["sweep_results"]:
            assert sweep.effect_size > 0
