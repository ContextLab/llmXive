import numpy as np
from typing import Tuple, Union, Optional

def quantize_fixed_fsr(signal: np.ndarray, bits: int, fsr: Optional[float] = None) -> np.ndarray:
    """
    Apply Fixed Full-Scale Range (FSR) quantization to a signal.
    
    This function implements the quantization logic required for FR-002.
    It maps floating point signal values to discrete integer levels within
    a specified Full-Scale Range (FSR).
    
    Parameters
    ----------
    signal : np.ndarray
        Input signal array (float64).
    bits : int
        Number of bits for quantization.
    fsr : float, optional
        Full-Scale Range. If None, inferred as 2 * max(|signal|) to ensure
        the signal fits within the range without clipping, unless the signal
        is empty.
        
    Returns
    -------
    np.ndarray
        Quantized signal (float64), reconstructed from integer levels.
        
    Notes
    -----
    - The number of quantization levels is L = 2^bits.
    - The step size is delta = FSR / L.
    - Values outside [-FSR/2, FSR/2] are clipped to the nearest boundary.
    """
    if bits <= 0:
        raise ValueError(f"Bits must be positive, got {bits}")
        
    num_levels = 1 << bits  # 2^bits
    
    # Determine FSR if not provided
    if fsr is None:
        if signal.size == 0:
            fsr = 1.0
        else:
            # Set FSR to cover the range of the signal with a small margin
            # to prevent clipping of the absolute max, or strictly use max range
            max_val = np.max(np.abs(signal))
            if max_val == 0:
                fsr = 1.0
            else:
                fsr = 2.0 * max_val
    
    half_fsr = fsr / 2.0
    delta = fsr / num_levels
    
    # Normalize signal to [-half_fsr, half_fsr] range
    # Clip to handle any values outside the FSR
    clipped_signal = np.clip(signal, -half_fsr, half_fsr)
    
    # Quantization:
    # 1. Shift to [0, FSR]
    shifted = clipped_signal + half_fsr
    # 2. Scale to [0, num_levels]
    scaled = shifted / delta
    # 3. Round to nearest integer (quantize)
    # We use np.round to handle the discrete levels. 
    # To ensure we stay within [0, num_levels-1], we clip again after rounding
    quantized_int = np.round(scaled).astype(np.int32)
    quantized_int = np.clip(quantized_int, 0, num_levels - 1)
    
    # Reconstruct:
    # 1. Scale back to [0, FSR]
    reconstructed_shifted = quantized_int * delta
    # 2. Shift back to [-half_fsr, half_fsr]
    reconstructed = reconstructed_shifted - half_fsr
    
    return reconstructed

def calculate_snr(signal: np.ndarray, noise: np.ndarray) -> float:
    """
    Calculate the Signal-to-Noise Ratio (SNR) of a signal injected into noise.
    
    Parameters
    ----------
    signal : np.ndarray
        Signal array.
    noise : np.ndarray
        Noise array (assumed to be zero-mean or the noise component).
        
    Returns
    -------
    float
        Calculated SNR.
    """
    # Simple energy ratio SNR: E_signal / E_noise
    # In GW analysis, matched filtering SNR is often used, but for
    # this utility, we use the standard power ratio definition.
    signal_power = np.mean(signal ** 2)
    noise_power = np.mean(noise ** 2)
    
    if noise_power == 0:
        return float('inf')
        
    return float(np.sqrt(signal_power / noise_power))

def calculate_optimal_fsr(signal: np.ndarray) -> float:
    """
    Calculate the optimal FSR to minimize clipping for a given signal.
    
    Parameters
    ----------
    signal : np.ndarray
        Input signal array.
        
    Returns
    -------
    float
        Optimal FSR value (2 * max(|signal|)).
    """
    if signal.size == 0:
        return 1.0
    return 2.0 * np.max(np.abs(signal))

def get_quantization_levels(bits: int) -> int:
    """
    Get the number of quantization levels for a given bit depth.
    
    Parameters
    ----------
    bits : int
        Number of bits.
        
    Returns
    -------
    int
        Number of levels (2^bits).
    """
    return 1 << bits

def verify_quantization_levels(quantized_signal: np.ndarray, bits: int) -> bool:
    """
    Verify that the quantized signal contains no more than 2^bits unique levels.
    
    Parameters
    ----------
    quantized_signal : np.ndarray
        Quantized signal array.
    bits : int
        Expected bit depth.
        
    Returns
    -------
    bool
        True if unique levels <= 2^bits, False otherwise.
    """
    num_levels = get_quantization_levels(bits)
    unique_count = len(np.unique(quantized_signal))
    return unique_count <= num_levels
