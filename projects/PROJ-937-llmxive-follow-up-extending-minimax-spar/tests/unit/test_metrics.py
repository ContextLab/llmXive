"""
Unit tests for code/eval/metrics.py.

Tests Exact Match, F1, and Perplexity calculators.
These tests verify that the metrics return the expected types and values
for known inputs.
"""
import pytest
import math
import numpy as np
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from eval.metrics import (
    calculate_exact_match,
    calculate_f1,
    calculate_perplexity
)


class TestExactMatch:
    """Tests for the Exact Match metric."""

    def test_exact_match_perfect(self):
        """Test that identical strings return 1.0."""
        prediction = "The quick brown fox"
        reference = "The quick brown fox"
        score = calculate_exact_match(prediction, reference)
        assert isinstance(score, float)
        assert score == 1.0

    def test_exact_match_case_sensitive(self):
        """Test that case differences return 0.0 (default behavior)."""
        prediction = "The Quick Brown Fox"
        reference = "The quick brown fox"
        score = calculate_exact_match(prediction, reference)
        assert isinstance(score, float)
        assert score == 0.0

    def test_exact_match_partial(self):
        """Test that partial matches return 0.0."""
        prediction = "The quick"
        reference = "The quick brown fox"
        score = calculate_exact_match(prediction, reference)
        assert isinstance(score, float)
        assert score == 0.0

    def test_exact_match_whitespace_normalization(self):
        """Test that extra whitespace is handled correctly (stripped)."""
        prediction = "  The quick brown fox  "
        reference = "The quick brown fox"
        score = calculate_exact_match(prediction, reference)
        assert isinstance(score, float)
        assert score == 1.0

    def test_exact_match_empty_strings(self):
        """Test behavior with empty strings."""
        prediction = ""
        reference = ""
        score = calculate_exact_match(prediction, reference)
        assert isinstance(score, float)
        assert score == 1.0

    def test_exact_match_non_empty_vs_empty(self):
        """Test behavior when one string is empty."""
        prediction = "Something"
        reference = ""
        score = calculate_exact_match(prediction, reference)
        assert isinstance(score, float)
        assert score == 0.0


class TestF1:
    """Tests for the F1 Score metric."""

    def test_f1_perfect(self):
        """Test that identical tokenized strings return 1.0."""
        prediction = "The quick brown fox"
        reference = "The quick brown fox"
        score = calculate_f1(prediction, reference)
        assert isinstance(score, float)
        assert abs(score - 1.0) < 1e-6

    def test_f1_no_overlap(self):
        """Test that completely different strings return 0.0."""
        prediction = "cat dog bird"
        reference = "elephant tiger lion"
        score = calculate_f1(prediction, reference)
        assert isinstance(score, float)
        assert score == 0.0

    def test_f1_partial_overlap(self):
        """Test F1 with partial token overlap."""
        prediction = "the cat sat on the mat"
        reference = "the dog sat on the rug"
        # Common: "the", "sat", "on", "the" (4 tokens)
        # Pred unique: "cat", "mat" (2) -> Precision = 4/6
        # Ref unique: "dog", "rug" (2) -> Recall = 4/6
        # F1 = 2 * (P*R)/(P+R)
        score = calculate_f1(prediction, reference)
        assert isinstance(score, float)
        expected_precision = 4 / 6
        expected_recall = 4 / 6
        expected_f1 = 2 * (expected_precision * expected_recall) / (expected_precision + expected_recall)
        assert abs(score - expected_f1) < 1e-6

    def test_f1_case_insensitivity(self):
        """Test that F1 is case insensitive."""
        prediction = "The Quick Brown Fox"
        reference = "the quick brown fox"
        score = calculate_f1(prediction, reference)
        assert isinstance(score, float)
        assert abs(score - 1.0) < 1e-6

    def test_f1_empty_prediction(self):
        """Test F1 when prediction is empty."""
        prediction = ""
        reference = "some text here"
        score = calculate_f1(prediction, reference)
        assert isinstance(score, float)
        assert score == 0.0

    def test_f1_empty_reference(self):
        """Test F1 when reference is empty."""
        prediction = "some text here"
        reference = ""
        score = calculate_f1(prediction, reference)
        assert isinstance(score, float)
        assert score == 0.0


class TestPerplexity:
    """Tests for the Perplexity metric."""

    def test_perplexity_uniform_distribution(self):
        """
        Test Perplexity with a uniform distribution.
        If probabilities are uniform (1/N), Perplexity should be N.
        Example: 4 tokens, each prob 0.25 -> PPL = 4.
        """
        # Log probs: ln(0.25)
        log_probs = [math.log(0.25), math.log(0.25), math.log(0.25), math.log(0.25)]
        score = calculate_perplexity(log_probs)
        assert isinstance(score, float)
        assert abs(score - 4.0) < 1e-4

    def test_perplexity_certainty(self):
        """
        Test Perplexity when one token has probability 1.0.
        PPL should be 1.0.
        """
        # Log probs: ln(1.0) = 0, others -inf (but we assume valid distribution)
        # Using a very small epsilon for others to avoid log(0) in real scenarios,
        # but for this test we simulate the ideal case.
        # In practice, calculate_perplexity handles the math.
        # If the model is 100% sure:
        log_probs = [0.0, -1000.0, -1000.0] # Approximating 1.0, 0, 0
        # Actually, let's use the formula: exp(-1/N * sum(log(p)))
        # If p=[1, 0, 0], sum(log) is 0. exp(0) = 1.
        # But log(0) is undefined. We assume the input is valid log-probs.
        # Let's use a distribution very close to certainty.
        import numpy as np
        probs = np.array([0.9999, 0.00005, 0.00005])
        log_probs = np.log(probs)
        score = calculate_perplexity(log_probs.tolist())
        assert isinstance(score, float)
        assert abs(score - 1.0) < 0.01

    def test_perplexity_returns_float(self):
        """Test that perplexity always returns a float."""
        log_probs = [math.log(0.5), math.log(0.5)]
        score = calculate_perplexity(log_probs)
        assert isinstance(score, float)
        assert score > 0

    def test_perplexity_high_confidence_low_ppl(self):
        """Test that high confidence leads to lower perplexity."""
        # Case A: Uniform 2 tokens -> PPL = 2
        log_probs_a = [math.log(0.5), math.log(0.5)]
        ppl_a = calculate_perplexity(log_probs_a)

        # Case B: Skewed 2 tokens (0.9, 0.1) -> PPL < 2
        log_probs_b = [math.log(0.9), math.log(0.1)]
        ppl_b = calculate_perplexity(log_probs_b)

        assert ppl_b < ppl_a

    def test_perplexity_single_token(self):
        """Test Perplexity with a single log-prob (should be 1.0 if prob=1)."""
        # If log_prob is 0 (prob 1.0), PPL = exp(0) = 1
        score = calculate_perplexity([0.0])
        assert isinstance(score, float)
        assert abs(score - 1.0) < 1e-6