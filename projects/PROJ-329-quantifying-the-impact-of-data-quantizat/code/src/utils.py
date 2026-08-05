"""
Utility functions for gravitational wave signal analysis.

Provides:
- Fixed Full-Scale Range (FSR) quantization logic
- SNR calculation helpers
- Quantization level verification
"""
import numpy as np
from typing import Tuple, Union, Optional


def get_quantization_levels(bit_depth: int) -> int:
    """
    Calculate the number of discrete levels for a given bit depth.
    
    Args:
        bit_depth: Number of bits for quantization (e.g., 1, 8, 16)
        
    Returns:
        Number of discrete levels (2^bit_depth)
    """
    if bit_depth < 1:
        raise ValueError("Bit depth must be at least 1")
    return 2 ** bit_depth


def calculate_optimal_fsr(signal: np.ndarray) -> float:
    """
    Calculate the optimal Full-Scale Range (FSR) based on signal amplitude.
    
    The FSR is set to cover the full range of the signal, from minimum to maximum.
    
    Args:
        signal: Input signal array (numpy array)
        
    Returns:
        FSR value (float)
    """
    signal_min = np.min(signal)
    signal_max = np.max(signal)
    return float(signal_max - signal_min)


def quantize_fixed_fsr(
    signal: np.ndarray,
    bit_depth: int,
    fsr: Optional[float] = None
) -> np.ndarray:
    """
    Apply Fixed Full-Scale Range (FSR) quantization to a signal.
    
    This function quantizes the input signal to a specified number of bits
    using a fixed full-scale range. If FSR is not provided, it is calculated
    from the signal's amplitude range.
    
    Args:
        signal: Input signal array (numpy array)
        bit_depth: Number of bits for quantization (e.g., 1, 8, 16)
        fsr: Optional full-scale range. If None, calculated from signal.
            
    Returns:
        Quantized signal array (numpy array)
        
    Raises:
        ValueError: If bit_depth < 1 or signal is empty
    """
    if bit_depth < 1:
        raise ValueError("Bit depth must be at least 1")
    
    if len(signal) == 0:
        raise ValueError("Signal cannot be empty")
    
    signal = np.asarray(signal, dtype=np.float64)
    
    # Calculate FSR if not provided
    if fsr is None:
        fsr = calculate_optimal_fsr(signal)
    
    if fsr == 0:
        # Handle constant signal case
        return np.zeros_like(signal)
    
    # Number of quantization levels
    num_levels = get_quantization_levels(bit_depth)
    
    # Normalize signal to [0, 1] range based on FSR
    # Center the FSR around the signal mean to handle bipolar signals
    signal_center = np.mean(signal)
    signal_normalized = (signal - signal_center) / (fsr / 2)
    
    # Clip to [-1, 1] to handle outliers
    signal_normalized = np.clip(signal_normalized, -1.0, 1.0)
    
    # Map to discrete levels [0, num_levels-1]
    # Scale from [-1, 1] to [0, num_levels-1]
    signal_quantized_idx = ((signal_normalized + 1.0) / 2.0) * (num_levels - 1)
    
    # Round to nearest integer
    signal_quantized_idx = np.round(signal_quantized_idx).astype(np.int64)
    
    # Map back to amplitude range
    # Scale from [0, num_levels-1] to [-fsr/2, fsr/2]
    signal_quantized = (signal_quantized_idx / (num_levels - 1) - 0.5) * fsr + signal_center
    
    return signal_quantized


def calculate_snr(
    signal: np.ndarray,
    noise: Optional[np.ndarray] = None,
    noise_power: Optional[float] = None
) -> float:
    """
    Calculate the Signal-to-Noise Ratio (SNR) for a given signal.
    
    Args:
        signal: Signal array (numpy array)
        noise: Optional noise array. If provided, SNR is calculated as
               signal_power / noise_power.
        noise_power: Optional pre-computed noise power. If provided, used instead
                    of calculating from noise array.
                    
    Returns:
        SNR value (float). If no noise info provided, returns signal power.
        
    Raises:
        ValueError: If both noise and noise_power are None, or if signal is empty
    """
    if len(signal) == 0:
        raise ValueError("Signal cannot be empty")
    
    signal_power = np.mean(signal ** 2)
    
    if noise is not None:
        if len(noise) != len(signal):
            raise ValueError("Signal and noise arrays must have the same length")
        noise_power_actual = np.mean(noise ** 2)
        if noise_power_actual == 0:
            return float('inf')
        return float(signal_power / noise_power_actual)
    elif noise_power is not None:
        if noise_power == 0:
            return float('inf')
        return float(signal_power / noise_power)
    else:
        raise ValueError("Either 'noise' array or 'noise_power' must be provided")


def verify_quantization_levels(
    quantized_signal: np.ndarray,
    bit_depth: int,
    tolerance: float = 1e-10
) -> Tuple[bool, int]:
    """
    Verify that a quantized signal has the expected number of unique levels.
    
    Args:
        quantized_signal: Quantized signal array (numpy array)
        bit_depth: Expected bit depth
        tolerance: Tolerance for floating-point comparison when counting levels
                    
    Returns:
        Tuple of (is_valid, actual_num_levels)
        - is_valid: True if actual levels <= expected levels
        - actual_num_levels: Number of unique levels found in the signal
    """
    expected_levels = get_quantization_levels(bit_depth)
    
    # Count unique levels with tolerance
    # Round to nearest representable value to handle floating-point errors
    rounded_signal = np.round(quantized_signal / tolerance) * tolerance
    actual_levels = len(np.unique(rounded_signal))
    
    is_valid = actual_levels <= expected_levels
    
    return is_valid, actual_levels