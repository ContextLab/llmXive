"""
Unit tests for feature extraction (LZC and Permutation Entropy).

Tests:
- T012: Unit test for LZC calculation on known signal.
- T013: Unit test for Permutation Entropy on known signal.
"""
import sys
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from features import calculate_lzc, calculate_permutation_entropy

def test_lzc_on_constant_signal():
    """
    T012: LZC of a constant signal should be 0 (or very close to 0).
    A constant signal has no new patterns.
    """
    # Create a constant signal
    signal = np.ones(1000)
    lzc = calculate_lzc(signal)
    
    # LZC is normalized to [0, 1]. Constant should be 0.
    assert lzc == 0.0, f"Expected LZC=0.0 for constant signal, got {lzc}"
    print("T012 PASSED: LZC on constant signal is 0.0")

def test_lzc_on_random_signal():
    """
    T012: LZC of a random signal should be high (close to 1).
    """
    # Create a random signal
    np.random.seed(42)
    signal = np.random.randn(1000)
    lzc = calculate_lzc(signal)
    
    # Random noise should have high complexity
    assert lzc > 0.5, f"Expected LZC > 0.5 for random signal, got {lzc}"
    print(f"T012 PASSED: LZC on random signal is {lzc:.4f} (> 0.5)")

def test_pe_on_constant_signal():
    """
    T013: Permutation Entropy of a constant signal should be 0.
    A constant signal has only one ordinal pattern (all equal), 
    resulting in zero entropy.
    """
    signal = np.ones(1000)
    pe = calculate_permutation_entropy(signal)
    
    assert pe == 0.0, f"Expected PE=0.0 for constant signal, got {pe}"
    print("T013 PASSED: PE on constant signal is 0.0")

def test_pe_on_random_signal():
    """
    T013: Permutation Entropy of a random signal should be high.
    Max PE for embedding dimension d is log(d!).
    """
    np.random.seed(42)
    signal = np.random.randn(1000)
    pe = calculate_permutation_entropy(signal)
    
    # PE is normalized to [0, 1]. Random should be close to 1.
    assert pe > 0.5, f"Expected PE > 0.5 for random signal, got {pe}"
    print(f"T013 PASSED: PE on random signal is {pe:.4f} (> 0.5)")

if __name__ == "__main__":
    test_lzc_on_constant_signal()
    test_lzc_on_random_signal()
    test_pe_on_constant_signal()
    test_pe_on_random_signal()
    print("All unit tests for features passed.")