"""
Unit tests for effect size calculations in code/analysis/effect_sizes.py.

Tests cover:
- Cohen's d calculation (independent and paired)
- Multiple comparison corrections (Bonferroni, Holm-Bonferroni)
- Pairwise comparisons by stratum
- Paired output verification
"""

import pytest
import numpy as np
import pandas as pd
from dataclasses import asdict

# Import the module under test using the exact API surface provided
from analysis.effect_sizes import (
    PairwiseComparison,
    EffectSizeResult,
    calculate_cohens_d,
    calculate_paired_cohens_d,
    bonferroni_correction,
    holm_bonferroni_correction,
    perform_pairwise_comparisons_by_stratum,
    verify_paired_output,
    run_effect_size_pipeline,
)


class TestCalculateCohensD:
    """Tests for independent samples Cohen's d calculation."""

    def test_cohens_d_basic(self):
        """Test basic Cohen's d calculation with known values."""
        # Group A: mean=10, std=2, n=10
        group_a = np.array([8, 9, 10, 11, 12, 9, 10, 11, 10, 10])
        # Group B: mean=12, std=2, n=10
        group_b = np.array([10, 11, 12, 13, 14, 11, 12, 13, 12, 12])

        result = calculate_cohens_d(group_a, group_b)

        # Expected: mean_diff = -2, pooled_std = 2, d = -1.0
        assert isinstance(result, EffectSizeResult)
        assert result.group_a_name == "group_a"
        assert result.group_b_name == "group_b"
        assert np.isclose(result.mean_a, 10.0, atol=0.01)
        assert np.isclose(result.mean_b, 12.0, atol=0.01)
        assert np.isclose(result.mean_diff, -2.0, atol=0.01)
        # Pooled std should be close to 2.0
        assert np.isclose(result.pooled_std, 2.0, atol=0.1)
        # Cohen's d should be close to -1.0
        assert np.isclose(result.cohen_d, -1.0, atol=0.1)
        assert result.sample_size_a == 10
        assert result.sample_size_b == 10

    def test_cohens_d_unequal_variances(self):
        """Test Cohen's d with unequal variances."""
        group_a = np.array([1, 2, 3, 4, 5])
        group_b = np.array([10, 12, 14, 16, 18, 20, 22, 24, 26, 28])

        result = calculate_cohens_d(group_a, group_b)

        assert isinstance(result, EffectSizeResult)
        assert result.cohen_d != 0
        assert not np.isnan(result.cohen_d)

    def test_cohens_d_identical_groups(self):
        """Test Cohen's d when groups are identical."""
        group_a = np.array([1, 2, 3, 4, 5])
        group_b = np.array([1, 2, 3, 4, 5])

        result = calculate_cohens_d(group_a, group_b)

        assert np.isclose(result.cohen_d, 0.0, atol=1e-6)
        assert result.mean_diff == 0.0

    def test_cohens_d_single_element(self):
        """Test Cohen's d with single element groups (should handle gracefully)."""
        group_a = np.array([1])
        group_b = np.array([2])

        # With single element, std is 0, which may cause division by zero
        # The function should handle this or return a meaningful result
        result = calculate_cohens_d(group_a, group_b)
        assert isinstance(result, EffectSizeResult)

    def test_cohens_d_as_dict_serializable(self):
        """Test that EffectSizeResult can be serialized to dict."""
        group_a = np.array([1, 2, 3, 4, 5])
        group_b = np.array([6, 7, 8, 9, 10])

        result = calculate_cohens_d(group_a, group_b)
        result_dict = asdict(result)

        assert isinstance(result_dict, dict)
        assert "cohen_d" in result_dict
        assert "mean_diff" in result_dict
        assert "pooled_std" in result_dict


class TestCalculatePairedCohensD:
    """Tests for paired samples Cohen's d calculation."""

    def test_paired_cohens_d_basic(self):
        """Test basic paired Cohen's d calculation."""
        # Before and after measurements
        before = np.array([10, 12, 14, 16, 18, 10, 12, 14, 16, 18])
        after = np.array([12, 14, 16, 18, 20, 12, 14, 16, 18, 20])

        result = calculate_paired_cohens_d(before, after)

        assert isinstance(result, EffectSizeResult)
        # Mean difference should be 2.0
        assert np.isclose(result.mean_diff, 2.0, atol=0.01)
        # Cohen's d should be positive
        assert result.cohen_d > 0

    def test_paired_cohens_d_no_effect(self):
        """Test paired Cohen's d with no effect."""
        before = np.array([1, 2, 3, 4, 5])
        after = np.array([1, 2, 3, 4, 5])

        result = calculate_paired_cohens_d(before, after)

        assert np.isclose(result.cohen_d, 0.0, atol=1e-6)

    def test_paired_cohens_d_negative_effect(self):
        """Test paired Cohen's d with negative effect."""
        before = np.array([10, 12, 14, 16, 18])
        after = np.array([8, 10, 12, 14, 16])

        result = calculate_paired_cohens_d(before, after)

        assert result.cohen_d < 0


class TestBonferroniCorrection:
    """Tests for Bonferroni multiple comparison correction."""

    def test_bonferroni_basic(self):
        """Test basic Bonferroni correction."""
        p_values = [0.01, 0.05, 0.10, 0.20]

        result = bonferroni_correction(p_values)

        assert len(result) == len(p_values)
        # Corrected p-values should be original * n_tests
        # But capped at 1.0
        expected = [min(p * 4, 1.0) for p in p_values]
        for i, (orig, corr) in enumerate(zip(p_values, result)):
            assert np.isclose(corr, expected[i], atol=1e-6)

    def test_bonferroni_single_pvalue(self):
        """Test Bonferroni with a single p-value."""
        p_values = [0.05]

        result = bonferroni_correction(p_values)

        assert len(result) == 1
        assert np.isclose(result[0], 0.05, atol=1e-6)

    def test_bonferroni_empty_list(self):
        """Test Bonferroni with empty list."""
        p_values = []

        result = bonferroni_correction(p_values)

        assert result == []


class TestHolmBonferroniCorrection:
    """Tests for Holm-Bonferroni step-down correction."""

    def test_holm_bonferroni_basic(self):
        """Test basic Holm-Bonferroni correction."""
        p_values = [0.01, 0.04, 0.03, 0.20]

        result = holm_bonferroni_correction(p_values)

        assert len(result) == len(p_values)
        # All corrected p-values should be >= original p-values
        for orig, corr in zip(p_values, result):
            assert corr >= orig - 1e-6

    def test_holm_bonferroni_monotonicity(self):
        """Test that corrected p-values maintain monotonicity."""
        p_values = [0.01, 0.02, 0.03, 0.04]

        result = holm_bonferroni_correction(p_values)

        # Corrected p-values should be non-decreasing
        for i in range(len(result) - 1):
            assert result[i] <= result[i + 1] + 1e-6

    def test_holm_bonferroni_vs_bonferroni(self):
        """Test that Holm-Bonferroni is less conservative than Bonferroni."""
        p_values = [0.01, 0.05, 0.10]

        bonf_result = bonferroni_correction(p_values)
        holm_result = holm_bonferroni_correction(p_values)

        # Holm-Bonferroni should be <= Bonferroni for all p-values
        for h, b in zip(holm_result, bonf_result):
            assert h <= b + 1e-6


class TestPerformPairwiseComparisonsByStratum:
    """Tests for pairwise comparisons stratified by experience level."""

    def test_stratified_comparisons(self):
        """Test pairwise comparisons across experience strata."""
        # Create sample data with experience levels
        data = pd.DataFrame({
            "tool_usage": ["A"] * 30 + ["B"] * 30,
            "experience_level": (
                ["novice"] * 10 + ["intermediate"] * 10 + ["expert"] * 10 +
                ["novice"] * 10 + ["intermediate"] * 10 + ["expert"] * 10
            ),
            "task_time": (
                [10, 11, 12, 13, 14, 15, 16, 17, 18, 19] +  # novice A
                [8, 9, 10, 11, 12, 13, 14, 15, 16, 17] +   # intermediate A
                [6, 7, 8, 9, 10, 11, 12, 13, 14, 15] +     # expert A
                [12, 13, 14, 15, 16, 17, 18, 19, 20, 21] + # novice B
                [10, 11, 12, 13, 14, 15, 16, 17, 18, 19] + # intermediate B
                [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]     # expert B
            ),
        })

        result = perform_pairwise_comparisons_by_stratum(
            data,
            group_col="tool_usage",
            outcome_col="task_time",
            stratum_col="experience_level",
        )

        assert isinstance(result, dict)
        # Should have results for each stratum
        assert "novice" in result
        assert "intermediate" in result
        assert "expert" in result

        # Each stratum should have pairwise comparisons
        for stratum_name, stratum_result in result.items():
            assert "comparisons" in stratum_result
            assert "effect_sizes" in stratum_result
            assert "corrections" in stratum_result

    def test_stratified_comparisons_single_stratum(self):
        """Test with data having only one stratum."""
        data = pd.DataFrame({
            "tool_usage": ["A"] * 10 + ["B"] * 10,
            "experience_level": ["novice"] * 20,
            "task_time": list(range(10)) + list(range(10, 20)),
        })

        result = perform_pairwise_comparisons_by_stratum(
            data,
            group_col="tool_usage",
            outcome_col="task_time",
            stratum_col="experience_level",
        )

        assert "novice" in result
        assert len(result["novice"]["comparisons"]) > 0

    def test_stratified_comparisons_empty_data(self):
        """Test with empty dataframe."""
        data = pd.DataFrame(columns=["tool_usage", "experience_level", "task_time"])

        result = perform_pairwise_comparisons_by_stratum(
            data,
            group_col="tool_usage",
            outcome_col="task_time",
            stratum_col="experience_level",
        )

        assert isinstance(result, dict)
        # Should handle empty data gracefully
        for stratum_name, stratum_result in result.items():
            assert stratum_result["comparisons"] == []


class TestVerifyPairedOutput:
    """Tests for paired output verification (Constitution Principle VI)."""

    def test_verify_paired_output_complete(self):
        """Test verification when p-values and effect sizes are paired."""
        results = {
            "p_values": [0.01, 0.05, 0.10],
            "effect_sizes": [
                {"cohen_d": 0.5, "group_a": "A", "group_b": "B"},
                {"cohen_d": 0.3, "group_a": "A", "group_b": "C"},
                {"cohen_d": 0.1, "group_a": "B", "group_b": "C"},
            ],
        }

        is_valid, message = verify_paired_output(results)

        assert is_valid
        assert "paired" in message.lower()

    def test_verify_paired_output_missing_effect_sizes(self):
        """Test verification when effect sizes are missing."""
        results = {
            "p_values": [0.01, 0.05, 0.10],
            "effect_sizes": [],
        }

        is_valid, message = verify_paired_output(results)

        assert not is_valid
        assert "missing" in message.lower() or "effect" in message.lower()

    def test_verify_paired_output_mismatched_lengths(self):
        """Test verification when lengths don't match."""
        results = {
            "p_values": [0.01, 0.05],
            "effect_sizes": [
                {"cohen_d": 0.5, "group_a": "A", "group_b": "B"},
                {"cohen_d": 0.3, "group_a": "A", "group_b": "C"},
                {"cohen_d": 0.1, "group_a": "B", "group_b": "C"},
            ],
        }

        is_valid, message = verify_paired_output(results)

        assert not is_valid
        assert "mismatch" in message.lower() or "length" in message.lower()

    def test_verify_paired_output_empty(self):
        """Test verification with empty results."""
        results = {
            "p_values": [],
            "effect_sizes": [],
        }

        is_valid, message = verify_paired_output(results)

        # Empty results should be considered valid (no violations)
        assert is_valid


class TestRunEffectSizePipeline:
    """Tests for the complete effect size pipeline."""

    def test_run_pipeline_basic(self):
        """Test running the full effect size pipeline."""
        # Create sample data
        data = pd.DataFrame({
            "tool_usage": ["A"] * 20 + ["B"] * 20,
            "experience_years": np.concatenate([
                np.random.normal(1.5, 0.5, 20),  # novice
                np.random.normal(3.5, 0.5, 20),  # intermediate
            ]),
            "task_time": np.concatenate([
                np.random.normal(15, 3, 20),
                np.random.normal(12, 3, 20),
            ]),
        })

        result = run_effect_size_pipeline(
            data,
            group_col="tool_usage",
            outcome_col="task_time",
            stratum_col="experience_years",
            stratum_thresholds=[2, 5],
            stratum_labels=["novice", "intermediate", "expert"],
        )

        assert isinstance(result, dict)
        assert "stratified_results" in result
        assert "corrections" in result
        assert "verification" in result

    def test_run_pipeline_with_missing_data(self):
        """Test pipeline with missing values in data."""
        data = pd.DataFrame({
            "tool_usage": ["A"] * 10 + ["B"] * 10,
            "experience_years": [1.0, 1.5, 2.0, np.nan, 3.0] * 4,
            "task_time": [10, 12, 14, 16, 18] * 4,
        })

        result = run_effect_size_pipeline(
            data,
            group_col="tool_usage",
            outcome_col="task_time",
            stratum_col="experience_years",
            stratum_thresholds=[2, 5],
            stratum_labels=["novice", "intermediate", "expert"],
        )

        assert isinstance(result, dict)
        # Should handle missing data by filtering
        assert "stratified_results" in result