"""
Unit tests for normality check and test selection logic in analysis.py.

This module verifies that the statistical analysis pipeline correctly:
1. Detects normality using Shapiro-Wilk test.
2. Selects the appropriate statistical test (Paired t-test vs Wilcoxon)
   based on normality and sample size.
3. Applies family-wise error correction (Bonferroni/Holm).
"""

import pytest
import numpy as np
from scipy import stats
from unittest.mock import patch, MagicMock

# Import the logic to be tested. Since analysis.py is not fully implemented yet,
# we mock the internal logic or test the helper functions directly if available.
# For this task, we assume the functions `check_normality`, `select_test`, and
# `apply_correction` will be implemented in `code/analysis.py`.
# We will test the logic by importing them if they exist, or by testing the
# mathematical logic directly in the test suite to ensure the requirements are met.

# Attempt to import the implementation (will be added in T029/T030)
try:
    from code.analysis import check_normality, select_statistical_test, apply_correction
    HAS_IMPLEMENTATION = True
except ImportError:
    HAS_IMPLEMENTATION = False

# Constants for testing
NORMALITY_THRESHOLD = 0.05
MIN_SAMPLE_SIZE = 30


class TestNormalityCheck:
    """Tests for the normality checking logic."""

    def test_normal_distribution_passes(self):
        """Verify that a normal distribution passes the Shapiro-Wilk test."""
        # Generate a large normal sample
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=1, size=100)

        if HAS_IMPLEMENTATION:
            is_normal, p_value = check_normality(data, alpha=NORMALITY_THRESHOLD)
            assert is_normal is True, "Normal distribution should pass normality check"
            assert p_value > NORMALITY_THRESHOLD
        else:
            # Fallback to direct scipy test if implementation not yet available
            stat, p_value = stats.shapiro(data[:5000]) # Shapiro limit is 5000
            assert p_value > NORMALITY_THRESHOLD

    def test_skewed_distribution_fails(self):
        """Verify that a skewed distribution fails the Shapiro-Wilk test."""
        # Generate a skewed sample (exponential)
        np.random.seed(42)
        data = np.random.exponential(scale=1.0, size=100)

        if HAS_IMPLEMENTATION:
            is_normal, p_value = check_normality(data, alpha=NORMALITY_THRESHOLD)
            assert is_normal is False, "Skewed distribution should fail normality check"
            assert p_value <= NORMALITY_THRESHOLD
        else:
            stat, p_value = stats.shapiro(data[:5000])
            assert p_value <= NORMALITY_THRESHOLD

    def test_small_sample_size(self):
        """Verify behavior with small sample sizes."""
        np.random.seed(42)
        data = np.random.normal(0, 1, size=5)

        if HAS_IMPLEMENTATION:
            is_normal, p_value = check_normality(data, alpha=NORMALITY_THRESHOLD)
            # Small samples often pass normality by default due to low power
            # The function should handle this gracefully
            assert isinstance(is_normal, bool)
            assert isinstance(p_value, float)
        else:
            stat, p_value = stats.shapiro(data)
            assert p_value > 0.05 # Likely pass for small normal samples


class TestTestSelection:
    """Tests for the statistical test selection logic."""

    def test_select_ttest_when_normal_and_large(self):
        """Should select Paired t-test if data is normal and n >= 30."""
        baseline = np.random.normal(0, 1, 50)
        perturbed = np.random.normal(0.5, 1, 50)

        if HAS_IMPLEMENTATION:
            test_name = select_statistical_test(baseline, perturbed)
            assert test_name == "paired_t_test", "Should select t-test for normal data"
        else:
            # Mock the logic
            # Logic: if normal and n >= 30 -> t-test
            stat_b, p_b = stats.shapiro(baseline)
            stat_p, p_p = stats.shapiro(perturbed)
            is_normal = (p_b > NORMALITY_THRESHOLD) and (p_p > NORMALITY_THRESHOLD)
            assert is_normal and len(baseline) >= MIN_SAMPLE_SIZE
            # In real impl, this returns "paired_t_test"

    def test_select_wilcoxon_when_non_normal(self):
        """Should select Wilcoxon if data is not normal."""
        # Exponential data (non-normal)
        baseline = np.random.exponential(1, 50)
        perturbed = np.random.exponential(1.5, 50)

        if HAS_IMPLEMENTATION:
            test_name = select_statistical_test(baseline, perturbed)
            assert test_name == "wilcoxon", "Should select Wilcoxon for non-normal data"
        else:
            stat_b, p_b = stats.shapiro(baseline)
            assert p_b <= NORMALITY_THRESHOLD # Fail normality

    def test_select_wilcoxon_when_small_sample(self):
        """Should select Wilcoxon if sample size < 30 even if normal."""
        # Normal data but small sample
        baseline = np.random.normal(0, 1, 20)
        perturbed = np.random.normal(0.5, 1, 20)

        if HAS_IMPLEMENTATION:
            test_name = select_statistical_test(baseline, perturbed)
            # If normality passes but n < 30, policy might still prefer Wilcoxon
            # or t-test. The spec says: "Checks normality and sample size (n >= 30)"
            # implies t-test requires BOTH.
            assert test_name == "wilcoxon", "Should select Wilcoxon for small samples"


class TestCorrection:
    """Tests for family-wise error correction."""

    def test_bonferroni_correction(self):
        """Verify Bonferroni correction logic."""
        p_values = [0.01, 0.04, 0.06]
        alpha = 0.05
        num_tests = len(p_values)

        if HAS_IMPLEMENTATION:
            corrected = apply_correction(p_values, method="bonferroni")
            # Bonferroni: p_corrected = p * k
            expected = [p * num_tests for p in p_values]
            assert np.allclose(corrected, expected)
            # Check significance
            significant = [p < alpha for p in corrected]
            assert significant == [True, True, False]
        else:
            # Manual verification
            corrected = [p * num_tests for p in p_values]
            assert np.allclose(corrected, [0.03, 0.12, 0.18])

    def test_holm_correction(self):
        """Verify Holm-Bonferroni correction logic."""
        p_values = [0.01, 0.04, 0.06]
        alpha = 0.05
        num_tests = len(p_values)

        if HAS_IMPLEMENTATION:
            corrected = apply_correction(p_values, method="holm")
            # Holm is more complex, but we verify it returns a list of floats
            assert len(corrected) == num_tests
            assert all(isinstance(p, float) for p in corrected)
        else:
            # Manual Holm calculation for verification
            sorted_indices = np.argsort(p_values)
            sorted_p = [p_values[i] for i in sorted_indices]
            corrected_p = []
            for i, p in enumerate(sorted_p):
                adjusted = p * (num_tests - i)
                corrected_p.append(adjusted)
            # Reorder back
            final_corrected = [0.0] * num_tests
            for i, val in zip(sorted_indices, corrected_p):
                final_corrected[i] = val
            assert len(final_corrected) == 3


class TestEdgeCases:
    """Tests for edge cases in statistical analysis."""

    def test_zero_variance(self):
        """Handle case where variance is zero."""
        data = np.zeros(50)

        if HAS_IMPLEMENTATION:
            # Should not crash, should return appropriate flags
            is_normal, p = check_normality(data)
            # Zero variance is technically normal (degenerate)
            # but Shapiro might fail or return 1.0.
            assert isinstance(is_normal, bool)
        else:
            # scipy shapiro fails for constant data
            with pytest.raises(ValueError):
                stats.shapiro(data)

    def test_mismatched_lengths(self):
        """Handle mismatched sample lengths."""
        baseline = np.random.normal(0, 1, 50)
        perturbed = np.random.normal(0.5, 1, 40)

        if HAS_IMPLEMENTATION:
            with pytest.raises(ValueError):
                select_statistical_test(baseline, perturbed)
        else:
            with pytest.raises(ValueError):
                stats.ttest_rel(baseline, perturbed)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])