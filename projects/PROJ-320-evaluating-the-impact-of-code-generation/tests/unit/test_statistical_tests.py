"""
Unit tests for statistical analysis functions in code/analysis/statistical_tests.py.

This module validates the implementation of statistical tests, including
Mann-Whitney U tests and independent t-tests, ensuring correct calculation
of p-values, statistics, and effect sizes.
"""

import pytest
import math
import numpy as np
from pathlib import Path
import sys
import json
import csv
import tempfile
import os

# Add the project root to the path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.statistical_tests import (
    load_metrics_data,
    group_by_source_type,
    calculate_cohens_d,
    verify_alpha_assumption,
    perform_independent_t_test,
    run_analysis_for_metric,
)


class TestIndependentTTestImplementation:
    """
    Tests for the independent two-sample t-test implementation.

    These tests verify that the t-test correctly calculates:
    - p-value
    - t-statistic
    - effect size (Cohen's d)
    """

    @pytest.fixture
    def sample_data_file(self, tmp_path):
        """Create a temporary CSV file with sample metrics data."""
        data = [
            ["pr_id", "source_type", "comment_count", "time_to_merge_minutes", "review_cycles", "complexity_score"],
            [1, "llm", 5, 120.5, 2, 10.5],
            [2, "llm", 3, 90.0, 1, 8.2],
            [3, "llm", 7, 150.0, 3, 12.1],
            [4, "llm", 4, 100.0, 2, 9.0],
            [5, "llm", 6, 130.0, 2, 11.0],
            [6, "human", 10, 200.0, 4, 15.0],
            [7, "human", 8, 180.0, 3, 14.0],
            [8, "human", 12, 250.0, 5, 16.0],
            [9, "human", 9, 190.0, 4, 15.5],
            [10, "human", 11, 220.0, 4, 16.5],
        ]

        file_path = tmp_path / "sample_metrics.csv"
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(data)

        return str(file_path)

    @pytest.fixture
    def small_sample_data_file(self, tmp_path):
        """Create a temporary CSV file with a small sample for edge case testing."""
        # Small groups to test t-test with limited data
        data = [
            ["pr_id", "source_type", "comment_count", "time_to_merge_minutes", "review_cycles", "complexity_score"],
            [1, "llm", 5, 120.5, 2, 10.5],
            [2, "llm", 3, 90.0, 1, 8.2],
            [3, "human", 10, 200.0, 4, 15.0],
            [4, "human", 8, 180.0, 3, 14.0],
        ]

        file_path = tmp_path / "small_sample_metrics.csv"
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(data)

        return str(file_path)

    def test_perform_independent_t_test_returns_required_outputs(self, sample_data_file):
        """
        Test that perform_independent_t_test returns a dictionary with:
        - p_value (float)
        - t_statistic (float)
        - effect_size (float)
        """
        # Load and group data
        metrics = load_metrics_data(sample_data_file)
        llm_group, human_group = group_by_source_type(metrics, "comment_count")

        # Perform t-test
        result = perform_independent_t_test(llm_group, human_group)

        # Verify output structure
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "p_value" in result, "Result must contain 'p_value' key"
        assert "t_statistic" in result, "Result must contain 't_statistic' key"
        assert "effect_size" in result, "Result must contain 'effect_size' key"

        # Verify types
        assert isinstance(result["p_value"], float), "p_value must be a float"
        assert isinstance(result["t_statistic"], float), "t_statistic must be a float"
        assert isinstance(result["effect_size"], float), "effect_size must be a float"

    def test_perform_independent_t_test_calculates_correct_statistics(self, sample_data_file):
        """
        Test that the t-test calculates correct statistics for a known dataset.
        We use numpy's ttest_ind to verify the implementation.
        """
        # Load and group data
        metrics = load_metrics_data(sample_data_file)
        llm_group, human_group = group_by_source_type(metrics, "comment_count")

        # Perform t-test
        result = perform_independent_t_test(llm_group, human_group)

        # Verify against numpy implementation
        from scipy import stats
        numpy_result = stats.ttest_ind(llm_group, human_group)

        # Check that p-value is approximately correct (allowing for minor floating point differences)
        assert math.isclose(result["p_value"], numpy_result.pvalue, rel_tol=1e-5), \
            f"p_value mismatch: got {result['p_value']}, expected {numpy_result.pvalue}"

        # Check that t-statistic is approximately correct
        assert math.isclose(result["t_statistic"], numpy_result.statistic, rel_tol=1e-5), \
            f"t_statistic mismatch: got {result['t_statistic']}, expected {numpy_result.statistic}"

    def test_cohens_d_calculation(self, sample_data_file):
        """
        Test that Cohen's d is calculated correctly.
        Cohen's d = (mean1 - mean2) / pooled_std
        """
        # Load and group data
        metrics = load_metrics_data(sample_data_file)
        llm_group, human_group = group_by_source_type(metrics, "comment_count")

        # Calculate Cohen's d using our implementation
        effect_size = calculate_cohens_d(llm_group, human_group)

        # Calculate expected value manually
        mean1 = np.mean(llm_group)
        mean2 = np.mean(human_group)
        std1 = np.std(llm_group, ddof=1)
        std2 = np.std(human_group, ddof=1)
        n1 = len(llm_group)
        n2 = len(human_group)

        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        expected_d = (mean1 - mean2) / pooled_std

        # Verify
        assert math.isclose(effect_size, expected_d, rel_tol=1e-5), \
            f"Cohen's d mismatch: got {effect_size}, expected {expected_d}"

    def test_perform_independent_t_test_with_small_sample(self, small_sample_data_file):
        """
        Test t-test implementation with a small sample size (2 per group).
        This ensures the function handles edge cases gracefully.
        """
        metrics = load_metrics_data(small_sample_data_file)
        llm_group, human_group = group_by_source_type(metrics, "comment_count")

        # Should not raise an exception
        result = perform_independent_t_test(llm_group, human_group)

        # Verify outputs exist
        assert "p_value" in result
        assert "t_statistic" in result
        assert "effect_size" in result

        # Values should be finite numbers
        assert math.isfinite(result["p_value"])
        assert math.isfinite(result["t_statistic"])
        assert math.isfinite(result["effect_size"])

    def test_run_analysis_for_metric_returns_complete_result(self, sample_data_file):
        """
        Test that run_analysis_for_metric returns a complete result dictionary
        including all required fields for t-test analysis.
        """
        metrics = load_metrics_data(sample_data_file)

        result = run_analysis_for_metric(metrics, "comment_count", "t_test")

        # Verify structure
        assert isinstance(result, dict)
        assert "p_value" in result
        assert "t_statistic" in result
        assert "effect_size" in result
        assert "is_significant" in result
        assert "metric_name" in result
        assert "test_type" in result

        # Verify types
        assert isinstance(result["p_value"], float)
        assert isinstance(result["t_statistic"], float)
        assert isinstance(result["effect_size"], float)
        assert isinstance(result["is_significant"], bool)
        assert result["metric_name"] == "comment_count"
        assert result["test_type"] == "t_test"

    def test_effect_size_magnitude_interpretation(self, sample_data_file):
        """
        Test that effect sizes are calculated with reasonable magnitudes.
        Cohen's d guidelines:
        - 0.2: small effect
        - 0.5: medium effect
        - 0.8: large effect
        """
        metrics = load_metrics_data(sample_data_file)
        llm_group, human_group = group_by_source_type(metrics, "comment_count")

        effect_size = calculate_cohens_d(llm_group, human_group)

        # Effect size should be a finite number
        assert math.isfinite(effect_size)

        # In our sample data, human group has higher comment counts,
        # so we expect a negative effect size (llm - human)
        # The magnitude should be reasonable (not extremely large or small)
        assert abs(effect_size) < 10, "Effect size magnitude seems unreasonably large"

    def test_t_test_with_identical_groups(self, tmp_path):
        """
        Test t-test behavior when both groups have identical values.
        This should result in a t-statistic of 0 and p-value of 1.0.
        """
        data = [
            ["pr_id", "source_type", "comment_count", "time_to_merge_minutes", "review_cycles", "complexity_score"],
            [1, "llm", 5, 120.5, 2, 10.5],
            [2, "llm", 5, 120.5, 2, 10.5],
            [3, "human", 5, 120.5, 2, 10.5],
            [4, "human", 5, 120.5, 2, 10.5],
        ]

        file_path = tmp_path / "identical_groups.csv"
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(data)

        metrics = load_metrics_data(str(file_path))
        llm_group, human_group = group_by_source_type(metrics, "comment_count")

        result = perform_independent_t_test(llm_group, human_group)

        # With identical groups, t-statistic should be 0 and p-value should be 1.0
        assert math.isclose(result["t_statistic"], 0.0, abs_tol=1e-10)
        assert math.isclose(result["p_value"], 1.0, abs_tol=1e-10)

    def test_alpha_assumption_verification(self):
        """
        Test that verify_alpha_assumption correctly validates the alpha threshold.
        """
        # Valid alpha values
        assert verify_alpha_assumption(0.05) is True
        assert verify_alpha_assumption(0.01) is True
        assert verify_alpha_assumption(0.10) is True

        # Invalid alpha values (outside 0-1 range)
        assert verify_alpha_assumption(1.5) is False
        assert verify_alpha_assumption(-0.1) is False

        # Edge cases
        assert verify_alpha_assumption(0.0) is False  # Alpha should be > 0
        assert verify_alpha_assumption(1.0) is False  # Alpha should be < 1