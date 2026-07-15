"""
Unit tests for code/analysis/threshold_finder.py
"""
import os
import sys
import json
import tempfile
import shutil
import csv
import pytest
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from code.analysis.threshold_finder import (
    wilson_score_interval,
    calculate_confidence_intervals,
    load_error_rates,
    find_type_i_threshold,
    find_power_threshold,
    save_thresholds
)


class TestWilsonScoreInterval:
    def test_wilson_normal_case(self):
        # 95 successes out of 100, z=1.96
        lower, upper = wilson_score_interval(95, 100)
        assert 0.88 < lower < 0.92
        assert 0.97 < upper < 0.99

    def test_wilson_low_proportion(self):
        # 5 successes out of 100
        lower, upper = wilson_score_interval(5, 100)
        assert 0.02 < lower < 0.05
        assert 0.10 < upper < 0.15

    def test_wilson_zero_successes(self):
        lower, upper = wilson_score_interval(0, 100)
        assert lower == 0.0
        assert 0.0 < upper < 0.05

    def test_wilson_all_successes(self):
        lower, upper = wilson_score_interval(100, 100)
        assert 0.96 < lower < 0.99
        assert upper == 1.0

    def test_wilson_small_n(self):
        # 1 success out of 2
        lower, upper = wilson_score_interval(1, 2)
        # With small n, interval should be wide
        assert lower < 0.3
        assert upper > 0.7


class TestCalculateConfidenceIntervals:
    def test_adds_ci_to_records(self):
        records = [
            {"test_type": "t-test", "effect_size": 0.0, "sample_size": 10, "error_rate": 0.05, "num_rejections": 500, "total_iterations": 10000}
        ]
        result = calculate_confidence_intervals(records)
        assert len(result) == 1
        assert "ci_lower" in result[0]
        assert "ci_upper" in result[0]
        assert result[0]["ci_lower"] <= result[0]["error_rate"] <= result[0]["ci_upper"]


class TestLoadErrorRates:
    def test_loads_from_csv(self, tmp_path):
        # Create a temporary error_rates_summary.csv
        csv_path = os.path.join(tmp_path, "error_rates_summary.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["test_type", "effect_size", "sample_size", "error_rate", "num_rejections", "total_iterations"])
            writer.writerow(["t-test", "0.0", "10", "0.05", "500", "10000"])
            writer.writerow(["t-test", "0.5", "50", "0.80", "8000", "10000"])
        
        # Temporarily override the module constant
        import code.analysis.threshold_finder as tf_module
        original_path = tf_module.ERROR_RATES_CSV_PATH
        tf_module.ERROR_RATES_CSV_PATH = csv_path
        
        try:
            data = load_error_rates()
            assert len(data) == 2
            assert data[0]["test_type"] == "t-test"
            assert data[0]["sample_size"] == 10
        finally:
            tf_module.ERROR_RATES_CSV_PATH = original_path


class TestFindTypeIThreshold:
    def test_finds_threshold_when_ci_exceeds_alpha(self):
        # Create data where CI lower bound exceeds 0.05 at n=50
        records = [
            {"test_type": "t-test", "effect_size": 0.0, "sample_size": 10, "error_rate": 0.04, "ci_lower": 0.03, "ci_upper": 0.05, "total_iterations": 10000},
            {"test_type": "t-test", "effect_size": 0.0, "sample_size": 20, "error_rate": 0.045, "ci_lower": 0.04, "ci_upper": 0.05, "total_iterations": 10000},
            {"test_type": "t-test", "effect_size": 0.0, "sample_size": 50, "error_rate": 0.06, "ci_lower": 0.055, "ci_upper": 0.065, "total_iterations": 10000},
        ]
        result = find_type_i_threshold(records, alpha=0.05)
        assert result["threshold_sample_size"] == 50
        assert result["test_type"] == "t-test"

    def test_returns_none_if_no_threshold(self):
        records = [
            {"test_type": "t-test", "effect_size": 0.0, "sample_size": 10, "error_rate": 0.04, "ci_lower": 0.03, "ci_upper": 0.05, "total_iterations": 10000},
        ]
        result = find_type_i_threshold(records, alpha=0.05)
        assert result["threshold_sample_size"] is None


class TestFindPowerThreshold:
    def test_finds_threshold_where_power_exceeds_target(self):
        # Create data where power lower CI >= 0.80 for 3 consecutive points starting at n=100
        records = [
            {"test_type": "t-test", "effect_size": 0.5, "sample_size": 50, "ci_lower": 0.70, "ci_upper": 0.85},
            {"test_type": "t-test", "effect_size": 0.5, "sample_size": 80, "ci_lower": 0.75, "ci_upper": 0.90},
            {"test_type": "t-test", "effect_size": 0.5, "sample_size": 100, "ci_lower": 0.80, "ci_upper": 0.92},
            {"test_type": "t-test", "effect_size": 0.5, "sample_size": 120, "ci_lower": 0.82, "ci_upper": 0.94},
            {"test_type": "t-test", "effect_size": 0.5, "sample_size": 140, "ci_lower": 0.85, "ci_upper": 0.96},
        ]
        result = find_power_threshold(records, power_target=0.80, consecutive=3)
        # Should find n=100 as the start of 3 consecutive (100, 120, 140)
        assert result["threshold_sample_size"] == 100

    def test_returns_none_if_no_threshold(self):
        records = [
            {"test_type": "t-test", "effect_size": 0.5, "sample_size": 50, "ci_lower": 0.50, "ci_upper": 0.60},
            {"test_type": "t-test", "effect_size": 0.5, "sample_size": 80, "ci_lower": 0.60, "ci_upper": 0.70},
        ]
        result = find_power_threshold(records, power_target=0.80, consecutive=3)
        assert result["threshold_sample_size"] is None


class TestSaveThresholds:
    def test_saves_to_json(self, tmp_path):
        thresholds = [
            {"test_type": "t-test", "threshold_sample_size": 50, "condition": "Type I error"}
        ]
        output_path = os.path.join(tmp_path, "thresholds.json")
        
        # Temporarily override the module constant
        import code.analysis.threshold_finder as tf_module
        original_dir = tf_module.DATA_SIMULATION_DIR
        original_path = tf_module.THRESHOLDS_OUTPUT_PATH
        tf_module.DATA_SIMULATION_DIR = tmp_path
        tf_module.THRESHOLDS_OUTPUT_PATH = output_path
        
        try:
            result_path = save_thresholds(thresholds)
            assert os.path.exists(result_path)
            with open(result_path, "r") as f:
                data = json.load(f)
            assert len(data) == 1
            assert data[0]["test_type"] == "t-test"
        finally:
            tf_module.DATA_SIMULATION_DIR = original_dir
            tf_module.THRESHOLDS_OUTPUT_PATH = original_path