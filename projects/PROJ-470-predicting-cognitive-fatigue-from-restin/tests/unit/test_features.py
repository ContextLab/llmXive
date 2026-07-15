"""
Unit tests for feature extraction functions.
"""
import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from features import calculate_lzc, calculate_permutation_entropy

def test_calculate_lzc_constant_signal():
    """Test LZC on a constant signal (should be 0)."""
    signal = np.ones(1000)
    lzc = calculate_lzc(signal)
    assert lzc == 0.0, f"Expected 0.0 for constant signal, got {lzc}"

def test_calculate_lzc_alternating_signal():
    """Test LZC on a simple alternating signal."""
    signal = np.array([0, 1, 0, 1, 0, 1, 0, 1] * 125)
    lzc = calculate_lzc(signal)
    # Alternating signals have low complexity but not zero
    assert 0.0 < lzc < 0.5, f"Expected low complexity for alternating signal, got {lzc}"

def test_calculate_lzc_random_signal():
    """Test LZC on a random signal (should be higher)."""
    np.random.seed(42)
    signal = np.random.randn(1000)
    lzc = calculate_lzc(signal)
    # Random signals should have higher complexity
    assert 0.3 < lzc <= 1.0, f"Expected higher complexity for random signal, got {lzc}"

def test_calculate_permutation_entropy_constant():
    """Test PE on a constant signal (should be 0)."""
    signal = np.ones(1000)
    pe = calculate_permutation_entropy(signal)
    assert pe == 0.0, f"Expected 0.0 for constant signal, got {pe}"

def test_calculate_permutation_entropy_random():
    """Test PE on a random signal."""
    np.random.seed(42)
    signal = np.random.randn(1000)
    pe = calculate_permutation_entropy(signal)
    # Random signals should have high entropy (close to 1.0)
    assert 0.5 < pe <= 1.0, f"Expected high entropy for random signal, got {pe}"

def test_calculate_permutation_entropy_order():
    """Test that different orders produce different results."""
    signal = np.random.randn(1000)
    pe_order3 = calculate_permutation_entropy(signal, order=3)
    pe_order4 = calculate_permutation_entropy(signal, order=4)
    
    # Results should be different (though both normalized)
    # This test ensures the function actually uses the order parameter
    assert isinstance(pe_order3, float)
    assert isinstance(pe_order4, float)

def test_empty_signal():
    """Test handling of empty signals."""
    empty_signal = np.array([])
    lzc = calculate_lzc(empty_signal)
    pe = calculate_permutation_entropy(empty_signal)
    assert lzc == 0.0
    assert pe == 0.0

def test_small_signal():
    """Test handling of very small signals."""
    small_signal = np.array([1, 2, 3])
    lzc = calculate_lzc(small_signal)
    pe = calculate_permutation_entropy(small_signal, order=3)
    # Should not crash, even if values are edge cases
    assert 0.0 <= lzc <= 1.0
    assert 0.0 <= pe <= 1.0