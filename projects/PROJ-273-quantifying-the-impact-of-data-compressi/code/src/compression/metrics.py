import numpy as np
from typing import Tuple, Optional, Dict, Any
import logging
from src.utils.logging import get_logger
from src.utils.config import get_project_root, ensure_dir
import json
from pathlib import Path

logger = get_logger(__name__)

def compute_mse(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """
    Compute Mean Squared Error between original and reconstructed waveforms.
    
    Args:
        original: Original waveform data (numpy array)
        reconstructed: Reconstructed waveform data (numpy array)
        
    Returns:
        MSE value as float
        
    Raises:
        ValueError: If arrays have different shapes or are empty
    """
    original = np.asarray(original, dtype=np.float64)
    reconstructed = np.asarray(reconstructed, dtype=np.float64)
    
    if original.shape != reconstructed.shape:
        raise ValueError(f"Shape mismatch: {original.shape} vs {reconstructed.shape}")
    
    if original.size == 0:
        raise ValueError("Input arrays cannot be empty")
        
    mse = np.mean((original - reconstructed) ** 2)
    return float(mse)

def compute_snr_degradation(
    original: np.ndarray, 
    reconstructed: np.ndarray, 
    sample_rate: float = 4096.0
) -> float:
    """
    Compute SNR degradation in dB between original and reconstructed waveforms.
    
    SNR degradation is calculated as:
    SNR_degradation (dB) = 10 * log10( Signal_Power / Error_Power )
    
    Where:
    - Signal_Power is the power of the original signal (approximated as total power)
    - Error_Power is the power of the reconstruction error
    
    Args:
        original: Original waveform data (numpy array)
        reconstructed: Reconstructed waveform data (numpy array)
        sample_rate: Sample rate in Hz (default 4096.0 for GW data)
        
    Returns:
        SNR degradation in dB (positive value indicates degradation)
        
    Raises:
        ValueError: If arrays have different shapes, are empty, or error power is zero
    """
    original = np.asarray(original, dtype=np.float64)
    reconstructed = np.asarray(reconstructed, dtype=np.float64)
    
    if original.shape != reconstructed.shape:
        raise ValueError(f"Shape mismatch: {original.shape} vs {reconstructed.shape}")
        
    if original.size == 0:
        raise ValueError("Input arrays cannot be empty")
    
    # Calculate signal power (using original as reference)
    signal_power = np.mean(original ** 2)
    
    # Calculate error power
    error = original - reconstructed
    error_power = np.mean(error ** 2)
    
    # Avoid division by zero
    if error_power < 1e-20:
        # Essentially perfect reconstruction
        return 0.0
    
    if signal_power < 1e-20:
        # Signal is essentially zero
        return float('inf')
    
    # SNR degradation in dB
    # Higher value means more degradation (worse quality)
    snr_degradation = 10.0 * np.log10(signal_power / error_power)
    
    return float(snr_degradation)

def compute_compression_metrics(
    original: np.ndarray, 
    reconstructed: np.ndarray, 
    sample_rate: float = 4096.0
) -> Dict[str, float]:
    """
    Compute a comprehensive set of compression metrics.
    
    Args:
        original: Original waveform data (numpy array)
        reconstructed: Reconstructed waveform data (numpy array)
        sample_rate: Sample rate in Hz (default 4096.0)
        
    Returns:
        Dictionary containing:
        - 'mse': Mean Squared Error
        - 'snr_degradation_db': SNR degradation in dB
        - 'rmse': Root Mean Squared Error
        - 'max_abs_error': Maximum absolute error
    """
    mse = compute_mse(original, reconstructed)
    snr_deg = compute_snr_degradation(original, reconstructed, sample_rate)
    rmse = np.sqrt(mse)
    max_abs_error = float(np.max(np.abs(original - reconstructed)))
    
    return {
        'mse': mse,
        'snr_degradation_db': round(snr_deg, 1),  # Precision >= 0.1 dB
        'rmse': rmse,
        'max_abs_error': max_abs_error
    }

def main():
    """
    Main entry point for testing metrics computation.
    This function demonstrates the metrics computation on sample data
    and writes results to a JSON file.
    """
    project_root = get_project_root()
    output_dir = ensure_dir(project_root / "data" / "processed" / "compression_metrics")
    
    # Generate sample waveform data (realistic GW-like signal + noise)
    np.random.seed(42)
    duration = 1.0  # seconds
    sample_rate = 4096.0
    t = np.linspace(0, duration, int(duration * sample_rate))
    
    # Simulate a chirp-like signal
    f0 = 30.0
    f1 = 200.0
    chirp = (t ** 2) * np.sin(2 * np.pi * f0 * t + (np.pi * (f1 - f0) * t**2) / duration)
    noise = np.random.normal(0, 0.01, size=t.shape)
    original_signal = chirp + noise
    
    # Simulate a compressed/reconstructed signal with some degradation
    # Add quantization noise and slight phase shift
    quantization_noise = np.random.normal(0, 0.001, size=t.shape)
    phase_shift = 0.01 * np.sin(2 * np.pi * 50 * t)
    reconstructed_signal = original_signal + quantization_noise + phase_shift
    
    # Compute metrics
    metrics = compute_compression_metrics(original_signal, reconstructed_signal, sample_rate)
    
    # Log results
    logger.info("Compression Metrics Computation:")
    logger.info(f"  MSE: {metrics['mse']:.2e}")
    logger.info(f"  SNR Degradation: {metrics['snr_degradation_db']:.1f} dB")
    logger.info(f"  RMSE: {metrics['rmse']:.2e}")
    logger.info(f"  Max Abs Error: {metrics['max_abs_error']:.2e}")
    
    # Save results to file
    output_path = output_dir / "sample_metrics.json"
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics saved to {output_path}")
    
    # Return metrics for potential programmatic use
    return metrics

if __name__ == "__main__":
    main()
