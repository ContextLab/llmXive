"""
Unit tests for src/evaluation/stats.py specifically for handling zero-variance groups.

This test suite verifies the behavior of statistical tests when one or both groups
have zero variance (all successes or all failures), ensuring the code handles these
edge cases gracefully without crashing.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.stats import (
    load_evaluation_results,
    extract_success_rates,
    perform_paired_test,
    apply_benjamini_hochberg,
    calculate_statistical_power,
    compare_strategies,
    save_statistics_report
)


class TestZeroVarianceHandling:
    """Tests for zero-variance group handling in statistical functions."""

    def test_perform_paired_test_zero_variance_group1(self):
        """Test that perform_paired_test handles zero variance in the first group."""
        # Group 1: all successes (variance = 0)
        group1 = [1.0, 1.0, 1.0, 1.0, 1.0]
        # Group 2: mixed results
        group2 = [1.0, 0.0, 1.0, 0.0, 1.0]

        # Should not raise an exception
        p_value, statistic, message = perform_paired_test(group1, group2)

        # Verify that we get a NaN p-value and appropriate message
        assert np.isnan(p_value), "P-value should be NaN for zero variance"
        assert "zero variance" in message.lower() or "skipped" in message.lower(), \
            f"Expected warning about zero variance, got: {message}"

    def test_perform_paired_test_zero_variance_group2(self):
        """Test that perform_paired_test handles zero variance in the second group."""
        # Group 1: mixed results
        group1 = [1.0, 0.0, 1.0, 0.0, 1.0]
        # Group 2: all failures (variance = 0)
        group2 = [0.0, 0.0, 0.0, 0.0, 0.0]

        # Should not raise an exception
        p_value, statistic, message = perform_paired_test(group1, group2)

        # Verify that we get a NaN p-value and appropriate message
        assert np.isnan(p_value), "P-value should be NaN for zero variance"
        assert "zero variance" in message.lower() or "skipped" in message.lower(), \
            f"Expected warning about zero variance, got: {message}"

    def test_perform_paired_test_both_groups_zero_variance_same(self):
        """Test that perform_paired_test handles both groups having zero variance (same value)."""
        # Both groups: all successes
        group1 = [1.0, 1.0, 1.0, 1.0, 1.0]
        group2 = [1.0, 1.0, 1.0, 1.0, 1.0]

        # Should not raise an exception
        p_value, statistic, message = perform_paired_test(group1, group2)

        # When both groups are identical with zero variance, the test is undefined
        assert np.isnan(p_value), "P-value should be NaN when both groups have zero variance"
        assert "zero variance" in message.lower() or "skipped" in message.lower(), \
            f"Expected warning about zero variance, got: {message}"

    def test_perform_paired_test_both_groups_zero_variance_different(self):
        """Test that perform_paired_test handles both groups having zero variance (different values)."""
        # Group 1: all successes
        group1 = [1.0, 1.0, 1.0, 1.0, 1.0]
        # Group 2: all failures
        group2 = [0.0, 0.0, 0.0, 0.0, 0.0]

        # Should not raise an exception
        p_value, statistic, message = perform_paired_test(group1, group2)

        # When both groups have zero variance but different means, the test is undefined
        assert np.isnan(p_value), "P-value should be NaN when both groups have zero variance"
        assert "zero variance" in message.lower() or "skipped" in message.lower(), \
            f"Expected warning about zero variance, got: {message}"

    def test_compare_strategies_with_zero_variance(self, tmp_path):
        """Test that compare_strategies handles zero-variance groups in the results."""
        # Create mock evaluation results with zero variance for one strategy
        results_data = {
            "task_1": {
                "baseline": [1.0, 1.0, 1.0, 1.0, 1.0],  # Zero variance
                "strategy_a": [1.0, 0.0, 1.0, 0.0, 1.0]
            },
            "task_2": {
                "baseline": [0.0, 0.0, 0.0, 0.0, 0.0],  # Zero variance
                "strategy_a": [1.0, 1.0, 0.0, 1.0, 0.0]
            }
        }

        # Write to a temporary file
        test_file = tmp_path / "test_results.json"
        with open(test_file, 'w') as f:
            json.dump(results_data, f)

        # Should not raise an exception
        stats_report = compare_strategies(str(test_file), ["baseline", "strategy_a"])

        # Verify that the report contains NaN for the problematic comparison
        assert "baseline_vs_strategy_a" in stats_report["bh_corrected_p_values"]
        # The p-value should be NaN due to zero variance
        assert np.isnan(stats_report["bh_corrected_p_values"]["baseline_vs_strategy_a"])

    def test_apply_benjamini_hochberg_with_nan_values(self):
        """Test that BH correction handles NaN values gracefully."""
        # Create p-values with some NaN (from zero variance cases)
        p_values = {
            "test_1": 0.01,
            "test_2": 0.05,
            "test_3": np.nan,  # Zero variance case
            "test_4": 0.10,
            "test_5": np.nan   # Another zero variance case
        }

        # Should not raise an exception
        corrected = apply_benjamini_hochberg(p_values)

        # Verify that non-NaN values are corrected
        assert corrected["test_1"] is not None
        assert corrected["test_2"] is not None
        assert corrected["test_4"] is not None

        # Verify that NaN values remain NaN
        assert np.isnan(corrected["test_3"])
        assert np.isnan(corrected["test_5"])

    def test_extract_success_rates_with_uniform_outcomes(self):
        """Test that extract_success_rates handles uniform outcomes correctly."""
        # Create mock evaluation results with uniform outcomes
        results_data = {
            "task_1": {
                "strategy_a": [1.0, 1.0, 1.0, 1.0, 1.0],  # All successes
                "strategy_b": [0.0, 0.0, 0.0, 0.0, 0.0]   # All failures
            }
        }

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(results_data, f)
            temp_path = f.name

        try:
            # Should not raise an exception
            success_rates = extract_success_rates(temp_path, ["strategy_a", "strategy_b"])

            # Verify the rates are calculated correctly (1.0 and 0.0)
            assert success_rates["strategy_a"] == 1.0
            assert success_rates["strategy_b"] == 0.0
        finally:
            os.unlink(temp_path)

    def test_save_statistics_report_with_nan_values(self, tmp_path):
        """Test that save_statistics_report handles NaN values correctly."""
        # Create a report with NaN values (from zero variance cases)
        report_data = {
            "mean_success_rate": 0.75,
            "bh_corrected_p_values": {
                "baseline_vs_strategy_a": np.nan,
                "baseline_vs_strategy_b": 0.03
            },
            "linearity_correlation_coefficient": 0.85,
            "reconstruction_error": 0.02,
            "memory_footprint": "4.2GB",
            "sensitivity_bh_corrected_p_values": {},
            "observed_success_rate_diff": 0.15,
            "statistical_power": 0.72,
            "notes": "Zero variance detected in baseline vs strategy_a comparison"
        }

        # Should not raise an exception
        output_path = tmp_path / "stats_report.json"
        save_statistics_report(report_data, str(output_path))

        # Verify the file was created and contains the data
        assert output_path.exists()

        # Load and verify the content
        with open(output_path, 'r') as f:
            loaded = json.load(f)

        assert loaded["mean_success_rate"] == 0.75
        assert np.isnan(loaded["bh_corrected_p_values"]["baseline_vs_strategy_a"])
        assert loaded["bh_corrected_p_values"]["baseline_vs_strategy_b"] == 0.03

    def test_perform_paired_test_wilcoxon_zero_variance(self):
        """Test that Wilcoxon test also handles zero variance gracefully."""
        # This tests the fallback to Wilcoxon when t-test fails
        group1 = [1.0, 1.0, 1.0, 1.0, 1.0]
        group2 = [1.0, 0.0, 1.0, 0.0, 1.0]

        # Force Wilcoxon by setting a flag or using the function directly
        # The function should handle this internally
        p_value, statistic, message = perform_paired_test(group1, group2)

        # Should handle gracefully
        assert np.isnan(p_value)
        assert "zero variance" in message.lower() or "skipped" in message.lower()

    def test_log_warning_for_zero_variance(self, caplog):
        """Test that appropriate warnings are logged for zero variance cases."""
        import logging

        group1 = [1.0, 1.0, 1.0, 1.0, 1.0]
        group2 = [1.0, 0.0, 1.0, 0.0, 1.0]

        # Set up logging capture
        with caplog.at_level(logging.WARNING):
            p_value, statistic, message = perform_paired_test(group1, group2)

        # Verify that a warning was logged
        assert any("zero variance" in record.message.lower() for record in caplog.records), \
            "Expected a warning about zero variance to be logged"

    def test_edge_case_single_trial(self):
        """Test handling of single trial (n=1) which leads to zero variance."""
        group1 = [1.0]
        group2 = [1.0, 0.0]

        # Should not crash, but return NaN
        p_value, statistic, message = perform_paired_test(group1, group2)

        assert np.isnan(p_value)
        assert "zero variance" in message.lower() or "skipped" in message.lower()

    def test_edge_case_empty_list(self):
        """Test handling of empty lists."""
        group1 = []
        group2 = [1.0, 0.0, 1.0]

        # Should handle gracefully
        p_value, statistic, message = perform_paired_test(group1, group2)

        assert np.isnan(p_value)
        assert "empty" in message.lower() or "skipped" in message.lower()