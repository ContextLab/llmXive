"""
Unit tests for statistical analysis functions in code/analyze.py.

Specifically tests the Wilcoxon signed-rank test implementation for
paired comparisons of memory usage between LLM-generated and human-written code.
"""
import pytest
import numpy as np
from scipy import stats as scipy_stats
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import code modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analyze import perform_wilcoxon_signed_rank


class TestWilcoxonSignedRank:
    """Test suite for Wilcoxon signed-rank test implementation."""

    def test_perfect_symmetry(self):
        """Test with perfectly symmetric differences (should yield high p-value)."""
        # Create synthetic paired data with symmetric differences
        llm_memory = np.array([100, 200, 300, 400, 500])
        human_memory = np.array([110, 210, 290, 410, 490])
        # Differences: -10, -10, 10, -10, 10 -> symmetric around 0
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        
        assert result is not None
        assert 'statistic' in result
        assert 'p_value' in result
        assert result['p_value'] > 0.05  # Should not reject null hypothesis

    def test_significant_difference(self):
        """Test with clearly different distributions (should yield low p-value)."""
        # LLM consistently uses more memory
        llm_memory = np.array([200, 300, 400, 500, 600])
        human_memory = np.array([100, 150, 200, 250, 300])
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        
        assert result is not None
        assert result['p_value'] < 0.05  # Should reject null hypothesis

    def test_zero_differences_excluded(self):
        """Test that zero differences are properly excluded."""
        llm_memory = np.array([100, 200, 300, 400])
        human_memory = np.array([100, 200, 350, 400])  # Two zero differences
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        
        assert result is not None
        # Should have processed only 2 non-zero differences
        assert result['n_pairs'] == 2

    def test_empty_after_zero_removal(self):
        """Test behavior when all differences are zero."""
        llm_memory = np.array([100, 200, 300])
        human_memory = np.array([100, 200, 300])
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        
        assert result is not None
        assert result['n_pairs'] == 0
        assert result['p_value'] == 1.0  # No difference possible
        assert result['statistic'] == 0

    def test_single_pair(self):
        """Test with minimal valid input (one pair)."""
        llm_memory = np.array([100])
        human_memory = np.array([110])
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        
        assert result is not None
        assert result['n_pairs'] == 1
        # With one pair, p-value calculation may vary but should be valid
        assert 0 <= result['p_value'] <= 1

    def test_tied_ranks_handling(self):
        """Test that tied absolute differences are handled with average ranks."""
        # Create data with tied absolute differences
        llm_memory = np.array([100, 200, 300, 400])
        human_memory = np.array([110, 190, 310, 390])
        # Differences: -10, 10, -10, 10 -> all have |diff| = 10
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        
        assert result is not None
        # Should handle ties without error
        assert 'statistic' in result
        assert 'p_value' in result

    def test_unequal_array_lengths(self):
        """Test error handling for mismatched input lengths."""
        llm_memory = np.array([100, 200, 300])
        human_memory = np.array([100, 200])
        
        with pytest.raises(ValueError, match="Input arrays must have equal length"):
            perform_wilcoxon_signed_rank(llm_memory, human_memory)

    def test_nan_values_handling(self):
        """Test that NaN values are properly handled/excluded."""
        llm_memory = np.array([100, np.nan, 300, 400])
        human_memory = np.array([110, 200, 300, 400])
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        
        assert result is not None
        # Should exclude the pair with NaN
        assert result['n_pairs'] == 3

    def test_effect_size_calculation(self):
        """Test that effect size (rank-biserial correlation) is calculated."""
        llm_memory = np.array([200, 300, 400, 500, 600])
        human_memory = np.array([100, 150, 200, 250, 300])
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        
        assert result is not None
        assert 'effect_size' in result
        assert -1 <= result['effect_size'] <= 1  # Rank-biserial correlation range

    def test_confidence_interval(self):
        """Test that confidence interval is included in results."""
        llm_memory = np.array([200, 300, 400, 500, 600])
        human_memory = np.array([100, 150, 200, 250, 300])
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        
        assert result is not None
        assert 'confidence_interval' in result
        ci = result['confidence_interval']
        assert len(ci) == 2
        assert ci[0] <= ci[1]

    def test_consistency_with_scipy(self):
        """Verify our implementation matches scipy.stats.wilcoxon."""
        np.random.seed(42)
        llm_memory = np.random.normal(100, 20, 50)
        human_memory = np.random.normal(90, 20, 50)
        
        our_result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        scipy_result = scipy_stats.wilcoxon(llm_memory, human_memory)
        
        # Check that p-values are approximately equal
        assert np.isclose(our_result['p_value'], scipy_result.pvalue, rtol=1e-10)
        assert np.isclose(our_result['statistic'], scipy_result.statistic, rtol=1e-10)

    def test_input_validation_types(self):
        """Test that non-array inputs are handled appropriately."""
        # Test with lists (should work as they are array-convertible)
        llm_memory = [100, 200, 300]
        human_memory = [110, 210, 290]
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        assert result is not None
        assert result['n_pairs'] == 3

        # Test with invalid input (strings)
        with pytest.raises((TypeError, ValueError)):
            perform_wilcoxon_signed_rank(["a", "b"], ["c", "d"])

    def test_large_sample_performance(self):
        """Test with larger sample size to ensure scalability."""
        np.random.seed(123)
        llm_memory = np.random.normal(100, 15, 1000)
        human_memory = np.random.normal(95, 15, 1000)
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        
        assert result is not None
        assert result['n_pairs'] == 1000
        assert 'p_value' in result
        assert 'statistic' in result
        assert 'effect_size' in result

    def test_output_structure_completeness(self):
        """Ensure all expected fields are present in output."""
        llm_memory = np.array([100, 200, 300, 400, 500])
        human_memory = np.array([110, 210, 290, 410, 490])
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        
        expected_fields = [
            'statistic', 'p_value', 'n_pairs', 'effect_size',
            'confidence_interval', 'method', 'alternative'
        ]
        
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"

    def test_alternative_hypothesis_parameter(self):
        """Test different alternative hypothesis settings."""
        llm_memory = np.array([200, 300, 400, 500, 600])
        human_memory = np.array([100, 150, 200, 250, 300])
        
        # Test 'greater' (LLM > Human)
        result_greater = perform_wilcoxon_signed_rank(
            llm_memory, human_memory, alternative='greater'
        )
        assert result_greater['alternative'] == 'greater'
        assert result_greater['p_value'] < 0.05  # Should be significant
        
        # Test 'less' (LLM < Human) - should not be significant
        result_less = perform_wilcoxon_signed_rank(
            llm_memory, human_memory, alternative='less'
        )
        assert result_less['alternative'] == 'less'
        assert result_less['p_value'] > 0.05  # Should not be significant

    def test_two_tailed_default(self):
        """Verify that two-sided is the default alternative."""
        llm_memory = np.array([100, 200, 300, 400, 500])
        human_memory = np.array([110, 210, 290, 410, 490])
        
        result = perform_wilcoxon_signed_rank(llm_memory, human_memory)
        
        assert result['alternative'] == 'two-sided'