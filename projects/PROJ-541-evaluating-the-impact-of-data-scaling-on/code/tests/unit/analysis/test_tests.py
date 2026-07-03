"""
Tests for p-value invariance under linear scaling transformations.

This module verifies that linear transformations (scaling and shifting)
applied to data do not alter the p-values of parametric statistical tests
(t-test, ANOVA), as these tests are invariant to such transformations.

Theoretical basis:
- t-statistic: t = (mean_diff) / (SE). If x -> a*x + b, mean_diff -> a*mean_diff, SE -> a*SE.
  The ratio remains constant if a != 0.
- F-statistic (ANOVA): Ratio of variance between groups to variance within.
  Scaling cancels out in the ratio.
"""

import pytest
import numpy as np
import pandas as pd
from scipy import stats
import sys
import os
from pathlib import Path

# Ensure parent code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import run_t_test, run_anova
from simulation.generator import generate_synthetic_data
from simulation.config import SimulationConfig


class TestPValueInvariance:
    """
    Test suite for p-value invariance under linear scaling.

    We generate synthetic data with known properties, apply different
    linear scaling methods, and verify that the resulting p-values
    remain identical (within floating point tolerance).
    """

    @pytest.fixture
    def base_data_null(self):
        """Generate data for null hypothesis (mean diff = 0)."""
        config = SimulationConfig(
            n_samples=100,
            mean_diff=0.0,
            std_dev=1.0,
            distribution_type="normal",
            skewness=0.0,
            heteroscedasticity=1.0,
            seed=42
        )
        group1, group2, _ = generate_synthetic_data(config)
        return group1, group2

    @pytest.fixture
    def base_data_alt(self):
        """Generate data for alternative hypothesis (mean diff = 1.0)."""
        config = SimulationConfig(
            n_samples=100,
            mean_diff=1.0,
            std_dev=1.0,
            distribution_type="normal",
            skewness=0.0,
            heteroscedasticity=1.0,
            seed=42
        )
        group1, group2, _ = generate_synthetic_data(config)
        return group1, group2

    @pytest.fixture
    def base_data_anova(self):
        """Generate data for ANOVA (3 groups, equal means)."""
        # Create 3 groups with similar means
        np.random.seed(42)
        group1 = np.random.normal(0, 1, 100)
        group2 = np.random.normal(0, 1, 100)
        group3 = np.random.normal(0, 1, 100)
        return [group1, group2, group3]

    def test_ttest_invariance_standardization_null(self, base_data_null):
        """
        Test that t-test p-value is invariant under standardization (Z-score).
        
        Standardization: x' = (x - mean) / std
        This is a linear transformation (a=1/std, b=-mean/std).
        """
        g1, g2 = base_data_null
        
        # Original p-value
        p_orig = run_t_test(g1, g2)[1]
        
        # Standardized data
        g1_std = standardize_data(g1)
        g2_std = standardize_data(g2)
        p_std = run_t_test(g1_std, g2_std)[1]
        
        # Assert invariance (within floating point tolerance)
        assert np.isclose(p_orig, p_std, rtol=1e-10, atol=1e-12), \
            f"Standardization changed p-value: {p_orig} vs {p_std}"

    def test_ttest_invariance_standardization_alt(self, base_data_alt):
        """
        Test that t-test p-value is invariant under standardization
        for alternative hypothesis.
        """
        g1, g2 = base_data_alt
        
        p_orig = run_t_test(g1, g2)[1]
        
        g1_std = standardize_data(g1)
        g2_std = standardize_data(g2)
        p_std = run_t_test(g1_std, g2_std)[1]
        
        assert np.isclose(p_orig, p_std, rtol=1e-10, atol=1e-12), \
            f"Standardization changed p-value for alt hypothesis: {p_orig} vs {p_std}"

    def test_ttest_invariance_minmax_null(self, base_data_null):
        """
        Test that t-test p-value is invariant under Min-Max scaling.
        
        Min-Max: x' = (x - min) / (max - min)
        This is a linear transformation (a=1/(max-min), b=-min/(max-min)).
        """
        g1, g2 = base_data_null
        
        p_orig = run_t_test(g1, g2)[1]
        
        g1_mm = min_max_scale(g1)
        g2_mm = min_max_scale(g2)
        p_mm = run_t_test(g1_mm, g2_mm)[1]
        
        assert np.isclose(p_orig, p_mm, rtol=1e-10, atol=1e-12), \
            f"Min-Max scaling changed p-value: {p_orig} vs {p_mm}"

    def test_ttest_invariance_minmax_alt(self, base_data_alt):
        """
        Test that t-test p-value is invariant under Min-Max scaling
        for alternative hypothesis.
        """
        g1, g2 = base_data_alt
        
        p_orig = run_t_test(g1, g2)[1]
        
        g1_mm = min_max_scale(g1)
        g2_mm = min_max_scale(g2)
        p_mm = run_t_test(g1_mm, g2_mm)[1]
        
        assert np.isclose(p_orig, p_mm, rtol=1e-10, atol=1e-12), \
            f"Min-Max scaling changed p-value for alt hypothesis: {p_orig} vs {p_mm}"

    def test_ttest_invariance_robust_null(self, base_data_null):
        """
        Test that t-test p-value is invariant under Robust scaling.
        
        Robust: x' = (x - median) / IQR
        This is a linear transformation (a=1/IQR, b=-median/IQR).
        """
        g1, g2 = base_data_null
        
        p_orig = run_t_test(g1, g2)[1]
        
        g1_rob = robust_scale(g1)
        g2_rob = robust_scale(g2)
        p_rob = run_t_test(g1_rob, g2_rob)[1]
        
        assert np.isclose(p_orig, p_rob, rtol=1e-10, atol=1e-12), \
            f"Robust scaling changed p-value: {p_orig} vs {p_rob}"

    def test_ttest_invariance_robust_alt(self, base_data_alt):
        """
        Test that t-test p-value is invariant under Robust scaling
        for alternative hypothesis.
        """
        g1, g2 = base_data_alt
        
        p_orig = run_t_test(g1, g2)[1]
        
        g1_rob = robust_scale(g1)
        g2_rob = robust_scale(g2)
        p_rob = run_t_test(g1_rob, g2_rob)[1]
        
        assert np.isclose(p_orig, p_rob, rtol=1e-10, atol=1e-12), \
            f"Robust scaling changed p-value for alt hypothesis: {p_orig} vs {p_rob}"

    def test_anova_invariance_standardization(self, base_data_anova):
        """
        Test that ANOVA F-test p-value is invariant under standardization.
        """
        groups = base_data_anova
        
        # Original p-value
        _, p_orig = run_anova(groups)
        
        # Standardized groups
        groups_std = [standardize_data(g) for g in groups]
        _, p_std = run_anova(groups_std)
        
        assert np.isclose(p_orig, p_std, rtol=1e-10, atol=1e-12), \
            f"Standardization changed ANOVA p-value: {p_orig} vs {p_std}"

    def test_anova_invariance_minmax(self, base_data_anova):
        """
        Test that ANOVA F-test p-value is invariant under Min-Max scaling.
        """
        groups = base_data_anova
        
        _, p_orig = run_anova(groups)
        
        groups_mm = [min_max_scale(g) for g in groups]
        _, p_mm = run_anova(groups_mm)
        
        assert np.isclose(p_orig, p_mm, rtol=1e-10, atol=1e-12), \
            f"Min-Max scaling changed ANOVA p-value: {p_orig} vs {p_mm}"

    def test_anova_invariance_robust(self, base_data_anova):
        """
        Test that ANOVA F-test p-value is invariant under Robust scaling.
        """
        groups = base_data_anova
        
        _, p_orig = run_anova(groups)
        
        groups_rob = [robust_scale(g) for g in groups]
        _, p_rob = run_anova(groups_rob)
        
        assert np.isclose(p_orig, p_rob, rtol=1e-10, atol=1e-12), \
            f"Robust scaling changed ANOVA p-value: {p_orig} vs {p_rob}"

    def test_combined_transformations(self, base_data_null):
        """
        Test invariance under a sequence of different linear transformations.
        """
        g1, g2 = base_data_null
        
        p_orig = run_t_test(g1, g2)[1]
        
        # Apply multiple transformations in sequence
        g1_transformed = standardize_data(min_max_scale(robust_scale(g1)))
        g2_transformed = standardize_data(min_max_scale(robust_scale(g2)))
        
        p_transformed = run_t_test(g1_transformed, g2_transformed)[1]
        
        assert np.isclose(p_orig, p_transformed, rtol=1e-10, atol=1e-12), \
            f"Combined transformations changed p-value: {p_orig} vs {p_transformed}"

    def test_shift_invariance(self, base_data_null):
        """
        Test invariance under pure shifting (adding constant).
        """
        g1, g2 = base_data_null
        
        p_orig = run_t_test(g1, g2)[1]
        
        # Add different constants to each group
        g1_shifted = g1 + 100.0
        g2_shifted = g2 + 50.0
        
        p_shifted = run_t_test(g1_shifted, g2_shifted)[1]
        
        assert np.isclose(p_orig, p_shifted, rtol=1e-10, atol=1e-12), \
            f"Shifting changed p-value: {p_orig} vs {p_shifted}"

    def test_scale_invariance(self, base_data_null):
        """
        Test invariance under pure scaling (multiplying by constant).
        """
        g1, g2 = base_data_null
        
        p_orig = run_t_test(g1, g2)[1]
        
        # Scale by different factors
        g1_scaled = g1 * 10.0
        g2_scaled = g2 * 5.0
        
        p_scaled = run_t_test(g1_scaled, g2_scaled)[1]
        
        assert np.isclose(p_orig, p_scaled, rtol=1e-10, atol=1e-12), \
            f"Scaling changed p-value: {p_orig} vs {p_scaled}"

    def test_ttest_preserves_significance_decision(self, base_data_alt):
        """
        Test that the significance decision (reject/fail to reject H0)
        is preserved under scaling for various alpha levels.
        """
        g1, g2 = base_data_alt
        alpha_levels = [0.01, 0.05, 0.10]
        
        for alpha in alpha_levels:
            p_orig = run_t_test(g1, g2)[1]
            decision_orig = p_orig < alpha
            
            g1_std = standardize_data(g1)
            g2_std = standardize_data(g2)
            p_std = run_t_test(g1_std, g2_std)[1]
            decision_std = p_std < alpha
            
            assert decision_orig == decision_std, \
                f"Significance decision changed at alpha={alpha} with standardization"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])