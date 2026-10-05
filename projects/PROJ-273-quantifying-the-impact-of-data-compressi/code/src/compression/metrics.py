"""
Metrics computation for compression quality assessment.

Implements T021: compute MSE, SNR degradation, and comprehensive compression metrics.
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any
import logging
from src.utils.logging import get_logger
from src.utils.config import get_project_root, ensure_dir
import json

logger = get_logger(__name__)

def compute_mse(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """
    Compute Mean Squared Error between original and reconstructed signals.
    
    Args:
        original: Original signal array
        reconstructed: Reconstructed signal array
        
    Returns:
        MSE value
    """
    if original.shape != reconstructed.shape:
        raise ValueError(f"Shape mismatch: {original.shape} vs {reconstructed.shape}")
    
    mse = np.mean((original - reconstructed) ** 2)
    return float(mse)

def compute_snr_degradation(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """
    Compute SNR degradation in dB.
    
    SNR degradation = 10 * log10(P_signal / P_noise)
    where P_signal is power of original, P_noise is power of error.
    
    Args:
        original: Original signal array
        reconstructed: Reconstructed signal array
        
    Returns:
        SNR degradation in dB (positive value indicates degradation)
    """
    if original.shape != reconstructed.shape:
        raise ValueError(f"Shape mismatch: {original.shape} vs {reconstructed.shape}")
    
    signal_power = np.mean(original ** 2)
    noise = original - reconstructed
    noise_power = np.mean(noise ** 2)
    
    if noise_power == 0:
        return 0.0  # Perfect reconstruction
    
    if signal_power == 0:
        return float('inf')  # Undefined
    
    snr_db = 10 * np.log10(signal_power / noise_power)
    return float(snr_db)

def compute_compression_metrics(original: np.ndarray, reconstructed: np.ndarray) -> Dict[str, Any]:
    """
    Compute comprehensive compression metrics.
    
    Args:
        original: Original signal array
        reconstructed: Reconstructed signal array
        
    Returns:
        Dictionary containing MSE, SNR degradation, and other metrics
    """
    mse = compute_mse(original, reconstructed)
    snr_degradation = compute_snr_degradation(original, reconstructed)
    
    # Additional metrics
    max_error = float(np.max(np.abs(original - reconstructed)))
    rmse = float(np.sqrt(mse))
    
    # Compression ratio (approximate, based on typical compression behavior)
    # This is a placeholder; actual compression ratio depends on the method
    compression_ratio = 1.0  # Will be updated by specific compression methods
    
    return {
        "mse": mse,
        "snr_degradation_db": snr_degradation,
        "rmse": rmse,
        "max_error": max_error,
        "compression_ratio": compression_ratio,
        "status": "unacceptable" if snr_degradation > 5.0 else "acceptable"
    }

def main():
    """Test the metrics computation functions."""
    logger.info("Testing metrics computation...")
    
    # Create test signals
    original = np.sin(np.linspace(0, 10 * np.pi, 1000))
    reconstructed = original + 0.01 * np.random.randn(1000)
    
    mse = compute_mse(original, reconstructed)
    snr = compute_snr_degradation(original, reconstructed)
    metrics = compute_compression_metrics(original, reconstructed)
    
    logger.info(f"MSE: {mse:.6f}")
    logger.info(f"SNR degradation: {snr:.2f} dB")
    logger.info(f"Metrics: {metrics}")
    
    logger.info("Metrics computation tests completed.")

if __name__ == "__main__":
    main()
