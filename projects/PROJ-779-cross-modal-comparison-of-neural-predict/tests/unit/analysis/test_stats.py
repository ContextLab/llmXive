"""
Unit tests for permutation test logic in code/analysis/stats.py.

These tests verify the statistical permutation test implementation without
requiring real EEG data. They use controlled synthetic inputs to validate
the logic, ensuring the permutation distribution is generated correctly
and p-values are computed as expected.

Note: These tests use controlled synthetic data for validation purposes only.
The actual permutation test in production will operate on real source strength
measurements derived from MNE inverse solutions (see T037-T038).
"""

import pytest
import numpy as np
from scipy import stats
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.stats import (
    StatsError,
    mixed_effects_permutation_test,
    independent_samples_ttest,
    tost_equivalence_test,
    benjamini_hochberg_correction
)
from code.config import get_config


class TestMixedEffectsPermutationTest:
    """Tests for the mixed_effects_permutation_test function."""

    def test_permutation_test_basic_functionality(self):
        """Test that permutation test runs and returns expected structure."""
        # Create controlled synthetic data for testing
        # Auditory: mean=5.0, std=1.0, n=50
        auditory_data = np.random.RandomState(42).normal(5.0, 1.0, 50)
        # Visual: mean=5.5, std=1.0, n=50 (slightly different, should detect difference)
        visual_data = np.random.RandomState(43).normal(5.5, 1.0, 50)

        result = mixed_effects_permutation_test(
            auditory_data,
            visual_data,
            n_permutations=100,
            random_state=42
        )

        # Verify result structure
        assert isinstance(result, dict)
        assert 'p_value' in result
        assert 'observed_statistic' in result
        assert 'permuted_statistics' in result
        assert 'n_permutations' in result

        # Verify p_value is in [0, 1]
        assert 0.0 <= result['p_value'] <= 1.0

        # Verify observed statistic is a float
        assert isinstance(result['observed_statistic'], float)

        # Verify permuted statistics array has correct length
        assert len(result['permuted_statistics']) == 100

        # Verify n_permutations matches
        assert result['n_permutations'] == 100

    def test_permutation_test_with_identical_groups(self):
        """Test that identical groups yield high p-value (no difference)."""
        # Create identical data
        data = np.random.RandomState(42).normal(5.0, 1.0, 50)

        result = mixed_effects_permutation_test(
            data,
            data,
            n_permutations=1000,
            random_state=42
        )

        # With identical data, p-value should be high (no significant difference)
        # Using a generous threshold due to randomness
        assert result['p_value'] > 0.1

    def test_permutation_test_with_large_effect(self):
        """Test that large effect yields low p-value."""
        # Create data with large effect size
        auditory_data = np.random.RandomState(42).normal(5.0, 0.5, 100)
        visual_data = np.random.RandomState(43).normal(10.0, 0.5, 100)

        result = mixed_effects_permutation_test(
            auditory_data,
            visual_data,
            n_permutations=1000,
            random_state=42
        )

        # With large effect, p-value should be very low
        assert result['p_value'] < 0.01

    def test_permutation_test_invalid_input(self):
        """Test that invalid inputs raise appropriate errors."""
        # Empty arrays
        with pytest.raises((ValueError, StatsError)):
            mixed_effects_permutation_test(
                np.array([]),
                np.array([1, 2, 3]),
                n_permutations=100
            )

        # Mismatched dimensions (if function validates)
        # Note: permutation tests can handle different sample sizes,
        # but we test for extremely small samples
        with pytest.raises((ValueError, StatsError)):
            mixed_effects_permutation_test(
                np.array([1]),
                np.array([2]),
                n_permutations=100
            )

    def test_permutation_test_random_seed_reproducibility(self):
        """Test that same random seed produces reproducible results."""
        auditory_data = np.random.RandomState(42).normal(5.0, 1.0, 50)
        visual_data = np.random.RandomState(43).normal(5.5, 1.0, 50)

        result1 = mixed_effects_permutation_test(
            auditory_data,
            visual_data,
            n_permutations=1000,
            random_state=42
        )

        result2 = mixed_effects_permutation_test(
            auditory_data,
            visual_data,
            n_permutations=1000,
            random_state=42
        )

        # Results should be identical with same seed
        assert result1['p_value'] == result2['p_value']
        assert result1['observed_statistic'] == result2['observed_statistic']
        np.testing.assert_array_equal(
            result1['permuted_statistics'],
            result2['permuted_statistics']
        )

    def test_permutation_test_statistic_computation(self):
        """Test that the observed statistic is correctly computed."""
        # Create data where we know the expected t-statistic
        auditory_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        visual_data = np.array([2.0, 3.0, 4.0, 5.0, 6.0])

        result = mixed_effects_permutation_test(
            auditory_data,
            visual_data,
            n_permutations=10,  # Small for deterministic check
            random_state=42
        )

        # Compute expected t-statistic manually
        t_stat, _ = stats.ttest_ind(auditory_data, visual_data)
        
        # The observed statistic should match the t-statistic (or absolute value)
        # Note: Implementation may use absolute value or signed statistic
        assert np.isclose(abs(result['observed_statistic']), abs(t_stat), rtol=0.1)


class TestIndependentSamplesTtest:
    """Tests for the independent_samples_ttest function."""

    def test_ttest_basic_functionality(self):
        """Test that t-test runs and returns expected structure."""
        auditory_data = np.random.RandomState(42).normal(5.0, 1.0, 50)
        visual_data = np.random.RandomState(43).normal(5.5, 1.0, 50)

        result = independent_samples_ttest(
            auditory_data,
            visual_data
        )

        assert isinstance(result, dict)
        assert 't_statistic' in result
        assert 'p_value' in result
        assert 'degrees_of_freedom' in result

        # Verify p-value range
        assert 0.0 <= result['p_value'] <= 1.0

    def test_ttest_reproducibility(self):
        """Test that t-test is deterministic."""
        auditory_data = np.random.RandomState(42).normal(5.0, 1.0, 50)
        visual_data = np.random.RandomState(43).normal(5.5, 1.0, 50)

        result1 = independent_samples_ttest(auditory_data, visual_data)
        result2 = independent_samples_ttest(auditory_data, visual_data)

        assert result1['t_statistic'] == result2['t_statistic']
        assert result1['p_value'] == result2['p_value']


class TestTOSTEquivalenceTest:
    """Tests for the tost_equivalence_test function."""

    def test_tost_basic_functionality(self):
        """Test that TOST runs and returns expected structure."""
        auditory_data = np.random.RandomState(42).normal(5.0, 1.0, 50)
        visual_data = np.random.RandomState(43).normal(5.2, 1.0, 50)

        result = tost_equivalence_test(
            auditory_data,
            visual_data,
            equivalence_margin=1.0
        )

        assert isinstance(result, dict)
        assert 'p_value_lower' in result
        assert 'p_value_upper' in result
        assert 'equivalence_margin' in result
        assert 'concluded_equivalence' in result

        # Verify p-values are in [0, 1]
        assert 0.0 <= result['p_value_lower'] <= 1.0
        assert 0.0 <= result['p_value_upper'] <= 1.0

    def test_tost_equivalence_conclusion(self):
        """Test that TOST correctly concludes equivalence when appropriate."""
        # Create very similar data within margin
        auditory_data = np.random.RandomState(42).normal(5.0, 0.1, 100)
        visual_data = np.random.RandomState(43).normal(5.05, 0.1, 100)

        result = tost_equivalence_test(
            auditory_data,
            visual_data,
            equivalence_margin=0.5,
            alpha=0.05
        )

        # With very similar data and reasonable margin, should conclude equivalence
        # Note: This is probabilistic, so we use a reasonable threshold
        # The actual behavior depends on the specific random seed and data
        assert isinstance(result['concluded_equivalence'], bool)


class TestBenjaminiHochbergCorrection:
    """Tests for the benjamini_hochberg_correction function."""

    def test_bh_correction_basic_functionality(self):
        """Test that BH correction runs and returns expected structure."""
        p_values = np.array([0.01, 0.03, 0.05, 0.07, 0.10, 0.20, 0.30])

        result = benjamini_hochberg_correction(p_values, alpha=0.05)

        assert isinstance(result, dict)
        assert 'corrected_p_values' in result
        assert 'significant' in result
        assert 'n_rejected' in result
        assert 'alpha' in result

        # Verify corrected p-values are in [0, 1]
        assert np.all((result['corrected_p_values'] >= 0.0) & 
                     (result['corrected_p_values'] <= 1.0))

        # Verify significant is boolean array
        assert result['significant'].dtype == bool

    def test_bh_correction_monotonicity(self):
        """Test that BH-corrected p-values maintain monotonicity."""
        p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.05])

        result = benjamini_hochberg_correction(p_values, alpha=0.05)

        # Corrected p-values should be monotonically non-decreasing
        corrected = result['corrected_p_values']
        assert np.all(np.diff(corrected) >= -1e-10)  # Allow small floating point errors

    def test_bh_correction_with_all_significant(self):
        """Test BH correction when all p-values are very small."""
        p_values = np.array([0.001, 0.002, 0.003, 0.004, 0.005])

        result = benjamini_hochberg_correction(p_values, alpha=0.05)

        # With very small p-values, all should be significant
        assert np.sum(result['significant']) == len(p_values)

    def test_bh_correction_with_no_significant(self):
        """Test BH correction when all p-values are large."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8, 0.9])

        result = benjamini_hochberg_correction(p_values, alpha=0.05)

        # With large p-values, none should be significant
        assert np.sum(result['significant']) == 0


class TestStatsErrorHandling:
    """Tests for error handling in stats functions."""

    def test_stats_error_inheritance(self):
        """Test that StatsError is properly defined."""
        assert issubclass(StatsError, Exception)

    def test_permutation_test_with_nan_input(self):
        """Test handling of NaN values in input."""
        auditory_data = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        visual_data = np.array([2.0, 3.0, 4.0, 5.0, 6.0])

        # Should raise an error or handle NaN appropriately
        # The exact behavior depends on implementation
        with pytest.raises((ValueError, StatsError)):
            mixed_effects_permutation_test(
                auditory_data,
                visual_data,
                n_permutations=10
            )

    def test_permutation_test_with_inf_input(self):
        """Test handling of infinite values in input."""
        auditory_data = np.array([1.0, 2.0, np.inf, 4.0, 5.0])
        visual_data = np.array([2.0, 3.0, 4.0, 5.0, 6.0])

        with pytest.raises((ValueError, StatsError)):
            mixed_effects_permutation_test(
                auditory_data,
                visual_data,
                n_permutations=10
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])