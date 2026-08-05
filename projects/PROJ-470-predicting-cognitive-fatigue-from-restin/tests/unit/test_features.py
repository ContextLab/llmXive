import pytest
import numpy as np
import sys
import os
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from features import calculate_permutation_entropy, calculate_lempel_ziv_complexity

def test_pe_known_signal():
    """
    Unit test for Permutation Entropy on a known synthetic signal.
    Generates white noise and verifies PE is a valid positive float.
    """
    # Generate synthetic white noise signal
    np.random.seed(42)
    sampling_rate = 256  # Hz
    duration = 120  # seconds
    n_samples = sampling_rate * duration
    amplitude = 1.0
    
    signal = np.random.normal(0, amplitude, n_samples)
    
    # Calculate Permutation Entropy
    embedding_dim = 3
    time_delay = 1
    pe_value = calculate_permutation_entropy(signal, embedding_dim, time_delay)
    
    # Assertions
    assert isinstance(pe_value, float), "PE value should be a float"
    assert not np.isnan(pe_value), "PE value should not be NaN"
    assert pe_value >= 0.0, "PE value should be non-negative"
    assert pe_value <= 1.0, "PE value should be <= 1.0 (normalized)"
    
    # For white noise, PE should be relatively high (close to 1)
    # but not exactly 1 due to finite sample size
    assert pe_value > 0.5, "White noise should have high permutation entropy"
    
    print(f"Permutation Entropy for white noise: {pe_value:.4f}")

def test_lzc_known_signal():
    """
    Unit test for LZC calculation on a known synthetic signal.
    Generates white noise and verifies LZC is a valid positive float.
    """
    # Generate synthetic white noise signal
    np.random.seed(42)
    sampling_rate = 256  # Hz
    duration = 120  # seconds
    n_samples = sampling_rate * duration
    amplitude = 1.0
    
    signal = np.random.normal(0, amplitude, n_samples)
    
    # Calculate LZC
    lzc_value = calculate_lempel_ziv_complexity(signal, sampling_rate)
    
    # Assertions
    assert isinstance(lzc_value, float), "LZC value should be a float"
    assert not np.isnan(lzc_value), "LZC value should not be NaN"
    assert lzc_value >= 0.0, "LZC value should be non-negative"
    
    print(f"Lempel-Ziv Complexity for white noise: {lzc_value:.4f}")

def test_pe_sine_wave():
    """
    Test Permutation Entropy on a simple sine wave.
    Sine waves should have lower PE than white noise.
    """
    # Generate sine wave
    sampling_rate = 256
    duration = 120
    n_samples = sampling_rate * duration
    frequency = 10  # Hz
    
    t = np.linspace(0, duration, n_samples)
    signal = np.sin(2 * np.pi * frequency * t)
    
    # Calculate PE
    embedding_dim = 3
    time_delay = 1
    pe_value = calculate_permutation_entropy(signal, embedding_dim, time_delay)
    
    # Assertions
    assert isinstance(pe_value, float), "PE value should be a float"
    assert not np.isnan(pe_value), "PE value should not be NaN"
    assert pe_value >= 0.0, "PE value should be non-negative"
    assert pe_value <= 1.0, "PE value should be <= 1.0 (normalized)"
    
    # Sine wave should have lower PE than white noise
    assert pe_value < 0.5, "Sine wave should have lower permutation entropy than white noise"
    
    print(f"Permutation Entropy for sine wave: {pe_value:.4f}")

def test_pe_edge_case_constant():
    """
    Test Permutation Entropy on a constant signal.
    Constant signal should have PE = 0.
    """
    signal = np.ones(1000) * 5.0
    
    pe_value = calculate_permutation_entropy(signal, embedding_dim=3, time_delay=1)
    
    assert pe_value == 0.0, "Constant signal should have PE = 0"
    print(f"Permutation Entropy for constant signal: {pe_value:.4f}")

def test_pe_edge_case_short_signal():
    """
    Test Permutation Entropy on a very short signal.
    Should handle gracefully and return 0 or a valid value.
    """
    signal = np.random.normal(0, 1, 10)  # Very short signal
    
    pe_value = calculate_permutation_entropy(signal, embedding_dim=3, time_delay=1)
    
    # Should not crash and should return a valid float
    assert isinstance(pe_value, float), "PE value should be a float"
    assert not np.isnan(pe_value), "PE value should not be NaN"
    print(f"Permutation Entropy for short signal: {pe_value:.4f}")
