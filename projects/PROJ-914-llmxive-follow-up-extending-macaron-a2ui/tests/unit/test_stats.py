"""
Unit tests for statistical correction methods (FDR/Bonferroni) in code/analysis/stats.py.

This module validates the Benjamini-Hochberg FDR and Bonferroni correction
implementations against known mathematical properties and edge cases.

Tests verify:
1. FDR correction produces valid adjusted p-values (0 <= q <= 1)
2. Bonferroni correction produces valid adjusted p-values
3. Both methods correctly handle edge cases (all 1s, all 0s, single value)
4. FDR is less conservative than Bonferroni (as expected theoretically)
5. Sorting and ranking logic is correct
"""

import pytest
import numpy as np
from analysis.stats import (
    benjamini_hochberg_fdr,
    bonferroni_correction,
    pairwise_ttest_with_fdr,
    validate_sample_size,
    calculate_power
)
from config import RANDOM_SEED

# Set random seed for reproducibility
np.random.seed(RANDOM_SEED)


class TestBenjaminiHochbergFDR:
    """Tests for the Benjamini-Hochberg FDR correction."""

    def test_basic_fdr_correction(self):
        """Test FDR correction on a simple set of p-values."""
        p_values = [0.01, 0.03, 0.05, 0.07, 0.10]
        alpha = 0.05
        
        adjusted_pvalues, is_significant = benjamini_hochberg_fdr(p_values, alpha)
        
        # Check that we get the right number of outputs
        assert len(adjusted_pvalues) == len(p_values)
        assert len(is_significant) == len(p_values)
        
        # Check that adjusted p-values are in [0, 1]
        for q in adjusted_pvalues:
            assert 0.0 <= q <= 1.0
        
        # Check that significant results correspond to original p-values < alpha
        # (Note: FDR is more lenient, so this is a necessary but not sufficient condition)
        for i, (p, sig) in enumerate(zip(p_values, is_significant)):
            if sig:
                # If significant after FDR, original p-value must be <= alpha
                # (though this is not guaranteed for all cases, it's a good sanity check)
                assert p <= alpha
    
    def test_fdr_edge_case_all_zeros(self):
        """Test FDR when all p-values are 0."""
        p_values = [0.0, 0.0, 0.0]
        alpha = 0.05
        
        adjusted_pvalues, is_significant = benjamini_hochberg_fdr(p_values, alpha)
        
        # All should be significant
        assert all(is_significant)
        # Adjusted p-values should be 0
        assert all(q == 0.0 for q in adjusted_pvalues)
    
    def test_fdr_edge_case_all_ones(self):
        """Test FDR when all p-values are 1."""
        p_values = [1.0, 1.0, 1.0]
        alpha = 0.05
        
        adjusted_pvalues, is_significant = benjamini_hochberg_fdr(p_values, alpha)
        
        # None should be significant
        assert not any(is_significant)
        # Adjusted p-values should be 1
        assert all(q == 1.0 for q in adjusted_pvalues)
    
    def test_fdr_monotonicity(self):
        """Test that adjusted p-values are monotonically non-decreasing with rank."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        alpha = 0.05
        
        adjusted_pvalues, _ = benjamini_hochberg_fdr(p_values, alpha)
        
        # BH procedure ensures monotonicity: q_(i) <= q_(i+1)
        for i in range(len(adjusted_pvalues) - 1):
            assert adjusted_pvalues[i] <= adjusted_pvalues[i + 1]
    
    def test_fdr_less_conservative_than_bonferroni(self):
        """Test that FDR is less conservative than Bonferroni (more rejections)."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05, 0.10, 0.20]
        alpha = 0.05
        
        _, fdr_sig = benjamini_hochberg_fdr(p_values, alpha)
        _, bonf_sig = bonferroni_correction(p_values, alpha)
        
        # FDR should reject at least as many hypotheses as Bonferroni
        assert sum(fdr_sig) >= sum(bonf_sig)
    
    def test_fdr_single_pvalue(self):
        """Test FDR with a single p-value."""
        p_values = [0.03]
        alpha = 0.05
        
        adjusted_pvalues, is_significant = benjamini_hochberg_fdr(p_values, alpha)
        
        assert len(adjusted_pvalues) == 1
        assert len(is_significant) == 1
        assert is_significant[0] == True  # 0.03 < 0.05
        assert adjusted_pvalues[0] == 0.03  # For single value, q = p
    
    def test_fdr_empty_list(self):
        """Test FDR with an empty list of p-values."""
        p_values = []
        alpha = 0.05
        
        adjusted_pvalues, is_significant = benjamini_hochberg_fdr(p_values, alpha)
        
        assert len(adjusted_pvalues) == 0
        assert len(is_significant) == 0
    
    def test_fdr_random_pvalues(self):
        """Test FDR on a larger set of random p-values."""
        np.random.seed(RANDOM_SEED)
        p_values = np.random.uniform(0, 1, 100).tolist()
        alpha = 0.05
        
        adjusted_pvalues, is_significant = benjamini_hochberg_fdr(p_values, alpha)
        
        assert len(adjusted_pvalues) == 100
        assert len(is_significant) == 100
        
        # Check bounds
        for q in adjusted_pvalues:
            assert 0.0 <= q <= 1.0
        
        # Check monotonicity
        for i in range(len(adjusted_pvalues) - 1):
            assert adjusted_pvalues[i] <= adjusted_pvalues[i + 1]

class TestBonferroniCorrection:
    """Tests for the Bonferroni correction."""

    def test_basic_bonferroni_correction(self):
        """Test Bonferroni correction on a simple set of p-values."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        alpha = 0.05
        
        adjusted_pvalues, is_significant = bonferroni_correction(p_values, alpha)
        
        # Check that we get the right number of outputs
        assert len(adjusted_pvalues) == len(p_values)
        assert len(is_significant) == len(p_values)
        
        # Check that adjusted p-values are in [0, 1]
        for q in adjusted_pvalues:
            assert 0.0 <= q <= 1.0
        
        # Bonferroni: reject if p <= alpha / n
        n = len(p_values)
        threshold = alpha / n
        expected_significant = [p <= threshold for p in p_values]
        
        assert list(is_significant) == expected_significant
    
    def test_bonferroni_edge_case_all_zeros(self):
        """Test Bonferroni when all p-values are 0."""
        p_values = [0.0, 0.0, 0.0]
        alpha = 0.05
        
        adjusted_pvalues, is_significant = bonferroni_correction(p_values, alpha)
        
        # All should be significant
        assert all(is_significant)
        # Adjusted p-values should be 0
        assert all(q == 0.0 for q in adjusted_pvalues)
    
    def test_bonferroni_edge_case_all_ones(self):
        """Test Bonferroni when all p-values are 1."""
        p_values = [1.0, 1.0, 1.0]
        alpha = 0.05
        
        adjusted_pvalues, is_significant = bonferroni_correction(p_values, alpha)
        
        # None should be significant
        assert not any(is_significant)
        # Adjusted p-values should be 1 (capped at 1.0)
        assert all(q == 1.0 for q in adjusted_pvalues)
    
    def test_bonferroni_single_pvalue(self):
        """Test Bonferroni with a single p-value."""
        p_values = [0.03]
        alpha = 0.05
        
        adjusted_pvalues, is_significant = bonferroni_correction(p_values, alpha)
        
        assert len(adjusted_pvalues) == 1
        assert len(is_significant) == 1
        assert is_significant[0] == True  # 0.03 < 0.05
        assert adjusted_pvalues[0] == 0.03  # For single value, q = p
    
    def test_bonferroni_empty_list(self):
        """Test Bonferroni with an empty list of p-values."""
        p_values = []
        alpha = 0.05
        
        adjusted_pvalues, is_significant = bonferroni_correction(p_values, alpha)
        
        assert len(adjusted_pvalues) == 0
        assert len(is_significant) == 0

class TestPairwiseTTtestWithFDR:
    """Tests for pairwise t-test with FDR correction."""

    def test_pairwise_ttest_basic(self):
        """Test pairwise t-test with FDR on simple data."""
        np.random.seed(RANDOM_SEED)
        # Create three groups with different means
        group1 = np.random.normal(0, 1, 50)
        group2 = np.random.normal(0.5, 1, 50)
        group3 = np.random.normal(1.0, 1, 50)
        
        groups = [group1, group2, group3]
        alpha = 0.05
        
        results = pairwise_ttest_with_fdr(groups, alpha)
        
        # Check that we get results for all pairs
        # 3 groups -> 3 pairs: (0,1), (0,2), (1,2)
        assert len(results) == 3
        
        # Check structure of each result
        for res in results:
            assert 'pair' in res
            assert 'p_value' in res
            assert 'adjusted_p_value' in res
            assert 'is_significant' in res
            assert 't_statistic' in res
            
            # Check bounds
            assert 0.0 <= res['p_value'] <= 1.0
            assert 0.0 <= res['adjusted_p_value'] <= 1.0
            assert isinstance(res['is_significant'], bool)
    
    def test_pairwise_ttest_identical_groups(self):
        """Test pairwise t-test when groups are identical."""
        np.random.seed(RANDOM_SEED)
        data = np.random.normal(0, 1, 50)
        groups = [data, data, data]
        alpha = 0.05
        
        results = pairwise_ttest_with_fdr(groups, alpha)
        
        # With identical groups, p-values should be high (not significant)
        for res in results:
            # Note: Due to sampling variation, p-values might not be exactly 1.0
            # but they should generally be high
            assert res['p_value'] > 0.01  # Should not be extremely small

class TestValidateSampleSize:
    """Tests for sample size validation."""

    def test_validate_sample_size_sufficient(self):
        """Test validation with sufficient sample size."""
        # Assuming a minimum of 30 per group is sufficient
        assert validate_sample_size(50, 0.5)  # n=50, effect_size=0.5
        assert validate_sample_size(100, 0.3)  # n=100, effect_size=0.3

    def test_validate_sample_size_insufficient(self):
        """Test validation with insufficient sample size."""
        # Very small sample with small effect size
        assert not validate_sample_size(5, 0.1)

class TestCalculatePower:
    """Tests for power calculation."""

    def test_calculate_power_basic(self):
        """Test basic power calculation."""
        # Larger sample size should give higher power
        power_large = calculate_power(100, 0.5)
        power_small = calculate_power(20, 0.5)
        
        assert power_large > power_small
        assert 0.0 <= power_large <= 1.0
        assert 0.0 <= power_small <= 1.0
    
    def test_calculate_power_effect_size(self):
        """Test that larger effect size gives higher power."""
        power_large_effect = calculate_power(50, 0.8)
        power_small_effect = calculate_power(50, 0.2)
        
        assert power_large_effect > power_small_effect
        assert 0.0 <= power_large_effect <= 1.0
        assert 0.0 <= power_small_effect <= 1.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])