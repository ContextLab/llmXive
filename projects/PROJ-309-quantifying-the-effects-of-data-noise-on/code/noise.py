import numpy as np
from typing import Tuple, Dict, Any, Optional, Union
import logging
from enum import Enum
from code.config import NoiseType
from code.utils.data_models import Trajectory, NoisyTrajectory

logger = logging.getLogger(__name__)

def calculate_signal_power(signal: np.ndarray) -> float:
    """
    Calculate the power of the signal.
    
    Args:
        signal: 1D or 2D numpy array representing the signal.
        
    Returns:
        float: Signal power (mean squared value).
    """
    if signal.ndim == 1:
        return float(np.mean(signal ** 2))
    elif signal.ndim == 2:
        # Mean power across all dimensions and time steps
        return float(np.mean(signal ** 2))
    else:
        raise ValueError(f"Signal must be 1D or 2D, got {signal.ndim}D")

def calculate_noise_power(noise: np.ndarray) -> float:
    """
    Calculate the power of the noise.
    
    Args:
        noise: 1D or 2D numpy array representing the noise.
        
    Returns:
        float: Noise power (mean squared value).
    """
    if noise.ndim == 1:
        return float(np.mean(noise ** 2))
    elif noise.ndim == 2:
        return float(np.mean(noise ** 2))
    else:
        raise ValueError(f"Noise must be 1D or 2D, got {noise.ndim}D")

def calculate_snr(signal_power: float, noise_power: float) -> float:
    """
    Calculate Signal-to-Noise Ratio in dB.
    
    Args:
        signal_power: Power of the signal.
        noise_power: Power of the noise.
        
    Returns:
        float: SNR in decibels.
    """
    if noise_power <= 0:
        return float('inf')
    return 10.0 * np.log10(signal_power / noise_power)

def inject_gaussian_noise(
    trajectory: Trajectory,
    snr_db: float,
    seed: Optional[int] = None
) -> NoisyTrajectory:
    """
    Inject additive Gaussian noise to achieve a target SNR.
    
    Args:
        trajectory: Clean trajectory data.
        snr_db: Target Signal-to-Noise Ratio in decibels.
        seed: Random seed for reproducibility.
        
    Returns:
        NoisyTrajectory: Trajectory with injected Gaussian noise.
    """
    if seed is not None:
        np.random.seed(seed)
    
    signal = trajectory.data
    signal_power = calculate_signal_power(signal)
    
    # Calculate required noise power for target SNR
    if snr_db == float('inf'):
        noise_power = 0.0
    else:
        noise_power = signal_power / (10 ** (snr_db / 10.0))
    
    # Generate Gaussian noise with calculated variance
    noise_std = np.sqrt(noise_power)
    noise = np.random.normal(0, noise_std, signal.shape)
    
    noisy_data = signal + noise
    
    return NoisyTrajectory(
        data=noisy_data,
        noise_type=NoiseType.GAUSSIAN,
        snr_db=snr_db,
        actual_snr_db=calculate_snr(signal_power, calculate_noise_power(noise)),
        seed=seed,
        original_trajectory_id=trajectory.id
    )

def inject_quantization_noise(
    trajectory: Trajectory,
    bits: int,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None
) -> NoisyTrajectory:
    """
    Inject uniform quantization noise simulating limited bit resolution.
    
    Args:
        trajectory: Clean trajectory data.
        bits: Number of bits for quantization.
        min_val: Minimum value for quantization range (default: min of data).
        max_val: Maximum value for quantization range (default: max of data).
        
    Returns:
        NoisyTrajectory: Trajectory with injected quantization noise.
    """
    signal = trajectory.data
    
    if min_val is None:
        min_val = float(np.min(signal))
    if max_val is None:
        max_val = float(np.max(signal))
    
    # Quantization step size
    num_levels = 2 ** bits
    step_size = (max_val - min_val) / num_levels
    
    # Quantize the signal
    # Round to nearest level, then convert back
    quantized = np.round((signal - min_val) / step_size) * step_size + min_val
    
    # Calculate noise as the difference
    noise = signal - quantized
    
    # Calculate actual SNR
    signal_power = calculate_signal_power(signal)
    noise_power = calculate_noise_power(noise)
    actual_snr = calculate_snr(signal_power, noise_power)
    
    noisy_data = quantized
    
    return NoisyTrajectory(
        data=noisy_data,
        noise_type=NoiseType.QUANTIZATION,
        snr_db=actual_snr,
        actual_snr_db=actual_snr,
        bits=bits,
        quantization_range=(min_val, max_val),
        original_trajectory_id=trajectory.id
    )

def add_noise_to_trajectory(
    trajectory: Trajectory,
    noise_type: NoiseType,
    snr_db: Optional[float] = None,
    bits: Optional[int] = None,
    seed: Optional[int] = None
) -> NoisyTrajectory:
    """
    Add noise to a trajectory based on the specified noise type.
    
    Args:
        trajectory: Clean trajectory data.
        noise_type: Type of noise to add (Gaussian or Quantization).
        snr_db: Target SNR for Gaussian noise (required for Gaussian).
        bits: Bit resolution for quantization noise (required for Quantization).
        seed: Random seed for reproducibility.
        
    Returns:
        NoisyTrajectory: Trajectory with injected noise.
        
    Raises:
        ValueError: If noise_type is unsupported or required parameters are missing.
    """
    logger.debug(f"Adding {noise_type} noise to trajectory {trajectory.id}")
    
    if noise_type == NoiseType.GAUSSIAN:
        if snr_db is None:
            raise ValueError("snr_db is required for Gaussian noise injection")
        return inject_gaussian_noise(trajectory, snr_db, seed)
        
    elif noise_type == NoiseType.QUANTIZATION:
        if bits is None:
            raise ValueError("bits is required for quantization noise injection")
        return inject_quantization_noise(trajectory, bits)
        
    else:
        raise ValueError(
            f"Unsupported noise type: {noise_type}. "
            f"Supported types are: {NoiseType.GAUSSIAN}, {NoiseType.QUANTIZATION}"
        )

def verify_snr_accuracy(
    trajectory: NoisyTrajectory,
    target_snr_db: float,
    tolerance_db: float = 0.5
) -> Tuple[bool, float]:
    """
    Verify that the actual SNR matches the target within a tolerance.
    
    Args:
        trajectory: Noisy trajectory with SNR information.
        target_snr_db: Target SNR value.
        tolerance_db: Acceptable deviation in dB.
        
    Returns:
        Tuple[bool, float]: (is_within_tolerance, actual_snr)
    """
    actual_snr = trajectory.actual_snr_db
    diff = abs(actual_snr - target_snr_db)
    is_within = diff <= tolerance_db
    
    logger.info(
        f"SNR verification: Target={target_snr_db}dB, Actual={actual_snr:.2f}dB, "
        f"Diff={diff:.2f}dB, Pass={is_within}"
    )
    
    return is_within, actual_snr