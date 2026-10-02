import pytest
import numpy as np
import os
import sys
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from sensitivity import run_sensitivity_sweep, check_robustness_warning, aggregate_results_for_report
import pandas as pd

class TestRobustnessWarning:
    """Test the robustness warning logic for effect sizes below 0.2."""

    def test_robustness_warning_false_all_above_threshold(self):
        """Test that warning is False when all effect sizes are >= 0.2."""
        sweep_results = [
            {"effect_size_cohen_d": 0.5, "robustness_flag": True},
            {"effect_size_cohen_d": 0.3, "robustness_flag": True},
            {"effect_size_cohen_d": 0.2, "robustness_flag": True}
        ]
        assert check_robustness_warning(sweep_results) is False

    def test_robustness_warning_true_one_below_threshold(self):
        """Test that warning is True when at least one effect size is < 0.2."""
        sweep_results = [
            {"effect_size_cohen_d": 0.5, "robustness_flag": True},
            {"effect_size_cohen_d": 0.15, "robustness_flag": False},
            {"effect_size_cohen_d": 0.3, "robustness_flag": True}
        ]
        assert check_robustness_warning(sweep_results) is True

    def test_robustness_warning_true_all_below_threshold(self):
        """Test that warning is True when all effect sizes are < 0.2."""
        sweep_results = [
            {"effect_size_cohen_d": 0.1, "robustness_flag": False},
            {"effect_size_cohen_d": 0.05, "robustness_flag": False},
            {"effect_size_cohen_d": 0.18, "robustness_flag": False}
        ]
        assert check_robustness_warning(sweep_results) is True

    def test_robustness_warning_empty_list(self):
        """Test that warning is False for empty list."""
        assert check_robustness_warning([]) is False

    def test_robustness_warning_insufficient_data(self):
        """Test that warning is False when data is insufficient."""
        sweep_results = [
            {
                "effect_size_cohen_d": 0.0,
                "robustness_flag": False,
                "insufficient_data": True,
                "message": "insufficient data for robustness check"
            }
        ]
        assert check_robustness_warning(sweep_results) is False

class TestSensitivitySweepLogic:
    """Test the sensitivity sweep logic."""

    def test_sweep_returns_correct_structure(self):
        """Test that sweep returns expected structure."""
        # Create mock data
        np.random.seed(42)
        n = 100
        gain_scores = np.random.normal(0, 1, n)
        groups = np.random.choice(['A', 'B'], n)
        
        df = pd.DataFrame({
            'gain_score': gain_scores,
            'group': groups
        })
        
        thresholds = [0.05, 0.10]
        results = run_sensitivity_sweep(df, thresholds)
        
        assert len(results) == len(thresholds)
        for item in results:
            assert "threshold_value" in item
            assert "n_participants_retained" in item
            assert "effect_size_cohen_d" in item
            assert "robustness_flag" in item

    def test_sweep_insufficient_data(self):
        """Test sweep behavior with N < 30."""
        df = pd.DataFrame({
            'gain_score': np.random.normal(0, 1, 20),
            'group': np.random.choice(['A', 'B'], 20)
        })
        
        results = run_sensitivity_sweep(df)
        
        assert len(results) == 1
        assert results[0]["insufficient_data"] is True
        assert results[0]["message"] == "insufficient data for robustness check"

    def test_aggregate_results_for_report(self):
        """Test merging analysis and sweep results."""
        analysis_result = {
            "t_statistic": 2.5,
            "p_value": 0.01
        }
        sweep_results = [
            {"effect_size_cohen_d": 0.5, "robustness_flag": True}
        ]
        
        report = aggregate_results_for_report(analysis_result, sweep_results)
        
        assert report["t_statistic"] == 2.5
        assert "sensitivity_analysis" in report
        assert report["robustness_warning"] is False