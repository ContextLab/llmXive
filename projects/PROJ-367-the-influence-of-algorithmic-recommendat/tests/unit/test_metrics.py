"""
Unit tests for metrics.py (T011).

Tests Shannon entropy calculation and diversity score logic.
"""
import pytest
import math
from metrics import shannon_entropy, calculate_diversity_score

class TestShannonEntropy:
    def test_uniform_distribution(self):
        """Test entropy of a uniform distribution (max entropy)."""
        # 2 categories, equal probability -> log2(2) = 1.0
        counts = [10, 10]
        # Normalize to probabilities
        total = sum(counts)
        probs = [c / total for c in counts]
        entropy = shannon_entropy(probs)
        assert math.isclose(entropy, 1.0, rel_tol=1e-9)

    def test_deterministic_distribution(self):
        """Test entropy of a deterministic distribution (zero entropy)."""
        # 1 category, 100% probability -> log2(1) = 0.0
        counts = [10]
        total = sum(counts)
        probs = [c / total for c in counts]
        entropy = shannon_entropy(probs)
        assert math.isclose(entropy, 0.0, rel_tol=1e-9)

    def test_known_value(self):
        """Test against a known manual calculation."""
        # Categories: Math, Math, Science (2 Math, 1 Science)
        # Probs: [2/3, 1/3]
        # Entropy = - (2/3)*log2(2/3) - (1/3)*log2(1/3)
        #         = - (2/3)*(-0.58496) - (1/3)*(-1.58496)
        #         = 0.38997 + 0.52832 = 0.91829
        counts = [2, 1]
        total = sum(counts)
        probs = [c / total for c in counts]
        entropy = shannon_entropy(probs)
        expected = -(2/3) * math.log2(2/3) - (1/3) * math.log2(1/3)
        assert math.isclose(entropy, expected, rel_tol=1e-9)

class TestCalculateDiversityScore:
    def test_diversity_score_calculation(self):
        """Test the wrapper function with a list of category counts."""
        # Input: 3 categories with counts [4, 2, 1]
        # Total = 7
        # Probs = [4/7, 2/7, 1/7]
        counts = [4, 2, 1]
        score = calculate_diversity_score(counts)
        
        # Manual calculation
        total = sum(counts)
        probs = [c / total for c in counts]
        expected = shannon_entropy(probs)
        
        assert math.isclose(score, expected, rel_tol=1e-9)

    def test_empty_input(self):
        """Test behavior with empty input (should return 0 or handle gracefully)."""
        # Per spec, empty enrollments should result in null or exclusion,
        # but the metric function itself should handle edge cases.
        # We expect 0 entropy for a single "empty" state or raise an error.
        # Based on typical Shannon entropy, 0 items -> 0 entropy.
        score = calculate_diversity_score([])
        assert score == 0.0
