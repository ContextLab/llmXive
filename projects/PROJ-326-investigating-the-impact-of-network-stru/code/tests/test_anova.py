"""
Unit tests for ANOVA and multiple-comparison correction in code/src/analysis/anova.py
"""
import pytest
import numpy as np
import pandas as pd
from typing import List, Dict, Any

from code.src.analysis.anova import (
    run_one_way_anova,
    apply_multiple_comparison_correction,
    correct_regression_pvalues,
    run_anova_on_diffusion_by_topology,
    ANOVAError
)
from code.src.analysis.regression import RegressionResult


class TestANOVATest:
    """Tests for one-way ANOVA F-test functionality."""

    def test_anova_significant_difference(self):
        """Test ANOVA detects significant difference between groups."""
        # Group 1: mean=10, Group 2: mean=20
        groups = {
            "group_a": np.random.normal(10, 1, 50),
            "group_b": np.random.normal(20, 1, 50)
        }
        result = run_one_way_anova(groups)
        assert result["f_statistic"] > 0
        assert result["p_value"] < 0.05  # Should be significant
        assert result["df_between"] == 1
        assert result["df_within"] == 98

    def test_anova_no_difference(self):
        """Test ANOVA finds no significant difference when groups are same."""
        np.random.seed(42)
        groups = {
            "group_a": np.random.normal(10, 1, 50),
            "group_b": np.random.normal(10, 1, 50)
        }
        result = run_one_way_anova(groups)
        # p-value should be > 0.05 (no significant difference)
        assert result["p_value"] > 0.05

    def test_anova_empty_groups(self):
        """Test ANOVA raises error for empty groups."""
        with pytest.raises(ANOVAError):
            run_one_way_anova({})

    def test_anova_zero_sample_group(self):
        """Test ANOVA raises error if a group has zero samples."""
        with pytest.raises(ANOVAError):
            run_one_way_anova({"group_a": [], "group_b": [1, 2, 3]})


class TestMultipleComparisonCorrection:
    """Tests for multiple-comparison correction methods."""

    def test_bonferroni_correction(self):
        """Test Bonferroni correction reduces p-values appropriately."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        result = apply_multiple_comparison_correction(p_values, method="bonferroni", alpha=0.05)
        # Bonferroni: p_corrected = p * n
        # For 5 tests, 0.01 * 5 = 0.05, 0.02 * 5 = 0.10, etc.
        assert len(result["corrected_p_values"]) == 5
        assert result["method"] == "bonferroni"
        # The smallest p-value (0.01) becomes 0.05, which is exactly at threshold
        # Depending on implementation, might be considered significant or not; we check the math
        expected_corrected = [min(p * 5, 1.0) for p in p_values]
        for actual, expected in zip(result["corrected_p_values"], expected_corrected):
            assert abs(actual - expected) < 1e-9

    def test_benjamini_hochberg_correction(self):
        """Test Benjamini-Hochberg FDR correction."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        result = apply_multiple_comparison_correction(p_values, method="benjamini_hochberg", alpha=0.05)
        assert len(result["corrected_p_values"]) == 5
        assert result["method"] == "benjamini_hochberg"
        # BH correction should be less stringent than Bonferroni
        bonf_result = apply_multiple_comparison_correction(p_values, method="bonferroni")
        # BH corrected p-values should be <= Bonferroni (except for floating point)
        for bh_p, bonf_p in zip(result["corrected_p_values"], bonf_result["corrected_p_values"]):
            assert bh_p <= bonf_p + 1e-9

    def test_correction_with_all_significant(self):
        """Test correction when all raw p-values are very small."""
        p_values = [0.001, 0.002, 0.003]
        result = apply_multiple_comparison_correction(p_values, method="bonferroni", alpha=0.05)
        # 0.001 * 3 = 0.003 < 0.05 -> significant
        assert all(result["is_significant"])

    def test_correction_with_none_significant(self):
        """Test correction when no raw p-values are significant even after correction."""
        p_values = [0.2, 0.3, 0.4]
        result = apply_multiple_comparison_correction(p_values, method="bonferroni", alpha=0.05)
        assert not any(result["is_significant"])

    def test_empty_p_values(self):
        """Test correction raises error for empty list."""
        with pytest.raises(ANOVAError):
            apply_multiple_comparison_correction([])

    def test_invalid_method(self):
        """Test correction raises error for invalid method."""
        with pytest.raises(ANOVAError):
            apply_multiple_comparison_correction([0.01], method="invalid_method")


class TestRegressionCorrection:
    """Tests for applying correction to regression p-values."""

    def test_correct_regression_pvalues(self):
        """Test that regression p-values are correctly corrected."""
        # Create mock RegressionResult objects
        res1 = RegressionResult(
            model_name="linear",
            r_squared=0.8,
            coefficients=[1.0, 2.0],
            p_values=[0.01, 0.02],
            std_errors=[0.1, 0.1]
        )
        res2 = RegressionResult(
            model_name="polynomial",
            r_squared=0.85,
            coefficients=[0.5, 1.5, 0.1],
            p_values=[0.03, 0.04, 0.05],
            std_errors=[0.05, 0.05, 0.05]
        )

        results = [res1, res2]
        corrected_results = correct_regression_pvalues(results, method="bonferroni", alpha=0.05)

        assert len(corrected_results) == 2
        # First result has 2 p-values
        assert len(corrected_results[0]["corrected_p_values"]) == 2
        # Second result has 3 p-values
        assert len(corrected_results[1]["corrected_p_values"]) == 3

        # Check Bonferroni math: p_corrected = p * 5 (5 total tests)
        expected_1 = [min(0.01 * 5, 1.0), min(0.02 * 5, 1.0)]
        expected_2 = [min(0.03 * 5, 1.0), min(0.04 * 5, 1.0), min(0.05 * 5, 1.0)]

        for i, exp in enumerate(expected_1):
            assert abs(corrected_results[0]["corrected_p_values"][i] - exp) < 1e-9
        for i, exp in enumerate(expected_2):
            assert abs(corrected_results[1]["corrected_p_values"][i] - exp) < 1e-9

    def test_correct_regression_empty_list(self):
        """Test correction with empty regression results list."""
        results = correct_regression_pvalues([])
        assert results == []


class TestFullANOVAPipeline:
    """Integration tests for the full ANOVA pipeline on simulation data."""

    def test_anova_pipeline(self):
        """Test running ANOVA on a synthetic simulation results DataFrame."""
        np.random.seed(42)
        n_samples = 100
        data = {
            "topology_class": np.repeat(["ErdosRenyi", "WattsStrogatz", "BarabasiAlbert"], n_samples // 3),
            "diffusion_rate": np.concatenate([
                np.random.normal(0.5, 0.1, n_samples // 3),
                np.random.normal(0.6, 0.1, n_samples // 3),
                np.random.normal(0.7, 0.1, n_samples // 3)
            ])
        }
        df = pd.DataFrame(data)

        result = run_anova_on_diffusion_by_topology(
            df,
            topology_column="topology_class",
            diffusion_column="diffusion_rate",
            correction_method="bonferroni",
            alpha=0.05
        )

        assert "anova_result" in result
        assert "post_hoc_result" in result
        assert "pairwise_comparisons" in result

        # With these means, ANOVA should be significant
        assert result["anova_result"]["p_value"] < 0.05

        # Post-hoc should have been run
        assert result["post_hoc_result"] is not None
        assert len(result["pairwise_comparisons"]) == 3  # 3 pairs: ER-W, ER-B, W-B

    def test_anova_pipeline_no_significance(self):
        """Test pipeline when groups are not significantly different."""
        np.random.seed(42)
        n_samples = 100
        # All groups have same mean
        data = {
            "topology_class": np.repeat(["A", "B", "C"], n_samples // 3),
            "diffusion_rate": np.concatenate([
                np.random.normal(0.5, 0.1, n_samples // 3),
                np.random.normal(0.5, 0.1, n_samples // 3),
                np.random.normal(0.5, 0.1, n_samples // 3)
            ])
        }
        df = pd.DataFrame(data)

        result = run_anova_on_diffusion_by_topology(
            df,
            topology_column="topology_class",
            diffusion_column="diffusion_rate",
            correction_method="bonferroni",
            alpha=0.05
        )

        # ANOVA p-value should be > 0.05
        assert result["anova_result"]["p_value"] > 0.05
        # Post-hoc should be None because ANOVA not significant
        assert result["post_hoc_result"] is None
        assert result["pairwise_comparisons"] == []

    def test_anova_pipeline_missing_columns(self):
        """Test pipeline raises error if required columns are missing."""
        df = pd.DataFrame({"wrong_col": [1, 2, 3]})
        with pytest.raises(ANOVAError):
            run_anova_on_diffusion_by_topology(df, "topology_class", "diffusion_rate")
