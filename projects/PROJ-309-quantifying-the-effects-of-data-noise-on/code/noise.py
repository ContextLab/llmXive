"""
Noise injection module for dynamical systems research.

Implements Gaussian and uniform quantization noise injection for trajectory data.
Provides functions to calculate signal/noise power and verify SNR accuracy.

FR-002: Gaussian noise injection with target SNR
FR-003: Uniform quantization noise injection with bit resolution
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any, List, Callable
from scipy.stats import norm
import logging

from config import NoiseType, get_snr_levels
from utils.data_models import Trajectory, NoisyTrajectory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_signal_power(signal: np.ndarray) -> float:
    """
    Calculate the power of a signal.

    Signal power is defined as the mean of the squared values.

    Args:
        signal: 1D or 2D numpy array of signal values. If 2D, power is calculated
               for each column and then averaged.

    Returns:
        float: The average power of the signal.
    """
    if signal.ndim == 1:
        return float(np.mean(signal ** 2))
    else:
        # For multi-dimensional signals, calculate power per dimension and average
        return float(np.mean(np.mean(signal ** 2, axis=0)))


def calculate_noise_power(noise: np.ndarray) -> float:
    """
    Calculate the power of noise.

    Noise power is defined as the mean of the squared values.

    Args:
        noise: 1D or 2D numpy array of noise values.

    Returns:
        float: The average power of the noise.
    """
    if noise.ndim == 1:
        return float(np.mean(noise ** 2))
    else:
        return float(np.mean(np.mean(noise ** 2, axis=0)))


def calculate_snr(signal_power: float, noise_power: float) -> float:
    """
    Calculate Signal-to-Noise Ratio (SNR) in decibels.

    SNR_dB = 10 * log10(P_signal / P_noise)

    Args:
        signal_power: Power of the signal.
        noise_power: Power of the noise.

    Returns:
        float: SNR in decibels. Returns inf if noise_power is 0.
    """
    if noise_power == 0:
        return float('inf')
    return float(10 * np.log10(signal_power / noise_power))


def inject_gaussian_noise(
    trajectory: Trajectory,
    target_snr_db: float,
    seed: Optional[int] = None
) -> NoisyTrajectory:
    """
    Inject additive Gaussian noise into a trajectory to achieve a target SNR.

    Implements FR-002: Gaussian noise injection with target SNR accuracy ±0.5dB.

    The noise is generated such that:
    10 * log10(P_signal / P_noise) = target_snr_db

    Which implies:
    P_noise = P_signal / (10^(target_snr_db / 10))

    For Gaussian noise with zero mean, P_noise = σ², so:
    σ = sqrt(P_noise)

    Args:
        trajectory: Clean trajectory object with `data` (numpy array) and metadata.
        target_snr_db: Target SNR in decibels.
        seed: Random seed for reproducibility. If None, uses system entropy.

    Returns:
        NoisyTrajectory: Object containing the noisy data, original data,
                       noise parameters, and measured SNR.

    Raises:
        ValueError: If target_snr_db is not finite.
    """
    if not np.isfinite(target_snr_db):
        raise ValueError(f"target_snr_db must be finite, got {target_snr_db}")

    # Set random seed for reproducibility
    rng = np.random.default_rng(seed)

    # Extract signal data
    signal_data = trajectory.data.copy()

    # Calculate signal power
    signal_power = calculate_signal_power(signal_data)

    if signal_power == 0:
        logger.warning("Signal power is zero. Cannot inject noise. Returning clean trajectory.")
        return NoisyTrajectory(
            data=signal_data,
            original_data=signal_data,
            noise_type=NoiseType.GAUSSIAN,
            noise_params={'target_snr_db': target_snr_db, 'actual_snr_db': float('inf')},
            measured_snr_db=float('inf')
        )

    # Calculate required noise power
    noise_power = signal_power / (10 ** (target_snr_db / 10))

    # Calculate standard deviation for Gaussian noise
    noise_std = np.sqrt(noise_power)

    # Generate Gaussian noise
    noise = rng.normal(loc=0.0, scale=noise_std, size=signal_data.shape)

    # Inject noise
    noisy_data = signal_data + noise

    # Verify SNR accuracy
    actual_noise_power = calculate_noise_power(noise)
    actual_snr_db = calculate_snr(signal_power, actual_noise_power)

    # Log verification
    snr_error = abs(actual_snr_db - target_snr_db)
    if snr_error > 0.5:
        logger.warning(
            f"SNR verification warning: Target={target_snr_db:.2f}dB, "
            f"Actual={actual_snr_db:.2f}dB, Error={snr_error:.2f}dB"
        )
    else:
        logger.info(
            f"SNR verification passed: Target={target_snr_db:.2f}dB, "
            f"Actual={actual_snr_db:.2f}dB, Error={snr_error:.2f}dB"
        )

    return NoisyTrajectory(
        data=noisy_data,
        original_data=signal_data,
        noise_type=NoiseType.GAUSSIAN,
        noise_params={
            'target_snr_db': target_snr_db,
            'actual_snr_db': actual_snr_db,
            'noise_std': noise_std,
            'seed': seed
        },
        measured_snr_db=actual_snr_db
    )


def inject_quantization_noise(
    trajectory: Trajectory,
    bit_resolution: int,
    seed: Optional[int] = None
) -> NoisyTrajectory:
    """
    Inject uniform quantization noise into a trajectory.

    Implements FR-003: Uniform quantization noise injection with user-specified bit resolution.

    Quantization noise is modeled as uniform noise in the range [-Δ/2, Δ/2]
    where Δ is the quantization step size.

    For a signal with range [min_val, max_val]:
    Δ = (max_val - min_val) / (2^bit_resolution - 1)

    The quantization error is uniformly distributed, so:
    P_noise = Δ² / 12

    Args:
        trajectory: Clean trajectory object with `data` (numpy array) and metadata.
        bit_resolution: Number of bits for quantization (e.g., 8, 10, 12, 16).
        seed: Random seed for reproducibility (used for dithering if needed).

    Returns:
        NoisyTrajectory: Object containing the quantized data, original data,
                       noise parameters, and estimated SNR.
    """
    if not isinstance(bit_resolution, int) or bit_resolution < 1:
        raise ValueError(f"bit_resolution must be a positive integer, got {bit_resolution}")

    rng = np.random.default_rng(seed)

    # Extract signal data
    signal_data = trajectory.data.copy()

    # Calculate signal range
    min_val = np.min(signal_data)
    max_val = np.max(signal_data)
    signal_range = max_val - min_val

    if signal_range == 0:
        logger.warning("Signal range is zero. Returning clean trajectory.")
        return NoisyTrajectory(
            data=signal_data,
            original_data=signal_data,
            noise_type=NoiseType.QUANTIZATION,
            noise_params={'bit_resolution': bit_resolution, 'estimated_snr_db': float('inf')},
            measured_snr_db=float('inf')
        )

    # Calculate quantization step size
    num_levels = 2 ** bit_resolution
    delta = signal_range / (num_levels - 1)

    # Simulate quantization by rounding to nearest level and adding uniform noise
    # This is a more accurate model than simple rounding
    # Add dithering noise before quantization to decorrelate quantization error
    dither = rng.uniform(-delta/2, delta/2, size=signal_data.shape)
    quantized_with_dither = signal_data + dither

    # Quantize to discrete levels
    normalized = (quantized_with_dither - min_val) / delta
    quantized_indices = np.round(normalized).astype(int)
    quantized_indices = np.clip(quantized_indices, 0, num_levels - 1)
    quantized_data = min_val + quantized_indices * delta

    # Calculate the actual quantization noise
    noise = quantized_data - signal_data

    # Calculate powers
    signal_power = calculate_signal_power(signal_data)
    noise_power = calculate_noise_power(noise)

    # Estimate SNR
    estimated_snr_db = calculate_snr(signal_power, noise_power)

    # Theoretical SNR for uniform quantization (approximate)
    # SNR ≈ 6.02 * bit_resolution + 1.76 dB (for full-scale sine wave)
    # For general signals, this is an approximation
    theoretical_snr_db = 6.02 * bit_resolution + 1.76

    logger.info(
        f"Quantization injection: bit_resolution={bit_resolution}, "
        f"delta={delta:.6f}, estimated_snr={estimated_snr_db:.2f}dB, "
        f"theoretical_snr≈{theoretical_snr_db:.2f}dB"
    )

    return NoisyTrajectory(
        data=quantized_data,
        original_data=signal_data,
        noise_type=NoiseType.QUANTIZATION,
        noise_params={
            'bit_resolution': bit_resolution,
            'delta': delta,
            'estimated_snr_db': estimated_snr_db,
            'theoretical_snr_db': theoretical_snr_db
        },
        measured_snr_db=estimated_snr_db
    )


def verify_snr_accuracy(
    trajectory: Trajectory,
    target_snr_db: float,
    tolerance_db: float = 0.5
) -> Tuple[bool, float]:
    """
    Verify that injected noise achieves the target SNR within tolerance.

    This function is used to validate the accuracy of noise injection.

    Args:
        trajectory: Noisy trajectory object (result of inject_gaussian_noise).
        target_snr_db: Target SNR in decibels.
        tolerance_db: Acceptable deviation in dB (default: 0.5dB).

    Returns:
        Tuple[bool, float]: (is_within_tolerance, actual_snr_db)
    """
    actual_snr_db = trajectory.measured_snr_db
    error = abs(actual_snr_db - target_snr_db)
    is_within_tolerance = error <= tolerance_db

    return is_within_tolerance, actual_snr_db


def get_noise_injection_function(noise_type: NoiseType) -> Callable:
    """
    Factory function to get the appropriate noise injection function.

    Args:
        noise_type: Enum value specifying the noise type.

    Returns:
        Callable: The corresponding noise injection function.

    Raises:
        ValueError: If noise_type is not supported.
    """
    if noise_type == NoiseType.GAUSSIAN:
        return inject_gaussian_noise
    elif noise_type == NoiseType.QUANTIZATION:
        return inject_quantization_noise
    else:
        raise ValueError(f"Unsupported noise type: {noise_type}")


def get_noise_injection_functions() -> Dict[str, Callable]:
    """
    Get all available noise injection functions.

    Returns:
        Dict mapping noise type names to injection functions.
    """
    return {
        'gaussian': inject_gaussian_noise,
        'quantization': inject_quantization_noise
    }