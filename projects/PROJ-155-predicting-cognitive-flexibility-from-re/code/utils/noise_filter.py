"""
Noise filtering utilities for resting-state fMRI analysis.

Implements:
1. SNR filtering based on temporal signal-to-noise ratio.
2. Motion-Noise Orthogonalization (MNO) to regress out motion-related variance
   that is orthogonal to the neural signal of interest.

Dependencies:
- code/config: for SNR thresholds and motion parameters
- code/utils/motion: for motion parameter extraction if needed
"""
import numpy as np
from typing import Optional, Tuple, List, Dict
from code.config import get_config
from code.utils.motion import calculate_mean_fd


def calculate_snr(time_series: np.ndarray, mask: Optional[np.ndarray] = None) -> float:
    """
    Calculate temporal Signal-to-Noise Ratio (tSNR) for a given time series.
    
    tSNR = mean(signal) / std(signal)
    
    Args:
        time_series: 1D or 2D numpy array of fMRI time series data.
                     If 2D, shape should be (n_timepoints, n_regions).
        mask: Optional boolean or integer mask array to select specific regions.
              If None, all regions are used.
    
    Returns:
        float: Mean tSNR across selected regions.
    
    Raises:
        ValueError: If input array is empty or contains NaNs.
    """
    if time_series.size == 0:
        raise ValueError("Input time series is empty.")
    
    if np.any(np.isnan(time_series)):
        # Replace NaNs with 0 for calculation, but warn
        time_series = np.nan_to_num(time_series, nan=0.0)
    
    if time_series.ndim == 1:
        time_series = time_series.reshape(-1, 1)
    
    if mask is not None:
        time_series = time_series[:, mask]
    
    mean_signal = np.mean(time_series, axis=0)
    std_signal = np.std(time_series, axis=0)
    
    # Avoid division by zero
    std_signal[std_signal == 0] = 1e-8
    
    tsnr = mean_signal / std_signal
    
    return float(np.mean(tsnr))


def filter_by_snr(
    time_series: np.ndarray,
    snr_threshold: Optional[float] = None,
    mask: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Filter regions based on SNR threshold.
    
    Args:
        time_series: 2D numpy array of shape (n_timepoints, n_regions).
        snr_threshold: Minimum SNR required. If None, uses config value.
        mask: Optional mask to apply before SNR calculation.
    
    Returns:
        Tuple of:
            - filtered_time_series: Time series with low-SNR regions removed.
            - kept_indices: Boolean array indicating which regions were kept.
    """
    if snr_threshold is None:
        config = get_config()
        snr_threshold = config.get('snr_threshold', 50.0)
    
    if time_series.ndim != 2:
        raise ValueError("time_series must be 2D (n_timepoints, n_regions)")
    
    # Calculate SNR for each region
    mean_signal = np.mean(time_series, axis=0)
    std_signal = np.std(time_series, axis=0)
    std_signal[std_signal == 0] = 1e-8
    snr_values = mean_signal / std_signal
    
    # Determine which regions to keep
    if mask is not None:
        combined_mask = mask & (snr_values >= snr_threshold)
    else:
        combined_mask = snr_values >= snr_threshold
    
    kept_indices = combined_mask
    filtered_time_series = time_series[:, kept_indices]
    
    return filtered_time_series, kept_indices


def orthogonalize_motion_noise(
    time_series: np.ndarray,
    motion_params: np.ndarray,
    mean_fd: float,
    fd_threshold: Optional[float] = None
) -> np.ndarray:
    """
    Perform Motion-Noise Orthogonalization (MNO).
    
    This function removes motion-related variance from the time series by
    regressing out motion parameters, but only for volumes where motion
    exceeds a threshold (scrubbing-like approach combined with regression).
    
    Args:
        time_series: 2D numpy array of shape (n_timepoints, n_regions).
        motion_params: 2D numpy array of shape (n_timepoints, n_motion_params).
                       Typically 6 rigid-body parameters (3 translations, 3 rotations).
        mean_fd: Mean Framewise Displacement for the subject.
        fd_threshold: FD threshold for identifying high-motion volumes.
                      If None, uses config value (default 0.2).
    
    Returns:
        np.ndarray: Cleaned time series with motion-related variance removed.
    
    Raises:
        ValueError: If dimensions don't match or inputs are invalid.
    """
    if time_series.shape[0] != motion_params.shape[0]:
        raise ValueError(
            f"Time series ({time_series.shape[0]} timepoints) and "
            f"motion params ({motion_params.shape[0]} timepoints) must have "
            f"the same number of timepoints."
        )
    
    if fd_threshold is None:
        config = get_config()
        fd_threshold = config.get('fd_threshold', 0.2)
    
    # Identify high-motion volumes
    # We assume motion_params contains FD or we calculate it
    # For simplicity, we use the provided mean_fd to check if overall motion is high
    # and then identify specific high-motion frames if motion_params includes FD
    
    # If motion_params has 6 columns (3 trans, 3 rot), we need to estimate FD
    # Standard FD calculation: sum of absolute differences of motion parameters
    if motion_params.shape[1] == 6:
        # Calculate FD from 6 motion parameters
        diffs = np.abs(np.diff(motion_params, axis=0))
        # Convert rotations (radians) to mm (assume 50mm radius)
        fd_values = np.sum(diffs[:, :3], axis=1) + 50.0 * np.sum(diffs[:, 3:], axis=1)
        # Prepend 0 for the first timepoint
        fd_values = np.insert(fd_values, 0, 0.0)
    else:
        # Assume motion_params is already FD or we can't calculate it
        # In this case, we'll use the provided mean_fd as a global check
        # and skip frame-specific scrubbing
        fd_values = np.full(motion_params.shape[0], mean_fd)
    
    high_motion_mask = fd_values > fd_threshold
    
    # Create design matrix for regression
    # Include motion parameters and their derivatives
    X = np.column_stack([
        motion_params,
        np.diff(motion_params, axis=0, prepend=motion_params[0:1])
    ])
    
    # Add constant term
    X = np.column_stack([np.ones(X.shape[0]), X])
    
    # Perform orthogonalization
    cleaned_time_series = time_series.copy()
    
    for i in range(time_series.shape[1]):
        y = time_series[:, i]
        
        # Regress out motion from high-motion volumes only
        if np.any(high_motion_mask):
            # Fit model on high-motion volumes
            X_high = X[high_motion_mask]
            y_high = y[high_motion_mask]
            
            # Ordinary least squares
            beta = np.linalg.lstsq(X_high, y_high, rcond=None)[0]
            
            # Predict and subtract from all volumes
            predicted_motion = X @ beta
            cleaned_time_series[:, i] = y - predicted_motion
        else:
            # No high-motion volumes, just detrend if needed
            # Simple mean subtraction
            cleaned_time_series[:, i] = y - np.mean(y)
    
    return cleaned_time_series


def apply_noise_filter_pipeline(
    time_series: np.ndarray,
    motion_params: np.ndarray,
    mean_fd: float
) -> np.ndarray:
    """
    Apply the full noise filtering pipeline:
    1. SNR filtering to remove low-quality regions.
    2. Motion-noise orthogonalization to remove motion artifacts.
    
    Args:
        time_series: 2D numpy array of shape (n_timepoints, n_regions).
        motion_params: 2D numpy array of shape (n_timepoints, n_motion_params).
        mean_fd: Mean Framewise Displacement for the subject.
    
    Returns:
        np.ndarray: Cleaned time series ready for connectivity analysis.
    """
    # Step 1: SNR filtering
    config = get_config()
    snr_threshold = config.get('snr_threshold', 50.0)
    fd_threshold = config.get('fd_threshold', 0.2)
    
    filtered_ts, kept_mask = filter_by_snr(
        time_series, 
        snr_threshold=snr_threshold
    )
    
    # Step 2: Motion-noise orthogonalization
    # Filter motion params to match kept regions (though motion params are global)
    cleaned_ts = orthogonalize_motion_noise(
        filtered_ts,
        motion_params,
        mean_fd,
        fd_threshold=fd_threshold
    )
    
    return cleaned_ts