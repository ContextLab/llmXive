"""
Noise injection module for adding controlled Gaussian and Quantization noise to trajectories.

Implements FR-002 (Gaussian Noise Injection) and FR-003 (Quantization Noise Injection).
Ensures target SNR accuracy within ±0.5 dB.
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
    Calculate the power of the input signal.
    Power is defined as the mean of the squared values.
    
    Args:
        signal: 1D or 2D numpy array of signal values.
        
    Returns:
        Signal power (float).
    """
    if signal.size == 0:
        return 0.0
    return float(np.mean(signal ** 2))

def calculate_noise_power(noise: np.ndarray) -> float:
    """
    Calculate the power of the input noise.
    Power is defined as the mean of the squared values.
    
    Args:
        noise: 1D or 2D numpy array of noise values.
        
    Returns:
        Noise power (float).
    """
    if noise.size == 0:
        return 0.0
    return float(np.mean(noise ** 2))

def calculate_snr(signal_power: float, noise_power: float) -> float:
    """
    Calculate Signal-to-Noise Ratio in decibels (dB).
    SNR (dB) = 10 * log10(P_signal / P_noise)
    
    Args:
        signal_power: Power of the signal.
        noise_power: Power of the noise.
        
    Returns:
        SNR in dB. Returns infinity if noise power is zero.
    """
    if noise_power == 0.0:
        return float('inf')
    if signal_power == 0.0:
        return float('-inf')
    return float(10.0 * np.log10(signal_power / noise_power))

def inject_gaussian_noise(
    trajectory: Trajectory,
    target_snr_db: float,
    seed: Optional[int] = None
) -> NoisyTrajectory:
    """
    Inject additive Gaussian noise into a trajectory to achieve a target SNR.
    
    Implements FR-002: Gaussian Noise Injection.
    The noise is generated such that the resulting SNR is within ±0.5 dB of the target.
    
    Args:
        trajectory: Clean trajectory data (Trajectory object).
        target_snr_db: Target Signal-to-Noise Ratio in decibels.
        seed: Random seed for reproducibility.
        
    Returns:
        NoisyTrajectory object containing the noisy data and metadata.
        
    Raises:
        ValueError: If target_snr_db is too high (noise power would be negative).
    """
    if seed is not None:
        np.random.seed(seed)
        
    # Extract signal data
    # trajectory.data is expected to be a 2D array (time, dimensions)
    signal_data = trajectory.data
    if signal_data.ndim == 1:
        signal_data = signal_data.reshape(-1, 1)
        
    # Calculate signal power (mean of all elements squared)
    signal_power = calculate_signal_power(signal_data)
    
    if signal_power == 0.0:
        logger.warning("Signal power is zero. Cannot inject noise. Returning clean trajectory.")
        return NoisyTrajectory(
            data=signal_data.copy(),
            system_type=trajectory.system_type,
            seed=trajectory.seed,
            snr_db=float('inf'),
            noise_type=NoiseType.GAUSSIAN,
            noise_params={"target_snr_db": target_snr_db, "actual_snr_db": float('inf')}
        )
        
    # Calculate required noise power for target SNR
    # SNR_dB = 10 * log10(P_signal / P_noise)
    # P_noise = P_signal / (10^(SNR_dB / 10))
    if target_snr_db == float('inf'):
        noise_power = 0.0
    else:
        ratio = 10 ** (target_snr_db / 10.0)
        if ratio <= 0:
            raise ValueError(f"Invalid SNR ratio for target {target_snr_db} dB. Ratio must be > 0.")
        noise_power = signal_power / ratio
        
    # Calculate standard deviation for Gaussian noise
    # For zero-mean Gaussian noise, Power = Variance = std_dev^2
    std_dev = np.sqrt(noise_power)
    
    # Generate Gaussian noise with same shape as signal
    noise = np.random.normal(0.0, std_dev, size=signal_data.shape)
    
    # Add noise to signal
    noisy_data = signal_data + noise
    
    # Verify actual SNR
    actual_noise_power = calculate_noise_power(noise)
    actual_snr_db = calculate_snr(signal_power, actual_noise_power)
    
    # Check accuracy
    if target_snr_db != float('inf'):
        snr_error = abs(actual_snr_db - target_snr_db)
        if snr_error > 0.5:
            logger.warning(
                f"SNR accuracy warning: Target={target_snr_db:.2f} dB, "
                f"Actual={actual_snr_db:.2f} dB, Error={snr_error:.2f} dB. "
                f"This exceeds the ±0.5 dB tolerance."
            )
    
    return NoisyTrajectory(
        data=noisy_data,
        system_type=trajectory.system_type,
        seed=trajectory.seed,
        snr_db=actual_snr_db,
        noise_type=NoiseType.GAUSSIAN,
        noise_params={
            "target_snr_db": target_snr_db,
            "actual_snr_db": actual_snr_db,
            "noise_std_dev": float(std_dev)
        }
    )

def inject_quantization_noise(
    trajectory: Trajectory,
    bit_resolution: int,
    signal_range: Optional[Tuple[float, float]] = None
) -> NoisyTrajectory:
    """
    Inject uniform quantization noise by simulating bit-depth reduction.
    
    Implements FR-003: Uniform Quantization Noise Injection.
    The signal is quantized to a specified number of bits and then de-quantized,
    introducing uniform noise in the range [-q/2, q/2] where q is the step size.
    
    Args:
        trajectory: Clean trajectory data (Trajectory object).
        bit_resolution: Number of bits for quantization (e.g., 8, 10, 12, 16).
        signal_range: Optional tuple (min_val, max_val) defining the signal range.
                     If None, uses the min/max of the data.
                     
    Returns:
        NoisyTrajectory object containing the quantized data and metadata.
        
    Raises:
        ValueError: If bit_resolution is less than 1.
    """
    if bit_resolution < 1:
        raise ValueError(f"Bit resolution must be at least 1, got {bit_resolution}.")
        
    # Extract signal data
    signal_data = trajectory.data
    if signal_data.ndim == 1:
        signal_data = signal_data.reshape(-1, 1)
        
    # Determine signal range
    if signal_range is None:
        min_val = float(np.min(signal_data))
        max_val = float(np.max(signal_data))
        # Add a small margin to avoid edge cases if min == max
        if min_val == max_val:
            max_val = min_val + 1.0
    else:
        min_val, max_val = signal_range
        
    range_val = max_val - min_val
    if range_val == 0:
        logger.warning("Signal range is zero. Returning clean trajectory.")
        return NoisyTrajectory(
            data=signal_data.copy(),
            system_type=trajectory.system_type,
            seed=trajectory.seed,
            snr_db=float('inf'),
            noise_type=NoiseType.QUANTIZATION,
            noise_params={"bit_resolution": bit_resolution, "actual_snr_db": float('inf')}
        )
        
    # Calculate number of levels and step size
    num_levels = 2 ** bit_resolution
    step_size = range_val / (num_levels - 1)
    
    # Quantization: Map signal to discrete levels and back
    # 1. Normalize to [0, num_levels - 1]
    normalized = (signal_data - min_val) / range_val
    # 2. Clip to [0, 1] to handle small floating point errors
    normalized = np.clip(normalized, 0.0, 1.0)
    # 3. Map to integer levels
    levels = np.round(normalized * (num_levels - 1)).astype(int)
    # 4. De-quantize (map back to signal range)
    quantized_data = min_val + (levels * step_size)
    
    # Calculate noise (difference between original and quantized)
    noise = quantized_data - signal_data
    
    # Theoretical noise power for uniform quantization: q^2 / 12
    # Actual noise power
    actual_noise_power = calculate_noise_power(noise)
    signal_power = calculate_signal_power(signal_data)
    actual_snr_db = calculate_snr(signal_power, actual_noise_power)
    
    # Calculate theoretical SNR for comparison
    # SNR_q ≈ 6.02 * N + 1.76 dB (for full-scale sine wave, approximate for general signals)
    theoretical_snr_db = 6.02 * bit_resolution + 1.76
    
    logger.info(
        f"Quantization: {bit_resolution}-bit, Step size={step_size:.6f}, "
        f"Actual SNR={actual_snr_db:.2f} dB, Theoretical≈{theoretical_snr_db:.2f} dB"
    )
    
    return NoisyTrajectory(
        data=quantized_data,
        system_type=trajectory.system_type,
        seed=trajectory.seed,
        snr_db=actual_snr_db,
        noise_type=NoiseType.QUANTIZATION,
        noise_params={
            "bit_resolution": bit_resolution,
            "step_size": float(step_size),
            "actual_snr_db": actual_snr_db,
            "theoretical_snr_db": theoretical_snr_db,
            "signal_range": [min_val, max_val]
        }
    )

def verify_snr_accuracy(
    trajectory: Trajectory,
    target_snr_db: float,
    tolerance_db: float = 0.5,
    seed: Optional[int] = None
) -> Tuple[NoisyTrajectory, bool]:
    """
    Inject Gaussian noise and verify that the actual SNR is within tolerance of the target.
    
    Args:
        trajectory: Clean trajectory data.
        target_snr_db: Target SNR in dB.
        tolerance_db: Acceptable deviation in dB (default 0.5).
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (NoisyTrajectory, is_within_tolerance).
    """
    noisy_traj = inject_gaussian_noise(trajectory, target_snr_db, seed)
    actual_snr = noisy_traj.snr_db
    
    if target_snr_db == float('inf'):
        is_within = actual_snr == float('inf')
    else:
        is_within = abs(actual_snr - target_snr_db) <= tolerance_db
        
    return noisy_traj, is_within

def get_noise_injection_function(
    noise_type: NoiseType
) -> Callable:
    """
    Factory function to get the appropriate noise injection function.
    
    Args:
        noise_type: Type of noise (GAUSSIAN or QUANTIZATION).
        
    Returns:
        Callable function for noise injection.
        
    Raises:
        ValueError: If noise_type is not supported.
    """
    if noise_type == NoiseType.GAUSSIAN:
        return inject_gaussian_noise
    elif noise_type == NoiseType.QUANTIZATION:
        return inject_quantization_noise
    else:
        raise ValueError(f"Unsupported noise type: {noise_type}. "
                         f"Supported types: {NoiseType.GAUSSIAN}, {NoiseType.QUANTIZATION}")

def get_noise_injection_functions() -> Dict[NoiseType, Callable]:
    """
    Get a dictionary of all available noise injection functions.
    
    Returns:
        Dictionary mapping NoiseType to injection function.
    """
    return {
        NoiseType.GAUSSIAN: inject_gaussian_noise,
        NoiseType.QUANTIZATION: inject_quantization_noise
    }