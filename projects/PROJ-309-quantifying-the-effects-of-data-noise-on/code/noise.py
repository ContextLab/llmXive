import numpy as np
from typing import Tuple, Optional, Dict, Any, List, Callable
from scipy.stats import norm
import logging
from config import NoiseType, get_snr_levels
from utils.data_models import Trajectory, NoisyTrajectory

logger = logging.getLogger(__name__)

def calculate_signal_power(signal: np.ndarray) -> float:
    """
    Calculate the power of the signal (mean of squared values).
    
    Args:
        signal: 1D or 2D numpy array representing the signal.
        
    Returns:
        float: Signal power.
    """
    if signal.ndim == 1:
        return float(np.mean(signal ** 2))
    else:
        # For multi-dimensional signals (e.g., trajectory), calculate per dimension and average
        return float(np.mean(signal ** 2))

def calculate_noise_power(noise: np.ndarray) -> float:
    """
    Calculate the power of the noise (mean of squared values).
    
    Args:
        noise: 1D or 2D numpy array representing the noise.
        
    Returns:
        float: Noise power.
    """
    if noise.ndim == 1:
        return float(np.mean(noise ** 2))
    else:
        return float(np.mean(noise ** 2))

def calculate_snr(signal: np.ndarray, noise: np.ndarray) -> float:
    """
    Calculate Signal-to-Noise Ratio (SNR) in decibels.
    SNR_dB = 10 * log10(P_signal / P_noise)
    
    Args:
        signal: 1D or 2D numpy array representing the signal.
        noise: 1D or 2D numpy array representing the noise.
        
    Returns:
        float: SNR in decibels.
    """
    signal_power = calculate_signal_power(signal)
    noise_power = calculate_noise_power(noise)
    
    if noise_power == 0:
        return float('inf')
    
    snr_linear = signal_power / noise_power
    return 10 * np.log10(snr_linear)

def inject_gaussian_noise(
    trajectory: Trajectory, 
    target_snr_db: float, 
    seed: Optional[int] = None
) -> NoisyTrajectory:
    """
    Inject additive Gaussian noise to achieve a target SNR.
    
    Args:
        trajectory: Clean trajectory data.
        target_snr_db: Target SNR in decibels.
        seed: Random seed for reproducibility.
        
    Returns:
        NoisyTrajectory: Trajectory with injected noise and metadata.
        
    Raises:
        ValueError: If target_snr_db is not a finite number.
    """
    if not np.isfinite(target_snr_db):
        raise ValueError(f"Target SNR must be a finite number, got {target_snr_db}")
    
    if seed is not None:
        np.random.seed(seed)
        
    signal_data = trajectory.data
    signal_power = calculate_signal_power(signal_data)
    
    # Calculate required noise power for target SNR
    # SNR_dB = 10 * log10(P_signal / P_noise)
    # P_noise = P_signal / 10^(SNR_dB / 10)
    target_snr_linear = 10 ** (target_snr_db / 10)
    if target_snr_linear == 0:
        noise_power = float('inf')
    else:
        noise_power = signal_power / target_snr_linear
        
    noise_std = np.sqrt(noise_power)
    noise = np.random.normal(0, noise_std, signal_data.shape)
    
    noisy_data = signal_data + noise
    
    # Verify actual SNR
    actual_snr = calculate_snr(signal_data, noise)
    
    return NoisyTrajectory(
        data=noisy_data,
        clean_data=signal_data,
        noise_type=NoiseType.GAUSSIAN,
        target_snr_db=target_snr_db,
        actual_snr_db=actual_snr,
        noise_std=noise_std,
        seed=seed
    )

def inject_quantization_noise(
    trajectory: Trajectory, 
    bit_resolution: int, 
    seed: Optional[int] = None
) -> NoisyTrajectory:
    """
    Inject uniform quantization noise based on bit resolution.
    Quantization noise is modeled as uniform distribution in [-q/2, q/2]
    where q is the quantization step size.
    
    Args:
        trajectory: Clean trajectory data.
        bit_resolution: Number of bits for quantization (e.g., 8, 12, 16).
        seed: Random seed for reproducibility.
        
    Returns:
        NoisyTrajectory: Trajectory with injected quantization noise and metadata.
        
    Raises:
        ValueError: If bit_resolution is not a positive integer.
    """
    if not isinstance(bit_resolution, int) or bit_resolution <= 0:
        raise ValueError(f"Bit resolution must be a positive integer, got {bit_resolution}")
        
    if seed is not None:
        np.random.seed(seed)
        
    signal_data = trajectory.data
    data_min = np.min(signal_data)
    data_max = np.max(signal_data)
    data_range = data_max - data_min
    
    if data_range == 0:
        # If signal is constant, no quantization noise can be added meaningfully
        logger.warning("Signal range is zero, adding zero noise")
        return NoisyTrajectory(
            data=signal_data.copy(),
            clean_data=signal_data,
            noise_type=NoiseType.QUANTIZATION,
            target_snr_db=float('inf'),
            actual_snr_db=float('inf'),
            noise_std=0.0,
            seed=seed,
            bit_resolution=bit_resolution
        )
    
    # Quantization step size
    num_levels = 2 ** bit_resolution
    q = data_range / num_levels
    
    # Quantization noise is approximately uniform in [-q/2, q/2]
    # Standard deviation of uniform distribution is q / sqrt(12)
    noise_std = q / np.sqrt(12)
    noise = np.random.uniform(-q/2, q/2, signal_data.shape)
    
    # Quantize the signal
    # Normalize to [0, num_levels), round, then scale back
    normalized = (signal_data - data_min) / data_range
    quantized_normalized = np.round(normalized * (num_levels - 1)) / (num_levels - 1)
    quantized_data = data_min + quantized_normalized * data_range
    
    # The "noise" is the difference between clean and quantized
    # But for the NoisyTrajectory, we want the quantized signal
    # The noise component is implicitly the quantization error
    
    # Calculate actual SNR based on the quantization noise
    # The noise here is the quantization error
    quantization_error = signal_data - quantized_data
    actual_snr = calculate_snr(signal_data, quantization_error)
    
    return NoisyTrajectory(
        data=quantized_data,
        clean_data=signal_data,
        noise_type=NoiseType.QUANTIZATION,
        target_snr_db=actual_snr, # For quantization, the SNR is determined by bit depth
        actual_snr_db=actual_snr,
        noise_std=noise_std,
        seed=seed,
        bit_resolution=bit_resolution
    )

def verify_snr_accuracy(
    noisy_trajectory: NoisyTrajectory, 
    tolerance_db: float = 0.5
) -> bool:
    """
    Verify that the actual SNR matches the target SNR within a tolerance.
    
    Args:
        noisy_trajectory: Noisy trajectory with SNR metadata.
        tolerance_db: Acceptable difference in dB.
        
    Returns:
        bool: True if SNR is within tolerance, False otherwise.
    """
    if not np.isfinite(noisy_trajectory.actual_snr_db) or not np.isfinite(noisy_trajectory.target_snr_db):
        # For quantization noise, target_snr_db might be calculated as actual
        # If both are inf, it's acceptable
        if np.isinf(noisy_trajectory.actual_snr_db) and np.isinf(noisy_trajectory.target_snr_db):
            return True
        return False
        
    diff = abs(noisy_trajectory.actual_snr_db - noisy_trajectory.target_snr_db)
    return diff <= tolerance_db

def get_noise_injection_function(noise_type: NoiseType) -> Callable:
    """
    Get the appropriate noise injection function based on noise type.
    
    Args:
        noise_type: The type of noise to inject (GAUSSIAN or QUANTIZATION).
        
    Returns:
        Callable: The corresponding injection function.
        
    Raises:
        ValueError: If noise_type is not supported.
    """
    if noise_type == NoiseType.GAUSSIAN:
        return inject_gaussian_noise
    elif noise_type == NoiseType.QUANTIZATION:
        return inject_quantization_noise
    else:
        raise ValueError(
            f"Unsupported noise type: {noise_type}. "
            f"Only {NoiseType.GAUSSIAN} and {NoiseType.QUANTIZATION} are supported."
        )

def get_noise_injection_functions() -> Dict[NoiseType, Callable]:
    """
    Get a dictionary of all supported noise injection functions.
    
    Returns:
        Dict[NoiseType, Callable]: Mapping of noise types to injection functions.
    """
    return {
        NoiseType.GAUSSIAN: inject_gaussian_noise,
        NoiseType.QUANTIZATION: inject_quantization_noise
    }
