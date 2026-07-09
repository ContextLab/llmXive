"""
Unit tests for Kolmogorov-Smirnov (KS) test calculation logic.
This module validates the statistical association analysis for US2.
"""
import pytest
import numpy as np
from scipy import stats
import sys
from pathlib import Path

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis import calculate_ks_statistic, perform_kstest_two_sample


class TestKSCalculation:
    """Tests for the KS statistic calculation functions."""

    def test_ks_statistic_identical_distributions(self):
        """
        Test that KS statistic is near zero for identical distributions.
        """
        np.random.seed(42)
        sample1 = np.random.normal(0, 1, 1000)
        sample2 = np.random.normal(0, 1, 1000)

        stat, p_val = calculate_ks_statistic(sample1, sample2)

        # For identical distributions, D statistic should be very small
        assert stat < 0.1, f"KS statistic {stat} is too high for identical distributions"
        assert p_val > 0.05, "P-value should be high for identical distributions"

    def test_ks_statistic_different_means(self):
        """
        Test that KS statistic is significant for distributions with different means.
        """
        np.random.seed(42)
        sample1 = np.random.normal(0, 1, 1000)
        sample2 = np.random.normal(2, 1, 1000)  # Different mean

        stat, p_val = calculate_ks_statistic(sample1, sample2)

        # For significantly different means, D statistic should be larger
        assert stat > 0.3, f"KS statistic {stat} is too low for different means"
        assert p_val < 0.05, "P-value should be low for significantly different means"

    def test_ks_statistic_different_variances(self):
        """
        Test that KS statistic detects difference in variances.
        """
        np.random.seed(42)
        sample1 = np.random.normal(0, 1, 1000)
        sample2 = np.random.normal(0, 2, 1000)  # Different variance

        stat, p_val = calculate_ks_statistic(sample1, sample2)

        # Different variances should result in a significant KS test
        assert p_val < 0.05, "P-value should be low for different variances"

    def test_ks_statistic_small_samples(self):
        """
        Test KS statistic with small sample sizes.
        """
        np.random.seed(42)
        sample1 = np.random.normal(0, 1, 20)
        sample2 = np.random.normal(0.5, 1, 20)

        stat, p_val = calculate_ks_statistic(sample1, sample2)

        # Should return valid statistics even with small samples
        assert 0 <= stat <= 1, "KS statistic must be between 0 and 1"
        assert 0 <= p_val <= 1, "P-value must be between 0 and 1"

    def test_ks_statistic_empty_arrays(self):
        """
        Test that KS statistic handles empty arrays gracefully.
        """
        sample1 = np.array([])
        sample2 = np.array([1, 2, 3])

        with pytest.raises(ValueError):
            calculate_ks_statistic(sample1, sample2)

    def test_ks_statistic_single_element(self):
        """
        Test KS statistic with single element arrays.
        """
        sample1 = np.array([1.0])
        sample2 = np.array([2.0])

        # scipy.stats.ks_2samp handles single elements but may return NaN or specific values
        # We just verify it doesn't crash and returns valid floats
        stat, p_val = calculate_ks_statistic(sample1, sample2)
        assert isinstance(stat, float), "Statistic should be a float"
        assert isinstance(p_val, float), "P-value should be a float"

    def test_ks_statistic_nan_handling(self):
        """
        Test that KS statistic handles arrays with NaN values.
        """
        sample1 = np.array([1.0, 2.0, np.nan, 3.0])
        sample2 = np.array([1.5, 2.5, 3.5])

        # The function should either raise an error or handle NaNs
        # Based on typical implementation, we expect it to handle or raise
        with pytest.raises((ValueError, RuntimeWarning)):
            calculate_ks_statistic(sample1, sample2)

    def test_ks_statistic_matches_scipy(self):
        """
        Verify our implementation matches scipy's ks_2samp.
        """
        np.random.seed(123)
        sample1 = np.random.normal(0, 1, 500)
        sample2 = np.random.normal(0.5, 1, 500)

        our_stat, our_pval = calculate_ks_statistic(sample1, sample2)
        scipy_stat, scipy_pval = stats.ks_2samp(sample1, sample2)

        np.testing.assert_almost_equal(our_stat, scipy_stat, decimal=10)
        np.testing.assert_almost_equal(our_pval, scipy_pval, decimal=10)


class TestPerformKSTestTwoSample:
    """Tests for the wrapper function perform_kstest_two_sample."""

    def test_returns_dict_structure(self):
        """
        Test that the function returns a dictionary with expected keys.
        """
        np.random.seed(42)
        sample1 = np.random.normal(0, 1, 100)
        sample2 = np.random.normal(0.5, 1, 100)

        result = perform_kstest_two_sample(sample1, sample2)

        assert isinstance(result, dict), "Result should be a dictionary"
        assert "statistic" in result, "Result should contain 'statistic'"
        assert "pvalue" in result, "Result should contain 'pvalue'"
        assert "significant" in result, "Result should contain 'significant'"
        assert "alpha" in result, "Result should contain 'alpha'"

    def test_significance_flag(self):
        """
        Test that the significance flag is correctly set based on p-value.
        """
        np.random.seed(42)
        # Different distributions
        sample1 = np.random.normal(0, 1, 1000)
        sample2 = np.random.normal(3, 1, 1000)

        result = perform_kstest_two_sample(sample1, sample2, alpha=0.05)

        assert result["significant"] is True, "Should be significant for different distributions"
        assert result["pvalue"] < 0.05, "P-value should be < 0.05"

        # Similar distributions
        sample3 = np.random.normal(0, 1, 1000)
        sample4 = np.random.normal(0.1, 1, 1000)

        result2 = perform_kstest_two_sample(sample3, sample4, alpha=0.05)

        assert result2["significant"] is False, "Should not be significant for similar distributions"
        assert result2["pvalue"] >= 0.05, "P-value should be >= 0.05"

    def test_custom_alpha(self):
        """
        Test that custom alpha parameter affects significance flag.
        """
        np.random.seed(42)
        sample1 = np.random.normal(0, 1, 100)
        sample2 = np.random.normal(0.3, 1, 100)

        # With alpha=0.05, might not be significant
        result1 = perform_kstest_two_sample(sample1, sample2, alpha=0.05)

        # With alpha=0.10, might be significant
        result2 = perform_kstest_two_sample(sample1, sample2, alpha=0.10)

        # The p-value is fixed, so changing alpha changes the significance flag
        assert result1["pvalue"] == result2["pvalue"], "P-value should be same"
        # One might be significant, the other not, depending on the p-value
        if result1["significant"] != result2["significant"]:
            assert (result1["pvalue"] < 0.10) and (result1["pvalue"] >= 0.05)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])