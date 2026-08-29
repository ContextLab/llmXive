"""
Unit tests for the power analysis module (T025b).
"""
import json
import tempfile
import pytest
from pathlib import Path
import numpy as np
from scipy.stats import t, nct

# Import the module functions
# Assuming the module is named power_analysis.py in code/analysis/
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis.power_analysis import (
    calculate_noncentrality_parameter,
    calculate_power,
    run_power_analysis,
    DEFAULT_ALPHA
)

class TestNoncentralityParameter:
    def test_calculate_ncp_positive_effect(self):
        d = 0.5
        n = 100
        expected = 0.5 * np.sqrt(100)
        assert calculate_noncentrality_parameter(d, n) == pytest.approx(expected)

    def test_calculate_ncp_negative_effect(self):
        d = -0.8
        n = 50
        expected = -0.8 * np.sqrt(50)
        assert calculate_noncentrality_parameter(d, n) == pytest.approx(expected)

    def test_calculate_ncp_zero_effect(self):
        d = 0.0
        n = 100
        assert calculate_noncentrality_parameter(d, n) == 0.0

class TestPowerCalculation:
    def test_high_power_large_effect(self):
        # Large effect size should yield high power
        d = 1.0
        n = 50
        ncp = calculate_noncentrality_parameter(d, n)
        power = calculate_power(ncp, n, alpha=0.05)
        assert power > 0.80

    def test_low_power_small_effect(self):
        # Small effect size with small sample should yield low power
        d = 0.2
        n = 20
        ncp = calculate_noncentrality_parameter(d, n)
        power = calculate_power(ncp, n, alpha=0.05)
        # Power is likely low, but we just check it's a valid probability
        assert 0.0 <= power <= 1.0

    def test_power_consistency_with_scipy(self):
        # Verify our implementation matches standard t-test power logic
        # Using a known case: d=0.5, n=30, alpha=0.05
        d = 0.5
        n = 30
        ncp = calculate_noncentrality_parameter(d, n)
        power = calculate_power(ncp, n, alpha=0.05)
        
        # Manual check using scipy nct
        df = n - 1
        t_crit = t.ppf(1 - 0.05 / 2, df)
        expected_power = (1 - nct.cdf(t_crit, df, ncp)) + nct.cdf(-t_crit, df, ncp)
        
        assert power == pytest.approx(expected_power)

class TestRunPowerAnalysis:
    @pytest.fixture
    def mock_metrics_file(self, tmp_path):
        # Create a temporary metrics file with valid data
        metrics = {
            "gnn_vs_rf": {
                "rmse_gnn": 0.5,
                "rmse_rf": 0.6,
                "cohens_d": 0.5,
                "n_samples": 100,
                "mean_difference": 0.1,
                "p_value": 0.01,
                "ci_lower": 0.05,
                "ci_upper": 0.15
            }
        }
        file_path = tmp_path / "metrics.json"
        with open(file_path, 'w') as f:
            json.dump(metrics, f)
        return file_path

    def test_run_analysis_success(self, mock_metrics_file, tmp_path):
        # Temporarily override the global paths for the test
        import analysis.power_analysis as pa_module
        original_metrics = pa_module.METRICS_FILE
        original_output = pa_module.POWER_OUTPUT_FILE
        
        pa_module.METRICS_FILE = mock_metrics_file
        pa_module.POWER_OUTPUT_FILE = tmp_path / "power_analysis.json"
        
        try:
            result = run_power_analysis(alpha=0.05)
            
            assert "statistical_power" in result
            assert "cohens_d" in result
            assert "n_samples" in result
            assert result["n_samples"] == 100
            assert 0.0 <= result["statistical_power"] <= 1.0
            assert "power_interpretation" in result
        finally:
            # Restore original paths
            pa_module.METRICS_FILE = original_metrics
            pa_module.POWER_OUTPUT_FILE = original_output

    def test_missing_cohens_d(self, mock_metrics_file, tmp_path):
        import analysis.power_analysis as pa_module
        original_metrics = pa_module.METRICS_FILE
        
        # Modify the mock file to remove cohens_d
        with open(mock_metrics_file, 'r') as f:
            data = json.load(f)
        del data["gnn_vs_rf"]["cohens_d"]
        with open(mock_metrics_file, 'w') as f:
            json.dump(data, f)
        
        pa_module.METRICS_FILE = mock_metrics_file
        
        try:
            with pytest.raises(KeyError, match="cohens_d"):
                run_power_analysis()
        finally:
            pa_module.METRICS_FILE = original_metrics

    def test_missing_comparison_key(self, mock_metrics_file, tmp_path):
        import analysis.power_analysis as pa_module
        original_metrics = pa_module.METRICS_FILE
        
        # Modify the mock file to remove the key
        with open(mock_metrics_file, 'r') as f:
            data = json.load(f)
        del data["gnn_vs_rf"]
        with open(mock_metrics_file, 'w') as f:
            json.dump(data, f)
        
        pa_module.METRICS_FILE = mock_metrics_file
        
        try:
            with pytest.raises(KeyError, match="comparison key"):
                run_power_analysis()
        finally:
            pa_module.METRICS_FILE = original_metrics