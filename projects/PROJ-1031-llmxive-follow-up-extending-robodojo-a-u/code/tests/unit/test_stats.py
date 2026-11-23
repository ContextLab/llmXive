import pytest
import numpy as np
from scipy import stats
from src.stats_analysis import perform_wilcoxon_test, calculate_rank_biserial_correlation, StatisticalMetrics

class TestWilcoxonImplementation:
    """Unit tests for the Wilcoxon signed-rank test implementation."""

    def test_perform_wilcoxon_test_basic(self):
        """Test basic Wilcoxon test with two identical distributions."""
        # Two identical distributions should yield a statistic of 0 and p-value of 1.0
        group_a = np.array([10.0, 12.0, 15.0, 11.0, 13.0])
        group_b = np.array([10.0, 12.0, 15.0, 11.0, 13.0])

        result = perform_wilcoxon_test(group_a, group_b)

        assert isinstance(result, StatisticalMetrics)
        assert result.statistic == 0.0
        assert result.p_value == 1.0
        assert result.null_hypothesis_rejected is False

    def test_perform_wilcoxon_test_significant_difference(self):
        """Test Wilcoxon test with clearly different distributions."""
        # Create distributions with a clear shift
        group_a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group_b = np.array([10.0, 11.0, 12.0, 13.0, 14.0])

        result = perform_wilcoxon_test(group_a, group_b)

        assert isinstance(result, StatisticalMetrics)
        assert result.statistic >= 0
        assert result.p_value < 0.05  # Should be significant
        assert result.null_hypothesis_rejected is True

    def test_perform_wilcoxon_test_small_sample(self):
        """Test with small sample size (N=3 per group)."""
        group_a = np.array([1.0, 2.0, 3.0])
        group_b = np.array([4.0, 5.0, 6.0])

        result = perform_wilcoxon_test(group_a, group_b)

        assert isinstance(result, StatisticalMetrics)
        assert result.statistic >= 0
        assert 0.0 <= result.p_value <= 1.0
        assert isinstance(result.null_hypothesis_rejected, bool)

    def test_perform_wilcoxon_test_tied_ranks(self):
        """Test handling of tied ranks."""
        # Introduce ties
        group_a = np.array([1.0, 2.0, 2.0, 3.0, 4.0])
        group_b = np.array([2.0, 3.0, 3.0, 4.0, 5.0])

        result = perform_wilcoxon_test(group_a, group_b)

        assert isinstance(result, StatisticalMetrics)
        assert result.statistic >= 0
        assert 0.0 <= result.p_value <= 1.0

    def test_perform_wilcoxon_test_empty_arrays(self):
        """Test behavior with empty input arrays."""
        with pytest.raises(ValueError):
            perform_wilcoxon_test(np.array([]), np.array([]))

    def test_perform_wilcoxon_test_single_element(self):
        """Test behavior with single element arrays."""
        group_a = np.array([1.0])
        group_b = np.array([2.0])

        # SciPy raises an error for single element arrays in wilcoxon
        # Our implementation should handle this gracefully or raise a clear error
        with pytest.raises((ValueError, IndexError)):
            perform_wilcoxon_test(group_a, group_b)

    def test_perform_wilcoxon_test_asymmetric_sample_sizes(self):
        """Test with asymmetric sample sizes (should still work if paired)."""
        # Note: Wilcoxon signed-rank is for paired data, so lengths must match
        group_a = np.array([1.0, 2.0, 3.0, 4.0])
        group_b = np.array([2.0, 3.0, 4.0])

        with pytest.raises(ValueError):
            perform_wilcoxon_test(group_a, group_b)

class TestRankBiserialCorrelation:
    """Unit tests for rank-biserial correlation calculation."""

    def test_rank_biserial_perfect_separation(self):
        """Test rank-biserial with perfect separation (all A < all B)."""
        group_a = np.array([1.0, 2.0, 3.0])
        group_b = np.array([4.0, 5.0, 6.0])

        result = calculate_rank_biserial_correlation(group_a, group_b)

        # Perfect separation should yield a correlation close to 1.0 (or -1.0 depending on direction)
        assert isinstance(result, float)
        assert -1.0 <= result <= 1.0
        # With A < B, we expect a negative correlation if we treat A as the first group
        # The exact sign depends on implementation, but magnitude should be high
        assert abs(result) > 0.8

    def test_rank_biserial_no_separation(self):
        """Test rank-biserial with identical distributions."""
        group_a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group_b = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        result = calculate_rank_biserial_correlation(group_a, group_b)

        # No separation should yield correlation close to 0
        assert isinstance(result, float)
        assert abs(result) < 0.1

    def test_rank_biserial_moderate_separation(self):
        """Test rank-biserial with moderate separation."""
        group_a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group_b = np.array([3.0, 4.0, 5.0, 6.0, 7.0])

        result = calculate_rank_biserial_correlation(group_a, group_b)

        assert isinstance(result, float)
        assert -1.0 <= result <= 1.0
        # Should show some separation
        assert abs(result) > 0.2

    def test_rank_biserial_with_ties(self):
        """Test rank-biserial with tied values."""
        group_a = np.array([1.0, 2.0, 2.0, 3.0])
        group_b = np.array([2.0, 3.0, 3.0, 4.0])

        result = calculate_rank_biserial_correlation(group_a, group_b)

        assert isinstance(result, float)
        assert -1.0 <= result <= 1.0

    def test_rank_biserial_single_element(self):
        """Test rank-biserial with single element groups."""
        group_a = np.array([1.0])
        group_b = np.array([2.0])

        result = calculate_rank_biserial_correlation(group_a, group_b)

        assert isinstance(result, float)
        # With perfect separation of 1 vs 1, should be extreme
        assert abs(result) == 1.0 or abs(result) > 0.9

    def test_rank_biserial_invalid_input(self):
        """Test rank-biserial with empty arrays."""
        with pytest.raises(ValueError):
            calculate_rank_biserial_correlation(np.array([]), np.array([]))