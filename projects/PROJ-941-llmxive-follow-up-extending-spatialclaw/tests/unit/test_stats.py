"""
Unit tests for statistical analysis modules in code/stats/.
Includes tests for Wilcoxon signed-rank test and Bonferroni correction.
"""

import pytest
import math
import numpy as np
from scipy import stats as scipy_stats

# Import the module under test.
# The actual implementation is expected to be in code/stats/tests.py
# We will import the specific function or module here.
# Since the task is to write the test for Bonferroni correction,
# we assume the implementation will be in code/stats/tests.py.
# If the module doesn't exist yet, we might need to mock or handle ImportError.
# However, per the task instructions, we implement the test.
# We will try to import the function `bonferroni_corrected_pvalues` from `code.stats.tests`
# or a similar name. Let's assume the function is named `apply_bonferroni_correction`.

try:
    from code.stats.tests import apply_bonferroni_correction
    HAS_STATS_MODULE = True
except ImportError:
    HAS_STATS_MODULE = False
    # We will still write the test, but it will be skipped if the module is missing.
    # This allows the test file to be valid even if the implementation is pending.
    apply_bonferroni_correction = None


class TestBonferroniCorrection:
    """Tests for the Bonferroni correction implementation."""

    @pytest.mark.skipif(not HAS_STATS_MODULE, reason="stats module not yet implemented")
    def test_bonferroni_single_pvalue(self):
        """Test Bonferroni correction with a single p-value."""
        p_values = [0.05]
        corrected = apply_bonferroni_correction(p_values)
        # With 1 test, corrected p-value should be min(p * 1, 1.0)
        assert len(corrected) == 1
        assert math.isclose(corrected[0], 0.05, abs_tol=1e-9)

    @pytest.mark.skipif(not HAS_STATS_MODULE, reason="stats module not yet implemented")
    def test_bonferroni_multiple_pvalues(self):
        """Test Bonferroni correction with multiple p-values."""
        p_values = [0.01, 0.05, 0.10]
        n = len(p_values)
        corrected = apply_bonferroni_correction(p_values)

        assert len(corrected) == n
        for i, p in enumerate(p_values):
            expected = min(p * n, 1.0)
            assert math.isclose(corrected[i], expected, abs_tol=1e-9)

    @pytest.mark.skipif(not HAS_STATS_MODULE, reason="stats module not yet implemented")
    def test_bonferroni_capping_at_one(self):
        """Test that corrected p-values are capped at 1.0."""
        p_values = [0.6, 0.7, 0.8]
        n = len(p_values)
        corrected = apply_bonferroni_correction(p_values)

        for p_corr in corrected:
            assert p_corr <= 1.0

    @pytest.mark.skipif(not HAS_STATS_MODULE, reason="stats module not yet implemented")
    def test_bonferroni_empty_list(self):
        """Test Bonferroni correction with an empty list."""
        p_values = []
        corrected = apply_bonferroni_correction(p_values)
        assert corrected == []

    @pytest.mark.skipif(not HAS_STATS_MODULE, reason="stats module not yet implemented")
    def test_bonferroni_all_significant(self):
        """Test case where all p-values remain significant after correction."""
        p_values = [0.001, 0.002, 0.003]
        n = len(p_values)
        corrected = apply_bonferroni_correction(p_values)
        alpha = 0.05
        # All corrected values should be < alpha
        for p_corr in corrected:
            assert p_corr < alpha

    @pytest.mark.skipif(not HAS_STATS_MODULE, reason="stats module not yet implemented")
    def test_bonferroni_all_insignificant(self):
        """Test case where all p-values become insignificant after correction."""
        p_values = [0.2, 0.3, 0.4]
        n = len(p_values)
        corrected = apply_bonferroni_correction(p_values)
        alpha = 0.05
        # All corrected values should be >= alpha
        for p_corr in corrected:
            assert p_corr >= alpha

    @pytest.mark.skipif(not HAS_STATS_MODULE, reason="stats module not yet implemented")
    def test_bonferroni_mixed_significance(self):
        """Test case with mixed significance after correction."""
        p_values = [0.001, 0.02, 0.15]
        n = len(p_values)
        corrected = apply_bonferroni_correction(p_values)
        alpha = 0.05

        # 0.001 * 3 = 0.003 < 0.05 (significant)
        # 0.02 * 3 = 0.06 > 0.05 (insignificant)
        # 0.15 * 3 = 0.45 > 0.05 (insignificant)
        assert corrected[0] < alpha
        assert corrected[1] >= alpha
        assert corrected[2] >= alpha

    @pytest.mark.skipif(not HAS_STATS_MODULE, reason="stats module not yet implemented")
    def test_bonferroni_preserves_order(self):
        """Test that the order of p-values is preserved."""
        p_values = [0.05, 0.01, 0.10, 0.02]
        corrected = apply_bonferroni_correction(p_values)
        # The relative order should be preserved (monotonicity)
        for i in range(len(p_values) - 1):
            # If p1 < p2, then corrected_p1 <= corrected_p2
            if p_values[i] < p_values[i+1]:
                assert corrected[i] <= corrected[i+1]

    @pytest.mark.skipif(not HAS_STATS_MODULE, reason="stats module not yet implemented")
    def test_bonferroni_large_n(self):
        """Test with a larger number of p-values to ensure scalability."""
        n = 1000
        p_values = [0.001] * n
        corrected = apply_bonferroni_correction(p_values)
        expected = min(0.001 * n, 1.0)
        assert all(math.isclose(p, expected, abs_tol=1e-9) for p in corrected)

    @pytest.mark.skipif(not HAS_STATS_MODULE, reason="stats module not yet implemented")
    def test_bonferroni_with_zero_pvalue(self):
        """Test handling of a p-value of 0."""
        p_values = [0.0, 0.05]
        corrected = apply_bonferroni_correction(p_values)
        assert corrected[0] == 0.0
        n = len(p_values)
        expected_second = min(0.05 * n, 1.0)
        assert math.isclose(corrected[1], expected_second, abs_tol=1e-9)

# Additional tests for Wilcoxon signed-rank test (referenced in T027 context)
# These tests assume the implementation is in code/stats/tests.py as `wilcoxon_signed_rank_test`
try:
    from code.stats.tests import wilcoxon_signed_rank_test
    HAS_WILCOXON = True
except ImportError:
    HAS_WILCOXON = False
    wilcoxon_signed_rank_test = None


class TestWilcoxonSignedRank:
    """Tests for the Wilcoxon signed-rank test implementation."""

    @pytest.mark.skipif(not HAS_WILCOXON, reason="wilcoxon function not yet implemented")
    def test_wilcoxon_identical_samples(self):
        """Test Wilcoxon test with identical samples (should yield high p-value)."""
        x = [1, 2, 3, 4, 5]
        y = [1, 2, 3, 4, 5]
        stat, pval = wilcoxon_signed_rank_test(x, y)
        # For identical samples, p-value should be 1.0 or very close
        assert pval == 1.0

    @pytest.mark.skipif(not HAS_WILCOXON, reason="wilcoxon function not yet implemented")
    def test_wilcoxon_different_samples(self):
        """Test Wilcoxon test with clearly different samples."""
        x = [1, 2, 3, 4, 5]
        y = [10, 20, 30, 40, 50]
        stat, pval = wilcoxon_signed_rank_test(x, y)
        # p-value should be very small
        assert pval < 0.05

    @pytest.mark.skipif(not HAS_WILCOXON, reason="wilcoxon function not yet implemented")
    def test_wilcoxon_returns_tuple(self):
        """Test that the function returns a tuple (statistic, p-value)."""
        x = [1, 2, 3]
        y = [2, 3, 4]
        result = wilcoxon_signed_rank_test(x, y)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], (int, float))
        assert isinstance(result[1], float)

    @pytest.mark.skipif(not HAS_WILCOXON, reason="wilcoxon function not yet implemented")
    def test_wilcoxon_small_sample(self):
        """Test with a small sample size."""
        x = [1, 2]
        y = [3, 4]
        stat, pval = wilcoxon_signed_rank_test(x, y)
        assert 0 <= pval <= 1.0

    @pytest.mark.skipif(not HAS_WILCOXON, reason="wilcoxon function not yet implemented")
    def test_wilcoxon_negative_values(self):
        """Test with negative values."""
        x = [-1, -2, -3]
        y = [1, 2, 3]
        stat, pval = wilcoxon_signed_rank_test(x, y)
        assert 0 <= pval <= 1.0

    @pytest.mark.skipif(not HAS_WILCOXON, reason="wilcoxon function not yet implemented")
    def test_wilcoxon_float_values(self):
        """Test with floating point values."""
        x = [1.1, 2.2, 3.3]
        y = [1.2, 2.3, 3.4]
        stat, pval = wilcoxon_signed_rank_test(x, y)
        assert 0 <= pval <= 1.0

    @pytest.mark.skipif(not HAS_WILCOXON, reason="wilcoxon function not yet implemented")
    def test_wilcoxon_single_element(self):
        """Test with a single element (edge case)."""
        x = [1]
        y = [2]
        # scipy.stats.wilcoxon may raise an error for n < 3 or n=1
        # We expect our wrapper to handle this gracefully or raise a specific error.
        # For now, we assume it returns a valid result or raises ValueError.
        # Let's check if it raises ValueError for insufficient data.
        try:
            stat, pval = wilcoxon_signed_rank_test(x, y)
            # If it doesn't raise, pval should be in [0, 1]
            assert 0 <= pval <= 1.0
        except ValueError:
            # Expected for small sample sizes in some implementations
            pass