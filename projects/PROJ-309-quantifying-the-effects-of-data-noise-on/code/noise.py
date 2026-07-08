"""
Noise injection module for adding controlled noise to trajectories.

Supports:
- Gaussian noise injection at target SNR levels (FR-002)
- Uniform quantization noise injection (FR-003)
- SNR verification and accuracy checking
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any, List, Callable
from scipy.stats import norm
import logging
from config import NoiseType, get_snr_levels
from utils.data_models import Trajectory, NoisyTrajectory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_signal_power(signal: np.ndarray) -> float:
    """
    Calculate the power of a signal (mean squared value).

    Args:
        signal: Input signal array (can be multi-dimensional).

    Returns:
        float: Mean squared value of the flattened signal.
    """
    # Flatten if multi-dimensional
    flat_signal = signal.flatten()
    return float(np.mean(flat_signal ** 2))

def calculate_noise_power(noise: np.ndarray) -> float:
    """
    Calculate the power of noise (mean squared value).

    Args:
        noise: Input noise array (can be multi-dimensional).

    Returns:
        float: Mean squared value of the flattened noise.
    """
    flat_noise = noise.flatten()
    return float(np.mean(flat_noise ** 2))

def calculate_snr(clean_data: np.ndarray, noisy_data: np.ndarray) -> float:
    """
    Calculate Signal-to-Noise Ratio in dB.

    SNR(dB) = 10 * log10(P_signal / P_noise)
    where P_signal is the power of the clean signal
    and P_noise is the power of the noise (difference between clean and noisy).

    Args:
        clean_data: Original clean trajectory data.
        noisy_data: Noisy trajectory data.

    Returns:
        float: SNR in decibels. Returns infinity if noise power is zero.
    """
    noise = noisy_data - clean_data
    signal_power = calculate_signal_power(clean_data)
    noise_power = calculate_noise_power(noise)

    if noise_power == 0:
        return float('inf')

    snr_linear = signal_power / noise_power
    snr_db = 10 * np.log10(snr_linear)
    return float(snr_db)

def verify_snr_accuracy(clean_data: np.ndarray, noisy_data: np.ndarray, target_snr_db: float, tolerance: float = 0.5) -> Tuple[bool, float]:
    """
    Verify that the actual SNR matches the target within tolerance.

    Args:
        clean_data: Original clean trajectory data.
        noisy_data: Noisy trajectory data.
        target_snr_db: Target SNR in dB.
        tolerance: Acceptable error in dB (default ±0.5dB).

    Returns:
        Tuple of (is_valid, actual_snr_db) where is_valid is True if the
        actual SNR is within the tolerance of the target.
    """
    actual_snr = calculate_snr(clean_data, noisy_data)
    error = abs(actual_snr - target_snr_db)
    return error <= tolerance, actual_snr

def inject_gaussian_noise(clean_data: np.ndarray, target_snr_db: float) -> np.ndarray:
    """
    Inject additive Gaussian noise to achieve target SNR (FR-002).

    The noise is scaled such that:
    SNR = 10 * log10(P_signal / P_noise) = target_snr_db

    Args:
        clean_data: Clean trajectory data (n_points, n_dimensions).
        target_snr_db: Target SNR in dB.

    Returns:
        np.ndarray: Noisy trajectory data with injected Gaussian noise.
    """
    # Calculate signal power
    signal_power = calculate_signal_power(clean_data)

    # Calculate required noise power
    # target_snr_linear = 10 ^ (target_snr_db / 10)
    # noise_power = signal_power / target_snr_linear
    target_snr_linear = 10 ** (target_snr_db / 10.0)
    if target_snr_linear == 0:
        noise_power = signal_power
    else:
        noise_power = signal_power / target_snr_linear

    # Calculate standard deviation for Gaussian noise
    # For zero-mean Gaussian noise, variance = noise_power
    std_dev = np.sqrt(noise_power)

    # Generate Gaussian noise
    noise = np.random.normal(0, std_dev, clean_data.shape)

    # Add noise to signal
    noisy_data = clean_data + noise

    # Verify SNR accuracy
    is_valid, actual_snr = verify_snr_accuracy(clean_data, noisy_data, target_snr_db)
    if not is_valid:
        logger.warning(f"Gaussian noise injection SNR mismatch: target={target_snr_db}dB, actual={actual_snr:.2f}dB")

    return noisy_data

def inject_quantization_noise(clean_data: np.ndarray, bits: int = 8) -> np.ndarray:
    """
    Inject uniform quantization noise (FR-003).

    Simulates the effect of quantizing the signal to a fixed number of bits.
    The quantization noise is uniformly distributed in [-q/2, q/2] where q is the step size.

    Args:
        clean_data: Clean trajectory data.
        bits: Number of bits for quantization (default 8).

    Returns:
        np.ndarray: Noisy trajectory data with quantization noise.
    """
    # Calculate range of the data
    data_min = np.min(clean_data)
    data_max = np.max(clean_data)
    data_range = data_max - data_min

    if data_range == 0:
        # All values are the same, no quantization needed
        logger.warning("Data range is zero; returning copy of clean data without quantization noise.")
        return clean_data.copy()

    # Calculate quantization step size
    n_levels = 2 ** bits
    step_size = data_range / (n_levels - 1)

    # Quantize the data
    quantized_data = np.round((clean_data - data_min) / step_size) * step_size + data_min

    # Calculate quantization noise (uniform distribution)
    # The noise is the difference between original and quantized values
    quantization_noise = clean_data - quantized_data

    # Add noise back to simulate the effect
    # This creates a noisy signal that represents the quantized version
    # The noise is uniformly distributed in [-step_size/2, step_size/2]
    noisy_data = quantized_data + np.random.uniform(-step_size/2, step_size/2, clean_data.shape)

    return noisy_data

def get_noise_injection_function(noise_type: NoiseType) -> Callable:
    """
    Get the appropriate noise injection function for a given noise type.

    Args:
        noise_type: The type of noise to inject (Gaussian or Quantization).

    Returns:
        Callable: The corresponding injection function.

    Raises:
        ValueError: If the noise type is not supported.
    """
    if noise_type == NoiseType.GAUSSIAN:
        return inject_gaussian_noise
    elif noise_type == NoiseType.QUANTIZATION:
        return inject_quantization_noise
    else:
        raise ValueError(f"Unsupported noise type: {noise_type}")

def get_noise_injection_functions() -> Dict[NoiseType, Callable]:
    """
    Get all available noise injection functions.

    Returns:
        Dict[NoiseType, Callable]: Mapping of noise types to their injection functions.
    """
    return {
        NoiseType.GAUSSIAN: inject_gaussian_noise,
        NoiseType.QUANTIZATION: inject_quantization_noise
    }