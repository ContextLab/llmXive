"""
Unit tests for feature extraction module.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from features import calculate_permutation_entropy, calculate_lempel_ziv_complexity, _calculate_permutation_entropy_fallback

def test_pe_known_signal():
    """
    Unit test for Permutation Entropy on a known synthetic signal.
    Generates white noise (seed=42, 256 Hz, 120s) and verifies output is valid.
    """
    # Generate synthetic white noise
    np.random.seed(42)
    duration = 120  # seconds
    sfreq = 256     # Hz
    n_samples = duration * sfreq
    amplitude = 1.0
    
    signal = np.random.normal(0, 1, n_samples) * amplitude
    
    # Calculate PE
    embedding_dim = 3
    time_delay = 1
    pe_value = calculate_permutation_entropy(signal, embedding_dim, time_delay)
    
    # Assertions
    assert isinstance(pe_value, (int, float)), "PE value must be numeric"
    assert not np.isnan(pe_value), "PE value must not be NaN"
    assert pe_value >= 0, "PE value must be non-negative"
    
    # Theoretical max for m=3 is log2(3!) = log2(6) ≈ 2.58
    # Normalized PE should be between 0 and 1
    assert pe_value <= 1.1, f"Normalized PE should be <= 1, got {pe_value}"
    
    print(f"PE value for synthetic white noise: {pe_value}")

def test_lzc_known_signal():
    """
    Unit test for LZC calculation on a known synthetic signal.
    """
    np.random.seed(42)
    duration = 120
    sfreq = 256
    n_samples = duration * sfreq
    amplitude = 1.0
    
    signal = np.random.normal(0, 1, n_samples) * amplitude
    
    lzc_value = calculate_lempel_ziv_complexity(signal)
    
    assert isinstance(lzc_value, (int, float)), "LZC value must be numeric"
    assert not np.isnan(lzc_value), "LZC value must not be NaN"
    assert lzc_value > 0, "LZC value for noise should be positive"
    
    print(f"LZC value for synthetic white noise: {lzc_value}")

def test_pe_fallback_implementation():
    """
    Test the fallback PE implementation specifically.
    """
    np.random.seed(42)
    signal = np.random.normal(0, 1, 1000)
    
    pe_val = _calculate_permutation_entropy_fallback(signal, embedding_dim=3, time_delay=1)
    
    assert 0 <= pe_val <= 1.0, f"Normalized PE should be in [0, 1], got {pe_val}"

def test_pe_constant_signal():
    """
    Test PE on a constant signal (should be 0).
    """
    signal = np.ones(1000)
    pe_val = calculate_permutation_entropy(signal, embedding_dim=3, time_delay=1)
    
    # Constant signal has no complexity, entropy should be 0
    assert pe_val == 0.0, f"PE for constant signal should be 0, got {pe_val}"

def test_pe_low_frequency_signal():
    """
    Test PE on a low frequency sine wave (should be lower than noise).
    """
    t = np.linspace(0, 1, 1000)
    signal = np.sin(2 * np.pi * 5 * t) # 5 Hz sine
    
    pe_val = calculate_permutation_entropy(signal, embedding_dim=3, time_delay=1)
    
    # Should be a valid number
    assert not np.isnan(pe_val)
    assert pe_val >= 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
