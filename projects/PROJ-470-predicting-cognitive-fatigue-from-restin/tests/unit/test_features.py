"""
Unit tests for feature extraction module (T014, T015).
Tests LZC and Permutation Entropy on synthetic signals.
"""
import pytest
import numpy as np
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from features import calculate_lzc, calculate_permutation_entropy

def test_lzc_white_noise():
    """
    Unit test for LZC calculation on white noise (synthetic).
    T014 Verification: Generate white noise, assert valid numeric float and not NaN.
    """
    # Generate synthetic signal: white noise, seed=42, normalized
    np.random.seed(42)
    duration = 120  # seconds
    fs = 256        # Hz
    n_samples = duration * fs
    signal = np.random.normal(0, 1, n_samples) # Amplitude normalized to unity (std=1)

    # Calculate LZC
    try:
        lzc_val = calculate_lzc(signal)
    except ImportError:
        pytest.skip("lempel_ziv_complexity not installed")

    assert isinstance(lzc_val, float), "LZC value must be a float"
    assert not np.isnan(lzc_val), "LZC value must not be NaN"
    # LZC for white noise should be non-zero and typically high (complex)
    assert lzc_val > 0, "LZC for white noise should be positive"
    print(f"LZC (white noise): {lzc_val}")

def test_pe_white_noise():
    """
    Unit test for Permutation Entropy on white noise (synthetic).
    T015 Verification: Generate white noise, assert valid numeric float and not NaN.
    """
    # Generate synthetic signal: white noise, seed=42, normalized
    np.random.seed(42)
    duration = 120  # seconds
    fs = 256        # Hz
    n_samples = duration * fs
    signal = np.random.normal(0, 1, n_samples)

    # Calculate PE
    try:
        pe_val = calculate_permutation_entropy(signal, order=3, delay=1)
    except ImportError:
        pytest.skip("nolds not installed")

    assert isinstance(pe_val, float), "PE value must be a float"
    assert not np.isnan(pe_val), "PE value must not be NaN"
    # PE for white noise should be close to log2(order!) (max entropy)
    # order=3 -> 3! = 6 -> log2(6) ≈ 2.58
    # It won't be exactly that due to finite samples, but should be in range.
    assert 0 < pe_val < 3.0, f"PE for white noise should be in reasonable range, got {pe_val}"
    print(f"PE (white noise): {pe_val}")

def test_lzc_sine_wave():
    """
    Test LZC on a simple sine wave (low complexity).
    """
    fs = 256
    t = np.linspace(0, 120, 120 * fs)
    signal = np.sin(2 * np.pi * 10 * t) # 10 Hz sine

    try:
        lzc_val = calculate_lzc(signal)
    except ImportError:
        pytest.skip("lempel_ziv_complexity not installed")

    assert isinstance(lzc_val, float)
    assert not np.isnan(lzc_val)
    # Sine wave should have lower complexity than white noise
    print(f"LZC (sine wave): {lzc_val}")

def test_pe_sine_wave():
    """
    Test PE on a simple sine wave (low entropy).
    """
    fs = 256
    t = np.linspace(0, 120, 120 * fs)
    signal = np.sin(2 * np.pi * 10 * t)

    try:
        pe_val = calculate_permutation_entropy(signal, order=3, delay=1)
    except ImportError:
        pytest.skip("nolds not installed")

    assert isinstance(pe_val, float)
    assert not np.isnan(pe_val)
    print(f"PE (sine wave): {pe_val}")
