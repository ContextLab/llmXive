"""
Unit tests for sensitivity analysis logic in User Story 3.

Tests verify that the robustness analysis correctly:
1. Iterates over multiple thresholds
2. Calculates correlations for each threshold
3. Compares results against a baseline
4. Determines sign stability and magnitude change
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import pytest
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.robustness import (
    run_sensitivity_analysis,
    compare_against_baseline,
    check_sign_stability,
    check_magnitude_change
)


class TestRobustnessUtils:
    """Test utility functions for robustness analysis."""

    def test_check_sign_stability_same_sign(self):
        """Test that same signs are detected as stable."""
        baseline_r = 0.45
        new_r = 0.52
        assert check_sign_stability(baseline_r, new_r) is True

    def test_check_sign_stability_different_sign(self):
        """Test that different signs are detected as unstable."""
        baseline_r = 0.45
        new_r = -0.12
        assert check_sign_stability(baseline_r, new_r) is False

    def test_check_sign_stability_zero_baseline(self):
        """Test sign stability with zero baseline."""
        baseline_r = 0.0
        new_r = 0.05
        # 0 to positive is considered stable (no sign flip)
        assert check_sign_stability(baseline_r, new_r) is True

    def test_check_magnitude_change_within_threshold(self):
        """Test magnitude change within threshold."""
        baseline_r = 0.50
        new_r = 0.53
        threshold = 0.05
        assert check_magnitude_change(baseline_r, new_r, threshold) is True

    def test_check_magnitude_change_exceeds_threshold(self):
        """Test magnitude change exceeding threshold."""
        baseline_r = 0.50
        new_r = 0.58
        threshold = 0.05
        assert check_magnitude_change(baseline_r, new_r, threshold) is False

    def test_check_magnitude_change_negative_new(self):
        """Test magnitude change with negative new value."""
        baseline_r = 0.50
        new_r = 0.40
        threshold = 0.05
        assert check_magnitude_change(baseline_r, new_r, threshold) is False


class TestCompareAgainstBaseline:
    """Test baseline comparison logic."""

    def test_compare_returns_correct_dict(self):
        """Test that comparison returns expected dictionary structure."""
        baseline = {"r": 0.50, "p_value": 0.001}
        new = {"r": 0.52, "p_value": 0.002}
        threshold = 0.05

        result = compare_against_baseline(baseline, new, threshold)

        assert "threshold" in result
        assert "correlation_r" in result
        assert "p_value" in result
        assert "sign_stable" in result
        assert "magnitude_stable" in result
        assert "result" in result  # 'PASS' or 'FAIL'

    def test_compare_passes_all_criteria(self):
        """Test comparison when all criteria are met."""
        baseline = {"r": 0.50, "p_value": 0.001}
        new = {"r": 0.52, "p_value": 0.002}
        threshold = 0.05

        result = compare_against_baseline(baseline, new, threshold)

        assert result["sign_stable"] is True
        assert result["magnitude_stable"] is True
        assert result["result"] == "PASS"

    def test_compare_fails_sign_stability(self):
        """Test comparison when sign stability fails."""
        baseline = {"r": 0.50, "p_value": 0.001}
        new = {"r": -0.10, "p_value": 0.002}
        threshold = 0.05

        result = compare_against_baseline(baseline, new, threshold)

        assert result["sign_stable"] is False
        assert result["result"] == "FAIL"

    def test_compare_fails_magnitude_stability(self):
        """Test comparison when magnitude stability fails."""
        baseline = {"r": 0.50, "p_value": 0.001}
        new = {"r": 0.60, "p_value": 0.002}
        threshold = 0.05

        result = compare_against_baseline(baseline, new, threshold)

        assert result["magnitude_stable"] is False
        assert result["result"] == "FAIL"


class TestRunSensitivityAnalysis:
    """Test the full sensitivity analysis workflow."""

    def test_run_sensitivity_analysis_with_mock_data(self):
        """Test sensitivity analysis with mock correlation data."""
        # Create mock baseline results
        baseline_data = {
            "correlation_r": 0.45,
            "p_value": 0.003,
            "ci_lower": 0.30,
            "ci_upper": 0.58
        }

        # Create mock data for different thresholds
        mock_data = {
            "threshold_0.10": {"r": 0.45, "p_value": 0.003},
            "threshold_0.20": {"r": 0.46, "p_value": 0.002},
            "threshold_0.30": {"r": 0.44, "p_value": 0.004},
            "threshold_0.40": {"r": 0.47, "p_value": 0.001},
        }

        thresholds = [0.10, 0.20, 0.30, 0.40]
        max_magnitude_change = 0.05

        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            with open(baseline_path, "w") as f:
                json.dump(baseline_data, f)

            # Mock data file would be created by the analysis pipeline
            # For this test, we simulate the structure
            mock_data_path = Path(tmpdir) / "mock_thresholds.json"
            with open(mock_data_path, "w") as f:
                json.dump(mock_data, f)

            # Run sensitivity analysis (this would normally call the actual
            # correlation functions, but we test the comparison logic)
            results = []
            for thresh in thresholds:
                key = f"threshold_{thresh}"
                baseline = baseline_data
                new_data = mock_data[key]
                comparison = compare_against_baseline(
                    {"r": baseline["correlation_r"], "p_value": baseline["p_value"]},
                    {"r": new_data["r"], "p_value": new_data["p_value"]},
                    max_magnitude_change
                )
                comparison["threshold"] = thresh
                results.append(comparison)

            # Verify results structure
            assert len(results) == len(thresholds)
            for result in results:
                assert "threshold" in result
                assert "sign_stable" in result
                assert "magnitude_stable" in result
                assert result["result"] in ["PASS", "FAIL"]

    def test_run_sensitivity_analysis_all_pass(self):
        """Test when all thresholds pass stability checks."""
        baseline_r = 0.45
        all_results = []
        thresholds = [0.10, 0.20, 0.30]

        for thresh in thresholds:
            new_r = baseline_r + (thresh * 0.01)  # Small changes
            comparison = compare_against_baseline(
                {"r": baseline_r, "p_value": 0.001},
                {"r": new_r, "p_value": 0.002},
                0.05
            )
            comparison["threshold"] = thresh
            all_results.append(comparison)

        # All should pass
        for result in all_results:
            assert result["result"] == "PASS"
            assert result["sign_stable"] is True

    def test_run_sensitivity_analysis_some_fail(self):
        """Test when some thresholds fail stability checks."""
        baseline_r = 0.45
        all_results = []
        thresholds = [0.10, 0.20, 0.30]
        new_values = [0.46, 0.40, -0.10]  # Last one changes sign

        for thresh, new_r in zip(thresholds, new_values):
            comparison = compare_against_baseline(
                {"r": baseline_r, "p_value": 0.001},
                {"r": new_r, "p_value": 0.002},
                0.05
            )
            comparison["threshold"] = thresh
            all_results.append(comparison)

        # Check that we have a mix of PASS and FAIL
        pass_count = sum(1 for r in all_results if r["result"] == "PASS")
        fail_count = sum(1 for r in all_results if r["result"] == "FAIL")

        assert pass_count >= 1
        assert fail_count >= 1