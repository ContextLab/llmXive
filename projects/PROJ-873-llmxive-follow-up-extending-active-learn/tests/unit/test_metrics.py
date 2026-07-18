"""
test_metrics.py - Unit tests for metrics calculation and wasted call classification.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.metrics import (
    calculate_cosine_similarity_proxy,
    is_wasted_call,
    calculate_ndcg_at_k,
    calculate_ndcg_at_10,
    wilcoxon_signed_rank_test,
    bonferroni_correction,
    StatisticalTestResult,
    BonferroniResult
)

class TestCosineSimilarityProxy:
    def test_identical_texts_high_similarity(self):
        """Test that identical texts have high similarity."""
        text = "This is a test document."
        sim = calculate_cosine_similarity_proxy(text, text)
        assert sim >= 0.9, "Identical texts should have very high similarity"

    def test_different_texts_lower_similarity(self):
        """Test that very different texts have lower similarity."""
        text1 = "The quick brown fox jumps over the lazy dog."
        text2 = "Quantum mechanics explains the behavior of matter and energy."
        sim = calculate_cosine_similarity_proxy(text1, text2)
        # Should be significantly lower than identical
        assert sim < 0.95, "Different texts should have lower similarity"

    def test_similar_texts_high_similarity(self):
        """Test that similar texts have high similarity."""
        text1 = "This is a test document for evaluation."
        text2 = "This is a test document for assessment."
        sim = calculate_cosine_similarity_proxy(text1, text2)
        assert sim > 0.8, "Similar texts should have high similarity"

class TestWastedCallClassification:
    def test_high_similarity_is_wasted(self):
        """Test that similarity > 0.95 is classified as wasted."""
        assert is_wasted_call(0.96) is True
        assert is_wasted_call(0.95) is True
        assert is_wasted_call(0.99) is True

    def test_low_similarity_not_wasted(self):
        """Test that similarity <= 0.95 is not classified as wasted."""
        assert is_wasted_call(0.94) is False
        assert is_wasted_call(0.90) is False
        assert is_wasted_call(0.50) is False

    def test_boundary_case(self):
        """Test the exact boundary case."""
        assert is_wasted_call(0.95, threshold=0.95) is True
        assert is_wasted_call(0.94999, threshold=0.95) is False

    def test_custom_threshold(self):
        """Test with custom threshold."""
        assert is_wasted_call(0.85, threshold=0.8) is True
        assert is_wasted_call(0.79, threshold=0.8) is False

class TestNDCG:
    def test_ndcg_perfect_ranking(self):
        """Test NDCG with perfect ranking."""
        # Perfect ranking: relevant docs first
        scores = [1, 1, 1, 0, 0]
        ndcg = calculate_ndcg_at_k(scores, 5)
        assert ndcg == 1.0, "Perfect ranking should have NDCG = 1.0"

    def test_ndcg_worst_ranking(self):
        """Test NDCG with worst ranking."""
        # Worst ranking: relevant docs last
        scores = [0, 0, 0, 1, 1]
        ndcg = calculate_ndcg_at_k(scores, 5)
        assert ndcg < 1.0, "Worst ranking should have NDCG < 1.0"

    def test_ndcg_at_10(self):
        """Test NDCG@10 specific calculation."""
        scores = [1, 1, 0, 1, 0, 0, 0, 0, 0, 0]
        ndcg = calculate_ndcg_at_10(scores)
        assert 0 <= ndcg <= 1, "NDCG should be between 0 and 1"

    def test_ndcg_empty_list(self):
        """Test NDCG with empty list."""
        ndcg = calculate_ndcg_at_k([], 5)
        assert ndcg == 0.0, "Empty list should have NDCG = 0.0"

    def test_ndcg_k_larger_than_list(self):
        """Test NDCG when k is larger than list length."""
        scores = [1, 1, 0]
        ndcg = calculate_ndcg_at_k(scores, 10)
        assert 0 <= ndcg <= 1, "Should handle k > len(scores)"

class TestWilcoxonTest:
    def test_wilcoxon_returns_result(self):
        """Test that Wilcoxon test returns expected result object."""
        sample1 = [0.8, 0.9, 0.85, 0.92]
        sample2 = [0.7, 0.75, 0.72, 0.78]
        result = wilcoxon_signed_rank_test(sample1, sample2)
        assert isinstance(result, StatisticalTestResult)
        assert hasattr(result, 'statistic')
        assert hasattr(result, 'pvalue')
        assert hasattr(result, 'significant')

    def test_wilcoxon_identical_samples(self):
        """Test Wilcoxon with identical samples (p-value should be 1.0)."""
        sample = [0.8, 0.9, 0.85, 0.92]
        result = wilcoxon_signed_rank_test(sample, sample)
        assert result.pvalue == 1.0, "Identical samples should have p-value = 1.0"

class TestBonferroniCorrection:
    def test_bonferroni_returns_result(self):
        """Test that Bonferroni correction returns expected result object."""
        pvalues = [0.01, 0.03, 0.05, 0.10]
        result = bonferroni_correction(pvalues)
        assert isinstance(result, BonferroniResult)
        assert hasattr(result, 'corrected_alpha')
        assert hasattr(result, 'adjusted_pvalues')
        assert hasattr(result, 'significant_indices')

    def test_bonferroni_adjusts_pvalues(self):
        """Test that Bonferroni adjusts p-values correctly."""
        pvalues = [0.01, 0.02]
        result = bonferroni_correction(pvalues)
        # With 2 tests, alpha=0.05, corrected_alpha should be 0.025
        assert result.corrected_alpha == 0.025
        # Adjusted p-values should be multiplied by n_tests
        assert result.adjusted_pvalues[0] == 0.02
        assert result.adjusted_pvalues[1] == 0.04

    def test_bonferroni_empty_list(self):
        """Test Bonferroni with empty list."""
        result = bonferroni_correction([])
        assert result.corrected_alpha == 0.0
        assert result.adjusted_pvalues == []
        assert result.significant_indices == []

    def test_bonferroni_significance(self):
        """Test significance detection."""
        pvalues = [0.01, 0.06, 0.03]  # With alpha=0.05, n=3 -> corrected_alpha=0.0167
        result = bonferroni_correction(pvalues)
        # 0.01 * 3 = 0.03 < 0.05 -> significant
        # 0.06 * 3 = 0.18 > 0.05 -> not significant
        # 0.03 * 3 = 0.09 > 0.05 -> not significant
        assert 0 in result.significant_indices
        assert 1 not in result.significant_indices
        assert 2 not in result.significant_indices