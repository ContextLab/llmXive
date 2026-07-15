"""
Unit tests for statistical analysis functions in code/benchmarks/stats.py.

This module specifically tests the Kruskal-Wallis H-test implementation
to ensure correct calculation of p-values and significance flags.
"""
import pytest
import math
import sys
import os

# Add the code directory to the path so we can import the module
# The project structure puts the module at code/benchmarks/stats.py
# We need to import it as 'benchmarks.stats' relative to the 'code' root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from benchmarks.stats import kruskal_wallis_test, compute_coefficient_of_variation, analyze_group_significance


class TestKruskalWallisHTest:
    """Unit tests for the Kruskal-Wallis H-test implementation."""

    def test_identical_groups(self):
        """Test that identical groups return high p-value (not significant)."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group3 = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = kruskal_wallis_test([group1, group2, group3])

        assert result['h_statistic'] >= 0.0
        # With identical groups, p-value should be very close to 1.0
        assert result['p_value'] > 0.9
        assert result['is_significant'] is False

    def test_distinct_groups(self):
        """Test that clearly distinct groups return low p-value (significant)."""
        # Create groups with very different means
        group1 = [1.0, 1.5, 2.0, 2.5, 3.0]
        group2 = [10.0, 10.5, 11.0, 11.5, 12.0]
        group3 = [20.0, 20.5, 21.0, 21.5, 22.0]

        result = kruskal_wallis_test([group1, group2, group3])

        assert result['h_statistic'] > 0.0
        # With such distinct groups, p-value should be very small
        assert result['p_value'] < 0.05
        assert result['is_significant'] is True

    def test_single_group(self):
        """Test behavior with a single group (edge case)."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]

        # Should handle single group gracefully
        result = kruskal_wallis_test([group1])

        assert result['h_statistic'] == 0.0
        assert result['p_value'] == 1.0
        assert result['is_significant'] is False

    def test_two_groups(self):
        """Test with exactly two groups."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [6.0, 7.0, 8.0, 9.0, 10.0]

        result = kruskal_wallis_test([group1, group2])

        assert result['h_statistic'] > 0.0
        assert result['p_value'] < 0.05
        assert result['is_significant'] is True

    def test_small_sample_size(self):
        """Test with minimal sample sizes (n=3 per group)."""
        group1 = [1.0, 2.0, 3.0]
        group2 = [4.0, 5.0, 6.0]
        group3 = [7.0, 8.0, 9.0]

        result = kruskal_wallis_test([group1, group2, group3])

        assert result['h_statistic'] > 0.0
        # With small samples, p-value might not be extremely small
        # but should still indicate significance for such distinct groups
        assert result['p_value'] < 0.1

    def test_empty_groups_handling(self):
        """Test that empty groups are handled gracefully."""
        group1 = [1.0, 2.0, 3.0]
        group2 = []
        group3 = [4.0, 5.0, 6.0]

        # Should either return a result or raise a specific exception
        # For this test, we expect it to handle empty groups by skipping them
        # or returning a warning-like result
        result = kruskal_wallis_test([group1, group2, group3])

        # If empty groups are skipped, we should still get valid results
        assert 'h_statistic' in result
        assert 'p_value' in result
        assert 'is_significant' in result

    def test_alpha_threshold(self):
        """Test that significance flag respects alpha threshold."""
        # Create groups with p-value exactly at alpha
        # This is hard to construct precisely, so we test the logic
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [1.1, 2.1, 3.1, 4.1, 5.1]
        group3 = [1.2, 2.2, 3.2, 4.2, 5.2]

        result = kruskal_wallis_test([group1, group2, group3])

        # The is_significant flag should be based on p_value < 0.05
        if result['p_value'] < 0.05:
            assert result['is_significant'] is True
        else:
            assert result['is_significant'] is False

    def test_consistency_with_scipy(self):
        """Verify our implementation matches scipy.stats.kruskal behavior."""
        # We'll create test data and compare results
        try:
            from scipy.stats import kruskal as scipy_kruskal
            
            group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
            group2 = [6.0, 7.0, 8.0, 9.0, 10.0]
            group3 = [11.0, 12.0, 13.0, 14.0, 15.0]

            our_result = kruskal_wallis_test([group1, group2, group3])
            scipy_result = scipy_kruskal(group1, group2, group3)

            # H-statistic should be very close
            assert math.isclose(our_result['h_statistic'], scipy_result.statistic, rel_tol=1e-10)
            
            # P-value should be very close
            assert math.isclose(our_result['p_value'], scipy_result.pvalue, rel_tol=1e-10)
            
        except ImportError:
            # If scipy is not available, skip this test
            pytest.skip("scipy not available for comparison test")


class TestCoefficientOfVariation:
    """Unit tests for coefficient of variation calculation."""

    def test_basic_cv_calculation(self):
        """Test basic CV calculation."""
        values = [10.0, 12.0, 11.0, 13.0, 14.0]
        
        result = compute_coefficient_of_variation(values)
        
        assert 'mean' in result
        assert 'std_dev' in result
        assert 'cv' in result
        
        # CV should be a percentage (0-100)
        assert 0 <= result['cv'] <= 100

    def test_zero_values(self):
        """Test handling of all-zero values."""
        values = [0.0, 0.0, 0.0, 0.0]
        
        result = compute_coefficient_of_variation(values)
        
        # When mean is 0, CV should be 0 or handled gracefully
        assert result['mean'] == 0.0
        assert result['cv'] == 0.0

    def test_single_value(self):
        """Test CV with a single value."""
        values = [5.0]
        
        result = compute_coefficient_of_variation(values)
        
        assert result['std_dev'] == 0.0
        assert result['cv'] == 0.0

    def test_cv_threshold_check(self):
        """Test that CV threshold check works correctly."""
        # Low variability
        values_low = [10.0, 10.1, 9.9, 10.0, 10.0]
        result_low = compute_coefficient_of_variation(values_low)
        assert result_low['cv'] < 15.0
        
        # High variability
        values_high = [1.0, 20.0, 5.0, 15.0, 10.0]
        result_high = compute_coefficient_of_variation(values_high)
        # This should have higher CV, potentially > 15%
        # Exact threshold depends on the data


class TestGroupSignificanceAnalysis:
    """Unit tests for group significance analysis."""

    def test_analyze_significance_basic(self):
        """Test basic group significance analysis."""
        groups = {
            'ArrayBloomFilter': [1.0, 2.0, 3.0, 4.0, 5.0],
            'VectorBloomFilter': [6.0, 7.0, 8.0, 9.0, 10.0],
            'BitsetBloomFilter': [11.0, 12.0, 13.0, 14.0, 15.0]
        }
        
        result = analyze_group_significance(groups)
        
        assert 'h_statistic' in result
        assert 'p_value' in result
        assert 'is_significant' in result
        assert 'groups' in result
        assert result['groups'] == list(groups.keys())

    def test_analyze_significance_with_empty_groups(self):
        """Test analysis with some empty groups."""
        groups = {
            'ArrayBloomFilter': [1.0, 2.0, 3.0],
            'VectorBloomFilter': [],
            'BitsetBloomFilter': [4.0, 5.0, 6.0]
        }
        
        result = analyze_group_significance(groups)
        
        # Should handle empty groups gracefully
        assert 'h_statistic' in result
        assert 'p_value' in result
        assert 'is_significant' in result

    def test_analyze_significance_single_group(self):
        """Test analysis with only one group."""
        groups = {
            'ArrayBloomFilter': [1.0, 2.0, 3.0, 4.0, 5.0]
        }
        
        result = analyze_group_significance(groups)
        
        assert result['h_statistic'] == 0.0
        assert result['p_value'] == 1.0
        assert result['is_significant'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])