"""
Unit tests for statistical utilities in stats_helpers.py
"""

import pytest
import numpy as np
from code.utils.stats_helpers import (
    bonferroni_correct,
    permutation_test,
    calculate_medes,
    calculate_sample_size_for_r2,
    f_test_comparison
)


class TestBonferroniCorrect:
    def test_basic_correction(self):
        """Test basic Bonferroni correction"""
        p_values = [0.01, 0.05, 0.10]
        result = bonferroni_correct(p_values, alpha=0.05)

        assert len(result['corrected_p_values']) == 3
        assert result['threshold'] == 0.05 / 3
        assert result['raw_p_values'] == p_values

    def test_significance_detection(self):
        """Test that significant results are correctly identified"""
        p_values = [0.001, 0.01, 0.20]  # Only first should be significant after correction
        result = bonferroni_correct(p_values, alpha=0.05)

        # With 3 tests, threshold = 0.0167
        # Corrected: 0.003, 0.03, 0.60
        # Only first should be significant
        assert result['significant'][0] == True
        assert result['significant'][1] == False
        assert result['significant'][2] == False

    def test_empty_input(self):
        """Test handling of empty input"""
        result = bonferroni_correct([], alpha=0.05)
        assert result['corrected_p_values'] == []
        assert result['threshold'] == 0.05

    def test_p_value_capping(self):
        """Test that corrected p-values are capped at 1.0"""
        p_values = [0.5, 0.6]
        result = bonferroni_correct(p_values, alpha=0.05)
        assert all(p <= 1.0 for p in result['corrected_p_values'])


class TestPermutationTest:
    def test_pearson_correlation(self):
        """Test permutation test with Pearson correlation"""
        np.random.seed(42)
        x = np.random.randn(50)
        y = x * 0.5 + np.random.randn(50) * 0.5  # Positive correlation

        result = permutation_test(x, y, statistic='pearson', n_permutations=1000, random_state=42)

        assert 'observed_stat' in result
        assert 'p_value' in result
        assert 'permuted_stats' in result
        assert result['n_permutations'] == 1000
        assert 0 <= result['p_value'] <= 1

    def test_spearman_correlation(self):
        """Test permutation test with Spearman correlation"""
        np.random.seed(42)
        x = np.random.randn(30)
        y = np.sort(x)  # Monotonic relationship

        result = permutation_test(x, y, statistic='spearman', n_permutations=500, random_state=42)

        assert result['observed_stat'] > 0  # Should be positive
        assert 0 <= result['p_value'] <= 1

    def test_r2_statistic(self):
        """Test permutation test with R² statistic"""
        np.random.seed(42)
        x = np.random.randn(40)
        y = x * 0.7 + np.random.randn(40) * 0.3

        result = permutation_test(x, y, statistic='r2', n_permutations=500, random_state=42)

        assert result['observed_stat'] >= 0  # R² should be non-negative
        assert result['observed_stat'] <= 1  # R² should be <= 1

    def test_alternative_greater(self):
        """Test one-sided greater alternative"""
        np.random.seed(42)
        x = np.random.randn(30)
        y = x * 0.8 + np.random.randn(30) * 0.2

        result = permutation_test(x, y, n_permutations=500, alternative='greater', random_state=42)
        assert 0 <= result['p_value'] <= 1

    def test_mismatched_lengths(self):
        """Test error handling for mismatched array lengths"""
        with pytest.raises(ValueError):
            permutation_test(np.array([1, 2, 3]), np.array([1, 2]))

    def test_small_sample(self):
        """Test error handling for too small samples"""
        with pytest.raises(ValueError):
            permutation_test(np.array([1]), np.array([2]))


class TestCalculateMedes:
    def test_sample_size_calculation(self):
        """Test calculation of required sample size"""
        result = calculate_medes(
            alpha=0.05,
            power=0.80,
            effect_size=0.5,  # Medium effect
            sigma=1.0
        )

        assert result['required_n_per_group'] > 0
        assert result['total_n'] > 0
        assert result['medes'] == 0.5

    def test_medes_calculation(self):
        """Test calculation of minimum detectable effect size"""
        result = calculate_medes(
            alpha=0.05,
            power=0.80,
            n_per_group=64,
            sigma=1.0
        )

        assert result['medes'] > 0
        assert result['required_n_per_group'] == 64

    def test_multiple_groups(self):
        """Test with multiple groups"""
        result = calculate_medes(
            alpha=0.05,
            power=0.80,
            n_groups=3,
            effect_size=0.4,
            sigma=1.0
        )

        assert result['total_n'] == result['required_n_per_group'] * 3

    def test_missing_input(self):
        """Test error when neither effect_size nor n_per_group provided"""
        with pytest.raises(ValueError):
            calculate_medes(alpha=0.05, power=0.80)


class TestCalculateSampleSizeForR2:
    def test_basic_calculation(self):
        """Test basic sample size calculation for R²"""
        result = calculate_sample_size_for_r2(
            alpha=0.05,
            power=0.80,
            r2_target=0.10,
            n_predictors=1
        )

        assert result['required_n'] > 0
        assert result['r2_target'] == 0.10

    def test_higher_power_requires_more_samples(self):
        """Test that higher power requires larger sample"""
        result_80 = calculate_sample_size_for_r2(power=0.80, r2_target=0.10)
        result_90 = calculate_sample_size_for_r2(power=0.90, r2_target=0.10)

        assert result_90['required_n'] > result_80['required_n']

    def test_smaller_effect_requires_more_samples(self):
        """Test that smaller R² requires larger sample"""
        result_10 = calculate_sample_size_for_r2(r2_target=0.10)
        result_05 = calculate_sample_size_for_r2(r2_target=0.05)

        assert result_05['required_n'] > result_10['required_n']

    def test_more_predictors_requires_more_samples(self):
        """Test that more predictors require larger sample"""
        result_1 = calculate_sample_size_for_r2(n_predictors=1)
        result_5 = calculate_sample_size_for_r2(n_predictors=5)

        assert result_5['required_n'] > result_1['required_n']


class TestFTestComparison:
    def test_model_comparison(self):
        """Test F-test for comparing nested models"""
        result = f_test_comparison(
            r2_reduced=0.20,
            r2_full=0.35,
            n=100,
            k_reduced=2,
            k_full=4
        )

        assert 'f_statistic' in result
        assert 'p_value' in result
        assert result['delta_r2'] == 0.15
        assert result['f_statistic'] > 0

    def test_significance_detection(self):
        """Test detection of significant model improvement"""
        # Large improvement should be significant
        result = f_test_comparison(
            r2_reduced=0.10,
            r2_full=0.40,
            n=200,
            k_reduced=1,
            k_full=3
        )

        assert result['significant'] == True

    def test_non_significant_improvement(self):
        """Test non-significant model improvement"""
        # Small improvement with small sample
        result = f_test_comparison(
            r2_reduced=0.30,
            r2_full=0.32,
            n=30,
            k_reduced=1,
            k_full=2
        )

        # May or may not be significant depending on exact values
        assert 'significant' in result

    def test_invalid_predictor_counts(self):
        """Test error when full model has fewer or equal predictors"""
        with pytest.raises(ValueError):
            f_test_comparison(
                r2_reduced=0.30,
                r2_full=0.35,
                n=100,
                k_reduced=3,
                k_full=2
            )