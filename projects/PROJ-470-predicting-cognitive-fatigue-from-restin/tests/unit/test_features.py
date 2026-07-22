import pytest
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path to import features module
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from features import calculate_lzc, calculate_permutation_entropy

def test_lzc_white_noise_range():
    """
    Test that LZC calculation on synthetic white noise returns a value
    within the expected range (0.45 < value < 0.55).
    """
    # Generate synthetic white noise: sufficient size, amplitude, sampling rate context
    # Using 10,000 samples to ensure statistical stability for LZC
    np.random.seed(42)
    white_noise = np.random.randn(10000) * 100  # Amplitude scaling doesn't affect binary LZC
    
    lzc_value = calculate_lzc(white_noise)
    
    # Assert the value is within the expected range for white noise
    assert 0.45 < lzc_value < 0.55, f"LZC value {lzc_value} outside expected range (0.45, 0.55)"

def test_permutation_entropy_white_noise_range():
    """
    Test that Permutation Entropy calculation on synthetic white noise returns a value
    within the expected range (0.9 < value < 1.1).
    """
    # Generate synthetic white noise
    np.random.seed(42)
    white_noise = np.random.randn(10000)
    
    pe_value = calculate_permutation_entropy(white_noise, order=3, delay=1)
    
    # Permutation entropy is normalized to [0, 1], so for white noise it should be close to 1.0
    # The range 0.9 < value < 1.1 accounts for normalization edge cases
    assert 0.9 < pe_value < 1.1, f"PE value {pe_value} outside expected range (0.9, 1.1)"

def test_lzc_constant_signal():
    """
    Test that LZC of a constant signal (zero complexity) is 0.0.
    """
    constant_signal = np.ones(1000)
    lzc_value = calculate_lzc(constant_signal)
    assert lzc_value == 0.0, f"Constant signal LZC should be 0.0, got {lzc_value}"

def test_permutation_entropy_constant_signal():
    """
    Test that Permutation Entropy of a constant signal is 0.0.
    """
    constant_signal = np.ones(1000)
    pe_value = calculate_permutation_entropy(constant_signal, order=3, delay=1)
    assert pe_value == 0.0, f"Constant signal PE should be 0.0, got {pe_value}"
