"""
Metrics module for evaluating compression quality.

Computes Mean Squared Error (MSE) and Signal-to-Noise Ratio (SNR) degradation
between original and reconstructed (decompressed) waveform data.

Precision for SNR is maintained at ≥ 0.1 dB as required by SC-002.
"""

import numpy as np
from typing import Tuple, Optional
import logging

from src.utils.logging import get_logger

logger = get_logger(__name__)


def compute_mse(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """
    Compute Mean Squared Error between original and reconstructed signals.
    
    Args:
        original: Original strain time series (numpy array).
        reconstructed: Reconstructed strain time series after decompression.
        
    Returns:
        MSE value as a float.
        
    Raises:
        ValueError: If input arrays have different shapes or are empty.
    """
    if original.shape != reconstructed.shape:
        raise ValueError(
            f"Shape mismatch: original {original.shape} vs reconstructed {reconstructed.shape}"
        )
    
    if original.size == 0:
        raise ValueError("Input arrays cannot be empty.")
    
    mse = np.mean((original - reconstructed) ** 2)
    return float(mse)


def compute_snr_degradation(
    original: np.ndarray, reconstructed: np.ndarray, fs: float = 4096.0
) -> float:
    """
    Compute SNR degradation in decibels (dB) between original and reconstructed signals.
    
    SNR is calculated as:
      SNR = 10 * log10(signal_power / noise_power)
    where noise_power is the power of the difference (error) signal.
    
    Degradation is defined as:
      Degradation (dB) = SNR_original - SNR_reconstructed
    However, since we are comparing original vs reconstructed, we treat the 
    'noise' as the reconstruction error.
    
    Formula used:
      SNR_degradation = 10 * log10(P_signal / P_error)
      
    This represents how much signal power is lost to error (noise introduced by compression).
    
    Args:
        original: Original strain time series (numpy array).
        reconstructed: Reconstructed strain time series after decompression.
        fs: Sampling frequency in Hz (default 4096.0 for GW data).
        
    Returns:
        SNR degradation in dB (float), precision ≥ 0.1 dB.
        
    Raises:
        ValueError: If input arrays have different shapes, are empty, or error power is zero.
    """
    if original.shape != reconstructed.shape:
        raise ValueError(
            f"Shape mismatch: original {original.shape} vs reconstructed {reconstructed.shape}"
        )
    
    if original.size == 0:
        raise ValueError("Input arrays cannot be empty.")
    
    # Calculate error (noise introduced by compression)
    error = original - reconstructed
    
    # Calculate signal power (mean squared of original)
    signal_power = np.mean(original ** 2)
    
    # Calculate noise power (mean squared of error)
    noise_power = np.mean(error ** 2)
    
    # Avoid division by zero
    if noise_power == 0:
        # Perfect reconstruction
        logger.warning("Noise power is zero. Returning infinite SNR degradation.")
        return float('inf')
    
    if signal_power == 0:
        raise ValueError("Signal power is zero. Cannot compute SNR.")
    
    # Compute SNR in dB
    snr_db = 10.0 * np.log10(signal_power / noise_power)
    
    # Round to 0.1 dB precision as required
    snr_db_rounded = round(snr_db, 1)
    
    logger.info(f"SNR degradation computed: {snr_db_rounded} dB")
    
    return snr_db_rounded


def compute_compression_metrics(
    original: np.ndarray,
    reconstructed: np.ndarray,
    fs: float = 4096.0
) -> dict:
    """
    Compute all compression metrics for a pair of signals.
    
    Args:
        original: Original strain time series.
        reconstructed: Reconstructed strain time series.
        fs: Sampling frequency in Hz.
        
    Returns:
        Dictionary containing:
            - 'mse': Mean Squared Error (float)
            - 'snr_degradation_db': SNR degradation in dB (float, 0.1 dB precision)
            - 'signal_power': Power of original signal (float)
            - 'noise_power': Power of error signal (float)
    """
    mse = compute_mse(original, reconstructed)
    snr_deg = compute_snr_degradation(original, reconstructed, fs)
    
    error = original - reconstructed
    signal_power = float(np.mean(original ** 2))
    noise_power = float(np.mean(error ** 2))
    
    return {
        'mse': mse,
        'snr_degradation_db': snr_deg,
        'signal_power': signal_power,
        'noise_power': noise_power
    }


def main():
    """
    Example usage for testing metrics computation.
    This function is intended for manual testing or as a demonstration.
    """
    # Generate sample data for testing
    t = np.linspace(0, 1, 4096)
    original = np.sin(2 * np.pi * 50 * t) + 0.1 * np.random.randn(len(t))
    
    # Simulate a compressed/reconstructed signal with some noise
    reconstructed = original + 0.01 * np.random.randn(len(t))
    
    metrics = compute_compression_metrics(original, reconstructed)
    
    print("Compression Metrics:")
    print(f"  MSE: {metrics['mse']:.2e}")
    print(f"  SNR Degradation: {metrics['snr_degradation_db']} dB")
    print(f"  Signal Power: {metrics['signal_power']:.6f}")
    print(f"  Noise Power: {metrics['noise_power']:.6f}")

if __name__ == "__main__":
    main()