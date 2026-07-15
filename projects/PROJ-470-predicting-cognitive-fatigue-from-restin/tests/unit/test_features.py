import pytest
import numpy as np
import sys
import os

# Add code to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from features import calculate_lzc, calculate_permutation_entropy

class TestLZC:
    """Unit tests for Lempel-Ziv Complexity calculation."""

    def test_constant_signal(self):
        """Constant signal should have LZC near 0."""
        signal = np.ones(1000)
        lzc = calculate_lzc(signal)
        assert lzc < 0.1, f"Constant signal LZC should be near 0, got {lzc}"

    def test_alternating_signal(self):
        """Alternating 0/1 signal has low complexity."""
        signal = np.tile([0, 1], 500)
        lzc = calculate_lzc(signal)
        # Alternating pattern is simple, low LZC
        assert lzc < 0.5, f"Alternating signal LZC too high: {lzc}"

    def test_random_signal(self):
        """Random signal should have higher LZC."""
        np.random.seed(42)
        signal = np.random.randn(1000)
        lzc = calculate_lzc(signal)
        # Random signal should have moderate to high complexity
        assert 0.3 < lzc < 1.0, f"Random signal LZC out of expected range: {lzc}"

    def test_empty_signal(self):
        """Empty signal should return 0."""
        signal = np.array([])
        lzc = calculate_lzc(signal)
        assert lzc == 0.0

    def test_known_pattern(self):
        """Test with a known repeating pattern."""
        # Pattern: 1, 2, 3 repeated
        signal = np.tile([1, 2, 3], 300)
        lzc = calculate_lzc(signal)
        assert lzc < 0.5, f"Repeating pattern should have low LZC, got {lzc}"

class TestPermutationEntropy:
    """Unit tests for Permutation Entropy calculation."""

    def test_constant_signal(self):
        """Constant signal has zero permutation entropy."""
        signal = np.ones(1000)
        pe = calculate_permutation_entropy(signal, order=3)
        assert pe == 0.0, f"Constant signal PE should be 0, got {pe}"

    def test_linear_trend(self):
        """Linear trend has low permutation entropy."""
        signal = np.linspace(0, 10, 1000)
        pe = calculate_permutation_entropy(signal, order=3)
        assert pe < 0.5, f"Linear trend PE too high: {pe}"

    def test_random_signal(self):
        """Random signal should have high permutation entropy."""
        np.random.seed(42)
        signal = np.random.randn(1000)
        pe = calculate_permutation_entropy(signal, order=3)
        # Max PE for order 3 is 1.0
        assert 0.5 < pe <= 1.0, f"Random signal PE out of expected range: {pe}"

    def test_order_2(self):
        """Test with order=2 (only 2 permutations possible)."""
        signal = np.random.randn(1000)
        pe = calculate_permutation_entropy(signal, order=2)
        assert 0 <= pe <= 1.0

    def test_high_order(self):
        """Test with higher order."""
        signal = np.random.randn(1000)
        pe = calculate_permutation_entropy(signal, order=5)
        assert 0 <= pe <= 1.0

    def test_short_signal(self):
        """Short signal should handle gracefully."""
        signal = np.array([1.0, 2.0, 3.0])
        # With order=3, delay=1, we need at least 3 points
        pe = calculate_permutation_entropy(signal, order=3)
        assert 0 <= pe <= 1.0

    def test_too_short_signal(self):
        """Signal too short for order should return 0."""
        signal = np.array([1.0, 2.0])
        pe = calculate_permutation_entropy(signal, order=3)
        assert pe == 0.0