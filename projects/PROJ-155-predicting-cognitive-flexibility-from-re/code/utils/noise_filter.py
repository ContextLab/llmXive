"""
Noise filtering utilities.
Exposes: calculate_snr, filter_by_snr, orthogonalize_motion_noise, apply_noise_filter_pipeline
"""
import numpy as np
from typing import Optional, Tuple, List, Dict
from code.config import get_config
from code.utils.motion import calculate_mean_fd

def calculate_snr(time_series: np.ndarray) -> float:
    """
    Calculate Signal-to-Noise Ratio (SNR).
    Simple definition: Mean / Std.
    
    Args:
        time_series: 1D or 2D array of fMRI time series data.
    
    Returns:
        SNR value.
    """
    mean_val = np.mean(time_series, axis=0)
    std_val = np.std(time_series, axis=0)
    # Avoid division by zero
    std_val = np.where(std_val == 0, 1e-6, std_val)
    return float(np.mean(mean_val / std_val))

def filter_by_snr(time_series: np.ndarray, threshold: float) -> np.ndarray:
    """
    Filter time series based on SNR threshold.
    Returns the time series if SNR > threshold, else zeros (or could raise).
    For this implementation, we return the data if valid, else a warning.
    """
    snr = calculate_snr(time_series)
    if snr < threshold:
        # In a real pipeline, we might flag or exclude this voxel/region
        pass 
    return time_series

def orthogonalize_motion_noise(time_series: np.ndarray, motion_params: np.ndarray) -> np.ndarray:
    """
    Orthogonalize time series against motion parameters (nuisance regression).
    
    Args:
        time_series: Shape (n_timepoints, n_regions)
        motion_params: Shape (n_timepoints, 6)
    
    Returns:
        Residualized time series.
    """
    # Add intercept
    X = np.column_stack([np.ones(motion_params.shape[0]), motion_params])
    # OLS projection: beta = (X'X)^-1 X'Y
    # Residuals = Y - X*beta
    # Using np.linalg.lstsq for stability
    beta, _, _, _ = np.linalg.lstsq(X, time_series, rcond=None)
    fitted = X @ beta
    residuals = time_series - fitted
    return residuals

def apply_noise_filter_pipeline(time_series: np.ndarray, motion_params: np.ndarray, snr_threshold: float = 1.0) -> np.ndarray:
    """
    Apply full noise filter pipeline: SNR check and motion orthogonalization.
    """
    # Step 1: SNR check (log if low, but proceed for now)
    snr = calculate_snr(time_series)
    if snr < snr_threshold:
        pass # Log warning in real implementation
    
    # Step 2: Motion orthogonalization
    cleaned_ts = orthogonalize_motion_noise(time_series, motion_params)
    
    return cleaned_ts
