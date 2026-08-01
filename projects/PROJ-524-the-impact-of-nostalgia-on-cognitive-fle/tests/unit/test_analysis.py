"""
Unit tests for code/analysis.py statistical functions.
Tests Welch's t-test, Cohen's d, confidence intervals, Bonferroni correction,
and power analysis using deterministic synthetic data.
"""
import pytest
import numpy as np
from scipy import stats
import pandas as pd
import json
import os
import sys
from pathlib import Path

# Add project root to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis import (
    welch_t_test,
    calculate_cohen_d,
    calculate_effect_size_ci,
    bonferroni_correction,
    calculate_power_and_mdes,
    run_sensitivity_analysis
)


class TestWelchTTest:
    def test_welch_t_test_basic(self):
        """Test basic Welch's t-test functionality."""
        group_a = np.array([23, 25, 28, 30, 32, 26, 29, 27, 31, 24])
        group_b = np.array([35, 38, 40, 42, 36, 39, 41, 37, 43, 34])

        result = welch_t_test(group_a, group_b)

        assert 't_statistic' in result
        assert 'p_value' in result
        assert 'df' in result
        assert isinstance(result['t_statistic'], float)
        assert 0 < result['p_value'] <= 1.0
        assert result['df'] > 0

    def test_welch_t_test_equal_groups(self):
        """Test that identical groups yield non-significant p-value."""
        group_a = np.array([25, 26, 27, 28, 29])
        group_b = np.array([25, 26, 27, 28, 29])

        result = welch_t_test(group_a, group_b)
        assert result['p_value'] > 0.05

    def test_welch_t_test_unequal_variances(self):
        """Test Welch's t-test handles unequal variances correctly."""
        group_a = np.array([10, 12, 11, 13, 10])  # Low variance
        group_b = np.array([15, 25, 10, 30, 5])   # High variance

        result = welch_t_test(group_a, group_b)
        assert 't_statistic' in result
        assert 'p_value' in result

    def test_welch_t_test_small_sample(self):
        """Test with very small sample sizes."""
        group_a = np.array([10, 12])
        group_b = np.array([15, 18])

        result = welch_t_test(group_a, group_b)
        assert 't_statistic' in result
        assert 'p_value' in result


class TestCohenD:
    def test_cohen_d_basic(self):
        """Test basic Cohen's d calculation."""
        group_a = np.array([23, 25, 28, 30, 32])
        group_b = np.array([35, 38, 40, 42, 36])

        d = calculate_cohen_d(group_a, group_b)

        assert isinstance(d, float)
        # Group B has higher mean, so d should be negative (a - b)
        assert d < 0

    def test_cohen_d_equal_groups(self):
        """Test that identical groups yield d = 0."""
        group_a = np.array([25, 26, 27, 28, 29])
        group_b = np.array([25, 26, 27, 28, 29])

        d = calculate_cohen_d(group_a, group_b)
        assert abs(d) < 1e-10

    def test_cohen_d_small_effect(self):
        """Test small effect size calculation."""
        group_a = np.array([20, 21, 22, 23, 24])
        group_b = np.array([21, 22, 23, 24, 25])

        d = calculate_cohen_d(group_a, group_b)
        assert abs(d) < 0.5  # Small effect


class TestEffectSizeCI:
    def test_calculate_effect_size_ci(self):
        """Test confidence interval calculation for effect size."""
        group_a = np.array([23, 25, 28, 30, 32, 26, 29, 27, 31, 24])
        group_b = np.array([35, 38, 40, 42, 36, 39, 41, 37, 43, 34])

        result = calculate_effect_size_ci(group_a, group_b, ci=0.95)

        assert 'cohens_d' in result
        assert 'ci_lower' in result
        assert 'ci_upper' in result
        assert result['ci_lower'] < result['cohens_d'] < result['ci_upper']

    def test_calculate_effect_size_ci_99(self):
        """Test 99% confidence interval is wider than 95%."""
        group_a = np.array([23, 25, 28, 30, 32, 26, 29, 27, 31, 24])
        group_b = np.array([35, 38, 40, 42, 36, 39, 41, 37, 43, 34])

        ci_95 = calculate_effect_size_ci(group_a, group_b, ci=0.95)
        ci_99 = calculate_effect_size_ci(group_a, group_b, ci=0.99)

        width_95 = ci_95['ci_upper'] - ci_95['ci_lower']
        width_99 = ci_99['ci_upper'] - ci_99['ci_lower']

        assert width_99 > width_95


class TestBonferroniCorrection:
    def test_bonferroni_basic(self):
        """Test basic Bonferroni correction."""
        p_values = [0.01, 0.04, 0.06, 0.10, 0.20]

        result = bonferroni_correction(p_values)

        assert len(result['corrected_p_values']) == len(p_values)
        assert result['alpha'] == 0.05
        assert result['num_tests'] == 5

    def test_bonferroni_single_test(self):
        """Test Bonferroni with single test (no correction)."""
        p_values = [0.03]

        result = bonferroni_correction(p_values)
        assert result['corrected_p_values'][0] == 0.03
        assert result['is_significant'][0] == (0.03 < 0.05)

    def test_bonferroni_all_significant(self):
        """Test when all tests are significant after correction."""
        p_values = [0.001, 0.002, 0.003]

        result = bonferroni_correction(p_values)
        assert all(result['is_significant'])

    def test_bonferroni_none_significant(self):
        """Test when no tests are significant after correction."""
        p_values = [0.1, 0.2, 0.3]

        result = bonferroni_correction(p_values)
        assert not any(result['is_significant'])


class TestPowerAndMDES:
    def test_calculate_power_and_mdes(self):
        """Test power and MDES calculation."""
        group_a = np.array([23, 25, 28, 30, 32, 26, 29, 27, 31, 24])
        group_b = np.array([35, 38, 40, 42, 36, 39, 41, 37, 43, 34])

        result = calculate_power_and_mdes(group_a, group_b, alpha=0.05)

        assert 'power' in result
        assert 'mdes' in result
        assert 0 <= result['power'] <= 1
        assert result['mdes'] > 0

    def test_calculate_power_and_mdes_large_sample(self):
        """Test with larger sample sizes for higher power."""
        np.random.seed(42)
        group_a = np.random.normal(25, 5, 100)
        group_b = np.random.normal(30, 5, 100)

        result = calculate_power_and_mdes(group_a, group_b, alpha=0.05)
        assert result['power'] > 0.8  # Should have high power


class TestSensitivityAnalysis:
    def test_run_sensitivity_analysis(self):
        """Test sensitivity analysis across multiple thresholds."""
        group_a = np.array([23, 25, 28, 30, 32, 26, 29, 27, 31, 24])
        group_b = np.array([35, 38, 40, 42, 36, 39, 41, 37, 43, 34])

        thresholds = [0.01, 0.05, 0.10]
        result = run_sensitivity_analysis(group_a, group_b, thresholds)

        assert 'results' in result
        assert len(result['results']) == len(thresholds)

        for r in result['results']:
            assert 'threshold' in r
            assert 'is_significant' in r
            assert 'p_value' in r

    def test_run_sensitivity_analysis_borderline(self):
        """Test sensitivity analysis with borderline p-value."""
        # Create groups with p-value near 0.05
        group_a = np.array([25, 26, 27, 28, 29, 30, 31, 32])
        group_b = np.array([30, 31, 32, 33, 34, 35, 36, 37])

        thresholds = [0.04, 0.05, 0.06]
        result = run_sensitivity_analysis(group_a, group_b, thresholds)

        # Should show sensitivity to threshold choice
        significant_count = sum(1 for r in result['results'] if r['is_significant'])
        assert significant_count > 0 and significant_count < len(thresholds)


class TestIntegration:
    def test_full_analysis_pipeline(self):
        """Test complete analysis workflow."""
        np.random.seed(42)
        nostalgia_group = np.random.normal(25, 5, 50)
        control_group = np.random.normal(30, 5, 50)

        # Run Welch's t-test
        t_result = welch_t_test(nostalgia_group, control_group)

        # Calculate effect size
        d = calculate_cohen_d(nostalgia_group, control_group)

        # Calculate CI
        ci_result = calculate_effect_size_ci(nostalgia_group, control_group)

        # Bonferroni correction (simulating multiple comparisons)
        p_values = [t_result['p_value'], 0.03, 0.07]
        bonf_result = bonferroni_correction(p_values)

        # Power analysis
        power_result = calculate_power_and_mdes(nostalgia_group, control_group)

        # Sensitivity analysis
        sens_result = run_sensitivity_analysis(
            nostalgia_group, control_group, [0.01, 0.05, 0.10]
        )

        # Verify all results are consistent
        assert t_result['p_value'] == ci_result['p_value']
        assert bonf_result['corrected_p_values'][0] == t_result['p_value'] * 3
        assert power_result['power'] > 0
        assert len(sens_result['results']) == 3
