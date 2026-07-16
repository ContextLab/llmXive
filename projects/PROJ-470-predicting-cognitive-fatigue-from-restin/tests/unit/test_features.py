"""
Unit tests for feature extraction functions.

Tests for Permutation Entropy and Lempel-Ziv Complexity calculations.
"""
import pytest
import numpy as np
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from features import calculate_permutation_entropy, calculate_lzc


class TestPermutationEntropy:
    """Tests for permutation entropy calculation."""
    
    def test_constant_signal(self):
        """PE should be 0 for constant signal (no patterns)."""
        signal = np.ones(100)
        entropy = calculate_permutation_entropy(signal, order=3, delay=1)
        assert entropy == 0.0
    
    def test_alternating_signal(self):
        """PE should be low for highly regular alternating signal."""
        signal = np.array([0, 1, 0, 1, 0, 1, 0, 1] * 12)
        entropy = calculate_permutation_entropy(signal, order=3, delay=1)
        # Should be relatively low compared to random
        assert entropy < 1.0
    
    def test_random_signal(self):
        """PE should be higher for random signal."""
        np.random.seed(42)
        signal = np.random.randn(500)
        entropy = calculate_permutation_entropy(signal, order=3, delay=1)
        # Should be closer to maximum (log2(6) ≈ 2.58)
        assert entropy > 1.5
    
    def test_order_parameter(self):
        """PE should change with different order values."""
        signal = np.random.randn(500)
        entropy_order3 = calculate_permutation_entropy(signal, order=3, delay=1)
        entropy_order4 = calculate_permutation_entropy(signal, order=4, delay=1)
        
        # Different orders should give different results
        assert entropy_order3 != entropy_order4
    
    def test_empty_signal(self):
        """PE should return 0 for empty signal."""
        signal = np.array([])
        entropy = calculate_permutation_entropy(signal)
        assert entropy == 0.0
    
    def test_small_signal(self):
        """PE should handle very small signals gracefully."""
        signal = np.array([1, 2, 3])
        entropy = calculate_permutation_entropy(signal, order=3, delay=1)
        assert entropy >= 0.0
    
    def test_known_signal(self):
        """Test with a signal of known properties."""
        # Create a signal with known pattern
        # [0, 1, 2, 0, 1, 2, ...] should have low entropy
        signal = np.tile([0, 1, 2], 50)
        entropy = calculate_permutation_entropy(signal, order=3, delay=1)
        assert entropy < 0.5  # Very low entropy for repeating pattern

class TestLempelZivComplexity:
    """Tests for Lempel-Ziv complexity calculation."""
    
    def test_constant_signal(self):
        """LZC should be low for constant signal."""
        signal = np.ones(100)
        lzc = calculate_lzc(signal)
        assert lzc < 0.5  # Low complexity
    
    def test_alternating_signal(self):
        """LZC should be low for alternating signal."""
        signal = np.array([0, 1, 0, 1, 0, 1, 0, 1] * 25)
        lzc = calculate_lzc(signal)
        assert lzc < 0.5  # Low complexity
    
    def test_random_signal(self):
        """LZC should be higher for random signal."""
        np.random.seed(42)
        signal = np.random.randn(500)
        lzc = calculate_lzc(signal)
        # Should be higher than regular signals
        assert lzc > 0.5
    
    def test_empty_signal(self):
        """LZC should return 0 for empty signal."""
        signal = np.array([])
        lzc = calculate_lzc(signal)
        assert lzc == 0.0
    
    def test_small_signal(self):
        """LZC should handle small signals."""
        signal = np.array([1, 2, 3, 4, 5])
        lzc = calculate_lzc(signal)
        assert lzc >= 0.0
    
    def test_binary_signal(self):
        """LZC should work with binary signals."""
        signal = np.array([0, 1, 0, 0, 1, 1, 0, 1, 0, 1] * 20)
        lzc = calculate_lzc(signal)
        assert lzc >= 0.0 and lzc <= 1.0  # Normalized value

class TestIntegration:
    """Integration tests for feature extraction."""
    
    def test_both_metrics_on_same_signal(self):
        """Both metrics should produce reasonable values on same signal."""
        np.random.seed(42)
        signal = np.random.randn(500)
        
        lzc = calculate_lzc(signal)
        pe = calculate_permutation_entropy(signal)
        
        # Both should be non-negative
        assert lzc >= 0.0
        assert pe >= 0.0
        
        # Both should be finite
        assert np.isfinite(lzc)
        assert np.isfinite(pe)
    
    def test_different_signals_different_metrics(self):
        """Different signals should produce different metric values."""
        np.random.seed(42)
        signal1 = np.random.randn(500)
        signal2 = np.random.randn(500)
        
        lzc1 = calculate_lzc(signal1)
        lzc2 = calculate_lzc(signal2)
        pe1 = calculate_permutation_entropy(signal1)
        pe2 = calculate_permutation_entropy(signal2)
        
        # Values should differ (with very high probability)
        assert lzc1 != lzc2 or pe1 != pe2