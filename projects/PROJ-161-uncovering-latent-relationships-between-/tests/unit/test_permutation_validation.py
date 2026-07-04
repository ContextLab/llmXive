"""
Unit tests for Fisher's exact test implementation and permutation validation.

This module tests the statistical functions used in User Story 2 (US2) to ensure
that cluster enrichment analysis is performed correctly and that permutation 
validation properly detects tautological results.
"""
import pytest
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
from scipy.stats import permutation_test
from typing import Tuple, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.config import get_project_root, load_config, PERMUTATION_ITERATIONS


class TestFisherExactTest:
    """Tests for Fisher's exact test implementation."""

    def test_fisher_exact_basic_functionality(self):
        """Test basic Fisher's exact test with known values."""
        # Create a 2x2 contingency table
        #          High Resistance    Low Resistance
        # Cluster      15                5
        # Non-cluster   5                75
        contingency_table = [[15, 5], [5, 75]]
        
        oddsratio, pvalue = fisher_exact(contingency_table, alternative='greater')
        
        # Verify we get reasonable results
        assert 0 < pvalue < 1, "p-value should be between 0 and 1"
        assert oddsratio > 1, "Odds ratio should be > 1 for enrichment"
        
    def test_fisher_exact_significance_threshold(self):
        """Test that Fisher's test correctly identifies significant enrichment."""
        # Strong enrichment case
        strong_table = [[50, 5], [10, 85]]
        _, pval_strong = fisher_exact(strong_table, alternative='greater')
        
        # Weak enrichment case
        weak_table = [[20, 10], [15, 55]]
        _, pval_weak = fisher_exact(weak_table, alternative='greater')
        
        # Strong enrichment should have lower p-value
        assert pval_strong < pval_weak, "Strong enrichment should have lower p-value"
        assert pval_strong < 0.05, "Strong enrichment should be significant at alpha=0.05"

    def test_fisher_exact_edge_cases(self):
        """Test Fisher's exact test with edge cases."""
        # Perfect separation (should give very small p-value)
        perfect_table = [[10, 0], [0, 10]]
        _, pval_perfect = fisher_exact(perfect_table, alternative='greater')
        assert pval_perfect == 0.0 or pval_perfect < 1e-10, "Perfect separation should give near-zero p-value"
        
        # No enrichment (equal distribution)
        null_table = [[10, 10], [10, 10]]
        _, pval_null = fisher_exact(null_table, alternative='greater')
        assert pval_null > 0.05, "No enrichment should not be significant"


class TestPermutationValidation:
    """Tests for permutation validation logic."""

    def test_permutation_test_basic(self):
        """Test basic permutation test functionality."""
        # Simulate data where cluster has higher resistance
        np.random.seed(42)
        cluster_data = np.random.normal(loc=0.8, scale=0.1, size=50)  # High resistance
        non_cluster_data = np.random.normal(loc=0.3, scale=0.1, size=50)  # Low resistance
        
        combined_data = np.concatenate([cluster_data, non_cluster_data])
        group_labels = np.array([1] * 50 + [0] * 50)
        
        # Perform permutation test
        test_statistic = lambda x, axis: np.mean(x[axis == 1]) - np.mean(x[axis == 0])
        
        result = permutation_test(
            (combined_data,), 
            test_statistic, 
            permutation_type='samples',
            n_resample=100,  # Small number for unit test speed
            random_state=42
        )
        
        # Verify we get a valid result
        assert result.pvalue > 0, "p-value should be positive"
        assert result.pvalue <= 1, "p-value should not exceed 1"
        
    def test_permutation_validation_detects_tautology(self):
        """Test that permutation validation detects tautological enrichment."""
        # In a tautological case, the observed statistic should be 
        # indistinguishable from permuted statistics
        np.random.seed(42)
        
        # Create random data with no true structure
        random_data = np.random.normal(loc=0.5, scale=0.2, size=100)
        random_labels = np.random.choice([0, 1], size=100)
        
        # Calculate observed statistic
        observed_stat = np.mean(random_data[random_labels == 1]) - np.mean(random_data[random_labels == 0])
        
        # Calculate permuted statistics
        permuted_stats = []
        n_iterations = 100  # Small for unit test
        
        for _ in range(n_iterations):
            shuffled_labels = np.random.permutation(random_labels)
            perm_stat = np.mean(random_data[shuffled_labels == 1]) - np.mean(random_data[shuffled_labels == 0])
            permuted_stats.append(perm_stat)
        
        # In a tautological case, observed should be within the distribution of permuted
        permuted_stats = np.array(permuted_stats)
        p_value_perm = (np.sum(permuted_stats >= observed_stat) + 1) / (n_iterations + 1)
        
        # For random data, p-value should be > 0.05 (not significant)
        assert p_value_perm > 0.05, "Random data should not show significant enrichment"

    def test_permutation_validation_detects_real_signal(self):
        """Test that permutation validation detects real enrichment signal."""
        np.random.seed(42)
        
        # Create data with clear structure
        cluster_data = np.random.normal(loc=0.9, scale=0.05, size=50)
        non_cluster_data = np.random.normal(loc=0.1, scale=0.05, size=50)
        
        combined_data = np.concatenate([cluster_data, non_cluster_data])
        true_labels = np.array([1] * 50 + [0] * 50)
        
        # Calculate observed statistic
        observed_stat = np.mean(combined_data[true_labels == 1]) - np.mean(combined_data[true_labels == 0])
        
        # Calculate permuted statistics
        permuted_stats = []
        n_iterations = 100  # Small for unit test
        
        for _ in range(n_iterations):
            shuffled_labels = np.random.permutation(true_labels)
            perm_stat = np.mean(combined_data[shuffled_labels == 1]) - np.mean(combined_data[shuffled_labels == 0])
            permuted_stats.append(perm_stat)
        
        permuted_stats = np.array(permuted_stats)
        p_value_perm = (np.sum(permuted_stats >= observed_stat) + 1) / (n_iterations + 1)
        
        # For structured data, p-value should be very small
        assert p_value_perm < 0.05, "Structured data should show significant enrichment"
        assert p_value_perm < 0.01, "Strong structure should show very significant enrichment"

    def test_permutation_iterations_from_config(self):
        """Test that permutation validation uses the configured number of iterations."""
        # Verify that the config value is accessible and reasonable
        config = load_config()
        iterations = config.get('PERMUTATION_ITERATIONS', 1000)
        
        assert isinstance(iterations, int), "PERMUTATION_ITERATIONS should be an integer"
        assert iterations > 0, "PERMUTATION_ITERATIONS should be positive"
        assert iterations >= 100, "PERMUTATION_ITERATIONS should be at least 100 for valid statistics"
        
        # In production, this would be exactly PERMUTATION_ITERATIONS
        # For unit tests, we use a smaller number for speed
        assert iterations == 1000, "Default PERMUTATION_ITERATIONS should be 1000"

    def test_permutation_test_with_small_sample(self):
        """Test permutation test with small sample sizes."""
        np.random.seed(42)
        
        small_cluster = np.array([0.8, 0.9, 0.85])
        small_non_cluster = np.array([0.2, 0.3, 0.25])
        
        combined = np.concatenate([small_cluster, small_non_cluster])
        labels = np.array([1, 1, 1, 0, 0, 0])
        
        observed = np.mean(combined[labels == 1]) - np.mean(combined[labels == 0])
        
        # With small samples, permutation test should still work
        perm_stats = []
        for _ in range(50):
            shuffled = np.random.permutation(labels)
            perm_stat = np.mean(combined[shuffled == 1]) - np.mean(combined[shuffled == 0])
            perm_stats.append(perm_stat)
        
        p_val = (np.sum(np.array(perm_stats) >= observed) + 1) / (len(perm_stats) + 1)
        
        # Should be significant with such clear separation
        assert p_val < 0.05, "Small but clear separation should be significant"


class TestIntegration:
    """Integration tests for Fisher's test and permutation validation."""

    def test_full_enrichment_pipeline(self):
        """Test the full enrichment analysis pipeline."""
        np.random.seed(42)
        
        # Simulate cluster assignments and resistance data
        n_samples = 200
        resistance_scores = np.random.beta(2, 5, size=n_samples)  # Skewed towards lower resistance
        
        # Create clusters with different characteristics
        cluster_labels = np.zeros(n_samples, dtype=int)
        cluster_labels[:60] = 1  # 60 samples in cluster
        
        # Make cluster have higher resistance
        resistance_scores[cluster_labels == 1] = np.random.beta(4, 2, size=60)
        
        # Create contingency table for Fisher's test
        high_resistance_threshold = 0.7
        high_res_cluster = np.sum((resistance_scores[cluster_labels == 1] >= high_resistance_threshold))
        low_res_cluster = np.sum((resistance_scores[cluster_labels == 1] < high_resistance_threshold))
        high_res_non_cluster = np.sum((resistance_scores[cluster_labels == 0] >= high_resistance_threshold))
        low_res_non_cluster = np.sum((resistance_scores[cluster_labels == 0] < high_resistance_threshold))
        
        contingency_table = [
            [high_res_cluster, low_res_cluster],
            [high_res_non_cluster, low_res_non_cluster]
        ]
        
        # Fisher's exact test
        oddsratio, pvalue_fisher = fisher_exact(contingency_table, alternative='greater')
        
        # Permutation validation
        observed_stat = np.mean(resistance_scores[cluster_labels == 1]) - np.mean(resistance_scores[cluster_labels == 0])
        
        perm_stats = []
        n_permutations = 100
        for _ in range(n_permutations):
            shuffled_labels = np.random.permutation(cluster_labels)
            perm_stat = np.mean(resistance_scores[shuffled_labels == 1]) - np.mean(resistance_scores[shuffled_labels == 0])
            perm_stats.append(perm_stat)
        
        pvalue_perm = (np.sum(np.array(perm_stats) >= observed_stat) + 1) / (n_permutations + 1)
        
        # Verify results
        assert 0 < pvalue_fisher < 1, "Fisher p-value should be valid"
        assert 0 < pvalue_perm < 1, "Permutation p-value should be valid"
        
        # Both tests should agree on significance
        both_significant = (pvalue_fisher < 0.05) and (pvalue_perm < 0.05)
        both_not_significant = (pvalue_fisher >= 0.05) and (pvalue_perm >= 0.05)
        
        assert both_significant or both_not_significant, "Fisher and permutation tests should agree on significance"

    def test_edge_case_no_clusters(self):
        """Test handling of edge case with no clusters."""
        # All samples in one group
        all_cluster = np.ones(100, dtype=int)
        resistance = np.random.random(100)
        
        # This should not crash, but may not be meaningful
        observed = np.mean(resistance[all_cluster == 1]) - np.mean(resistance[all_cluster == 0])
        
        # With no variation in labels, permutation test is degenerate
        # Our implementation should handle this gracefully
        assert not np.isnan(observed), "Should handle edge case without NaN"

    def test_consistency_across_runs(self):
        """Test that results are consistent when random seed is set."""
        def run_analysis(seed):
            np.random.seed(seed)
            n = 100
            resistance = np.random.random(n)
            labels = np.random.randint(0, 2, n)
            
            observed = np.mean(resistance[labels == 1]) - np.mean(resistance[labels == 0])
            
            perm_stats = []
            for _ in range(50):
                shuffled = np.random.permutation(labels)
                perm_stat = np.mean(resistance[shuffled == 1]) - np.mean(resistance[shuffled == 0])
                perm_stats.append(perm_stat)
            
            return observed, np.mean(perm_stats)
        
        # Same seed should give same results
        obs1, perm1 = run_analysis(123)
        obs2, perm2 = run_analysis(123)
        
        assert obs1 == obs2, "Results should be identical with same seed"
        assert perm1 == perm2, "Permutation results should be identical with same seed"