"""
Data Transform Module.

Implements downsampling and quantization of strain data.

This module ensures strict typing and comprehensive documentation
as per task T039 requirements.
"""
import logging
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def validate_nyquist_compliance(data: np.ndarray, original_rate: float, target_rate: float) -> bool:
    """
    Validate Nyquist limit compliance before downsampling.
    
    Args:
        data: Input strain data.
        original_rate: Original sampling rate.
        target_rate: Target sampling rate.
        
    Returns:
        True if compliant, False otherwise.
    """
    if target_rate >= original_rate / 2:
        return True
    
    # Check dominant frequency
    n = len(data)
    frequencies = fftfreq(n, 1/original_rate)
    spectrum = np.abs(fft(data))
    dominant_freq = frequencies[np.argmax(spectrum[1:n//2])] + frequencies[1]
    
    if dominant_freq > target_rate / 2:
        logger.warning(f"Dominant frequency {dominant_freq} Hz exceeds Nyquist limit {target_rate/2} Hz")
        return False
    
    return True

def downsample_strain_data(data: np.ndarray, original_rate: float, target_rate: float) -> np.ndarray:
    """
    Downsample strain data using scipy.signal.decimate.
    
    Args:
        data: Input strain data.
        original_rate: Original sampling rate.
        target_rate: Target sampling rate.
        
    Returns:
        Downsampled data.
    """
    factor = int(original_rate / target_rate)
    if original_rate % target_rate != 0:
        raise ValueError("Target rate must be an integer divisor of original rate")
    
    return signal.decimate(data, factor, ftype='iir')

def quantize_strain_data(data: np.ndarray, bit_depth: int) -> np.ndarray:
    """
    Quantize strain data to a specific bit depth.
    
    Args:
        data: Input strain data.
        bit_depth: Target bit depth (e.g., 16, 32).
        
    Returns:
        Quantized data.
    """
    if bit_depth == 32:
        return data.astype(np.float32)
    elif bit_depth == 16:
        # Simulate 16-bit float (half precision)
        return data.astype(np.float16)
    else:
        raise ValueError(f"Unsupported bit depth: {bit_depth}")

def apply_resolution_transforms(data: np.ndarray, original_rate: float, 
                                target_rate: float, bit_depth: int) -> np.ndarray:
    """
    Apply both downsampling and quantization.
    
    Args:
        data: Input strain data.
        original_rate: Original sampling rate.
        target_rate: Target sampling rate.
        bit_depth: Target bit depth.
        
    Returns:
        Transformed data.
    """
    # Validate Nyquist
    if not validate_nyquist_compliance(data, original_rate, target_rate):
        logger.warning("Nyquist compliance failed, proceeding with caution")
    
    # Downsample
    downsampled = downsample_strain_data(data, original_rate, target_rate)
    
    # Quantize
    quantized = quantize_strain_data(downsampled, bit_depth)
    
    return quantized

def generate_all_resolutions(data: np.ndarray, original_rate: float, 
                             resolutions: List[Tuple[float, int]]) -> Dict[str, np.ndarray]:
    """
    Generate data for all target resolutions.
    
    Args:
        data: Input strain data.
        original_rate: Original sampling rate.
        resolutions: List of (target_rate, bit_depth) tuples.
        
    Returns:
        Dictionary mapping resolution key to data.
    """
    results = {}
    for rate, depth in resolutions:
        key = f"{rate}Hz_{depth}bit"
        results[key] = apply_resolution_transforms(data, original_rate, rate, depth)
    return results

def main() -> None:
    """
    Main entry point for transform script.
    """
    logger.info("Transform module loaded.")

if __name__ == '__main__':
    main()
