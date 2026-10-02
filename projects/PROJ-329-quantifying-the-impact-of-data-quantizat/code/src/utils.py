"""
Utility functions for quantization logic (Fixed FSR) and SNR calculation helpers.

This module provides the core mathematical operations required for:
1. Fixed Full-Scale Range (FSR) quantization of gravitational wave signals.
2. Signal-to-Noise Ratio (SNR) calculation for injected signals.
3. Validation of quantization levels.

Imports:
    numpy (from requirements.txt)
    typing (standard library)
"""

import numpy as np
from typing import Tuple, Union, Optional, List


def get_quantization_levels(n_bits: int) -> int:
    """
    Calculate the number of discrete levels for a given bit depth.
    
    Args:
        n_bits: The bit depth (e.g., 8, 16).
        
    Returns:
        The total number of quantization levels (2^n_bits).
        
    Raises:
        ValueError: If n_bits is not a positive integer.
    """
    if not isinstance(n_bits, int) or n_bits <= 0:
        raise ValueError(f"n_bits must be a positive integer, got {n_bits}")
    return 1 << n_bits  # 2 ** n_bits


def calculate_optimal_fsr(signal: np.ndarray, n_bits: int) -> float:
    """
    Calculate the optimal Full-Scale Range (FSR) to minimize quantization error
    for a given signal and bit depth.
    
    The optimal FSR is determined by the maximum absolute amplitude of the signal,
    ensuring the signal fits within the quantization range without clipping,
    while maximizing resolution.
    
    Args:
        signal: The input waveform array (float64).
        n_bits: The target bit depth.
        
    Returns:
        The optimal FSR value (float).
    """
    max_amplitude = np.max(np.abs(signal))
    if max_amplitude == 0:
        return 1.0  # Default FSR for zero signal
    return max_amplitude


def quantize_fixed_fsr(
    signal: np.ndarray, 
    n_bits: int, 
    fsr: Optional[float] = None
) -> np.ndarray:
    """
    Apply Fixed Full-Scale Range (FSR) quantization to a signal.
    
    This function maps continuous float64 signal values to discrete integer levels
    within the range [-2^(n_bits-1), 2^(n_bits-1) - 1] (signed integer representation),
    then scales them back to the original amplitude range.
    
    The quantization process:
    1. Determine FSR (max amplitude if not provided).
    2. Normalize signal to [-1, 1] range.
    3. Map to discrete levels.
    4. Scale back to original amplitude.
    
    Args:
        signal: Input waveform array (float64).
        n_bits: Target bit depth (e.g., 8, 16).
        fsr: Optional fixed full-scale range. If None, calculated from signal max.
        
    Returns:
        Quantized signal array (float64), with values at discrete levels.
        
    Raises:
        ValueError: If n_bits is invalid or signal is empty.
    """
    if n_bits <= 0:
        raise ValueError(f"n_bits must be positive, got {n_bits}")
    if signal.size == 0:
        raise ValueError("Signal array cannot be empty")
    
    # Calculate or use provided FSR
    if fsr is None:
        fsr = calculate_optimal_fsr(signal, n_bits)
    
    # Number of levels
    num_levels = get_quantization_levels(n_bits)
    
    # Quantization step size (delta)
    # For signed representation: range is [-FSR, FSR)
    # Delta = 2 * FSR / num_levels
    delta = (2.0 * fsr) / num_levels
    
    # Normalize signal to [-1, 1] range relative to FSR
    # signal_norm = signal / fsr
    # Clamp to [-1, 1] to handle any slight overshoots
    signal_norm = np.clip(signal / fsr, -1.0, 1.0 - 1e-15)
    
    # Map to integer levels: round to nearest integer
    # Level range: [-num_levels/2, num_levels/2 - 1]
    levels = np.round(signal_norm * (num_levels / 2))
    
    # Clamp levels to valid range to ensure no overflow
    min_level = -num_levels // 2
    max_level = (num_levels // 2) - 1
    levels = np.clip(levels, min_level, max_level)
    
    # Convert back to amplitude
    quantized_signal = levels * delta
    
    return quantized_signal


def calculate_snr(
    signal: np.ndarray, 
    noise_psd: Optional[np.ndarray] = None,
    sample_rate: float = 4096.0,
    noise_std: Optional[float] = None
) -> float:
    """
    Calculate the Signal-to-Noise Ratio (SNR) of a signal.
    
    Two modes of operation:
    1. If noise_psd is provided: Calculate matched-filter SNR using the PSD.
    2. If noise_std is provided: Calculate SNR as mean(signal)/std(noise).
    3. If neither: Estimate noise from the signal tail (assuming signal is transient).
    
    For this pilot implementation, we use a simplified SNR calculation:
    SNR = (RMS of signal) / (RMS of noise)
    
    Args:
        signal: The waveform array (float64).
        noise_psd: Optional Power Spectral Density array (not used in simplified mode).
        sample_rate: Sample rate in Hz (default 4096 Hz for LIGO O3).
        noise_std: Optional known noise standard deviation.
        
    Returns:
        The calculated SNR (float).
        
    Raises:
        ValueError: If signal is empty.
    """
    if signal.size == 0:
        raise ValueError("Signal array cannot be empty")
    
    # Simplified SNR calculation for pilot:
    # We assume the signal is injected into noise, so we estimate noise from
    # the tail of the signal (last 20% of samples) where signal is negligible
    
    tail_start = int(len(signal) * 0.8)
    noise_segment = signal[tail_start:]
    
    if len(noise_segment) == 0:
        # Fallback: use entire signal if too short
        noise_segment = signal
    
    # Estimate noise standard deviation from the tail
    if noise_std is not None:
        noise_rms = noise_std
    else:
        noise_rms = np.std(noise_segment)
    
    # Signal RMS (total power)
    signal_rms = np.sqrt(np.mean(signal**2))
    
    if noise_rms == 0:
        return float('inf')
    
    snr = signal_rms / noise_rms
    return float(snr)


def verify_quantization_levels(
    quantized_signal: np.ndarray, 
    n_bits: int, 
    tolerance: float = 1e-10
) -> Tuple[bool, int, int]:
    """
    Verify that a quantized signal contains no more than 2^n_bits unique levels.
    
    This function counts the unique values in the quantized signal and compares
    it against the theoretical maximum number of levels (2^n_bits).
    
    Args:
        quantized_signal: The quantized waveform array (float64).
        n_bits: The bit depth used for quantization.
        tolerance: Floating point tolerance for comparing values (default 1e-10).
        
    Returns:
        Tuple of (is_valid, unique_count, max_allowed):
            - is_valid: True if unique_count <= 2^n_bits
            - unique_count: Number of unique values found
            - max_allowed: Maximum allowed unique values (2^n_bits)
    """
    max_allowed = get_quantization_levels(n_bits)
    
    # Round to tolerance to handle floating point artifacts
    rounded_signal = np.round(quantized_signal / tolerance) * tolerance
    unique_values = np.unique(rounded_signal)
    unique_count = len(unique_values)
    
    is_valid = unique_count <= max_allowed
    
    return is_valid, unique_count, max_allowed
