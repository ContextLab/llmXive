import pytest
import numpy as np
from analysis.stats import (
    mcnemar_test,
    mcnemar_asymptotic,
    calculate_pass_rates,
    bonferroni_correction,
    fdr_correction
)

class TestMcNemarTest:
    def test_mcnemar_asymptotic_basic(self):
        """Verify McNemar's test asymptotic calculation."""
        # Contingency table:
        #           Baseline
        #           Pass  Fail
        # Intervention Pass  a     b
        #                Fail  c     d
        #
        # Example: 100 paired samples
        # Baseline: 60 pass, 40 fail
        # Intervention: 70 pass, 30 fail
        # Discordant pairs: b=10, c=20
        
        b = 10  # Baseline Pass, Intervention Fail
        c = 20  # Baseline Fail, Intervention Pass
        
        chi2_stat, p_value = mcnemar_asymptotic(b, c)
        
        assert isinstance(chi2_stat, float)
        assert isinstance(p_value, float)
        assert 0 <= p_value <= 1

    def test_mcnemar_test_edge_case_equal(self):
        """Verify McNemar's test when b == c (no difference)."""
        b = 15
        c = 15
        
        chi2_stat, p_value = mcnemar_asymptotic(b, c)
        
        # When b == c, chi2 should be 0 and p-value should be 1.0
        assert chi2_stat == 0.0
        assert p_value == 1.0

    def test_mcnemar_test_small_sample(self):
        """Verify McNemar's test with small sample."""
        b = 1
        c = 5
        
        chi2_stat, p_value = mcnemar_asymptotic(b, c)
        
        assert isinstance(p_value, float)
        assert 0 <= p_value <= 1

class TestCalculatePassRates:
    def test_calculate_pass_rates_basic(self):
        """Verify pass rate calculation."""
        baseline_outcomes = [1, 1, 0, 1, 0]  # 3/5 = 0.6
        intervention_outcomes = [1, 1, 1, 1, 0]  # 4/5 = 0.8
        
        baseline_rate, intervention_rate = calculate_pass_rates(
            baseline_outcomes,
            intervention_outcomes
        )
        
        assert baseline_rate == 0.6
        assert intervention_rate == 0.8

    def test_calculate_pass_rates_all_pass(self):
        """Verify pass rate when all pass."""
        baseline = [1, 1, 1]
        intervention = [1, 1, 1]
        
        baseline_rate, intervention_rate = calculate_pass_rates(baseline, intervention)
        
        assert baseline_rate == 1.0
        assert intervention_rate == 1.0

    def test_calculate_pass_rates_all_fail(self):
        """Verify pass rate when all fail."""
        baseline = [0, 0, 0]
        intervention = [0, 0, 0]
        
        baseline_rate, intervention_rate = calculate_pass_rates(baseline, intervention)
        
        assert baseline_rate == 0.0
        assert intervention_rate == 0.0

class TestMultipleComparisonCorrection:
    def test_bonferroni_correction(self):
        """Verify Bonferroni correction."""
        p_values = [0.01, 0.05, 0.1]
        alpha = 0.05
        
        corrected = bonferroni_correction(p_values, alpha)
        
        assert isinstance(corrected, list)
        assert len(corrected) == len(p_values)
        
        # Bonferroni multiplies p-values by number of tests
        expected = [min(p * len(p_values), 1.0) for p in p_values]
        assert corrected == expected

    def test_fdr_correction(self):
        """Verify FDR (Benjamini-Hochberg) correction."""
        p_values = [0.01, 0.04, 0.05, 0.2]
        alpha = 0.05
        
        corrected = fdr_correction(p_values, alpha)
        
        assert isinstance(corrected, list)
        assert len(corrected) == len(p_values)

    def test_correction_with_single_pvalue(self):
        """Verify correction with single p-value."""
        p_values = [0.03]
        alpha = 0.05
        
        corrected = bonferroni_correction(p_values, alpha)
        assert corrected[0] == 0.03  # No change for single test
