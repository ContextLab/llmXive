"""
Noise filtering utilities for SNR filtering and Motion-Noise Orthogonalization.

Exposed API:
    calculate_snr: Calculate Signal-to-Noise Ratio.
    filter_by_snr: Filter time series based on SNR threshold (returns boolean mask).
    orthogonalize_motion_noise: Regress out motion parameters from time series.
    apply_noise_filter_pipeline: End-to-end pipeline applying SNR check and orthogonalization.
"""
import numpy as np
from typing import Optional, Tuple, List, Dict, Union
from code.config import get_config
from code.utils.motion import calculate_mean_fd
import logging

logger = logging.getLogger(__name__)

def calculate_snr(time_series: np.ndarray) -> float:
    """
    Calculate Signal-to-Noise Ratio (SNR) for fMRI time series.
    
    Definition: Mean signal intensity / Standard deviation of signal.
    Computed across all timepoints and regions, then averaged.
    
    Args:
        time_series: 1D (n_timepoints) or 2D (n_timepoints, n_regions) array.
    
    Returns:
        float: Mean SNR value across all regions.
    """
    if time_series.ndim == 1:
        time_series = time_series.reshape(-1, 1)
    
    # Calculate mean and std across time axis (axis=0)
    mean_val = np.mean(time_series, axis=0)
    std_val = np.std(time_series, axis=0)
    
    # Avoid division by zero
    std_val = np.where(std_val == 0, 1e-8, std_val)
    
    # Calculate SNR per region
    snr_per_region = mean_val / std_val
    
    # Return mean SNR across all regions
    return float(np.mean(snr_per_region))

def filter_by_snr(time_series: np.ndarray, threshold: Optional[float] = None) -> Tuple[np.ndarray, bool]:
    """
    Check if time series meets SNR threshold.
    
    Args:
        time_series: 1D or 2D array of fMRI data.
        threshold: SNR threshold. If None, uses config value.
    
    Returns:
        Tuple of (time_series, passes_threshold).
        If passes_threshold is False, the data is considered noisy.
    """
    if threshold is None:
        config = get_config()
        threshold = config.get('snr_threshold', 1.0)
    
    snr = calculate_snr(time_series)
    passes = snr >= threshold
    
    if not passes:
        logger.warning(f"SNR {snr:.4f} is below threshold {threshold}. Data may be noisy.")
    
    return time_series, passes

def orthogonalize_motion_noise(time_series: np.ndarray, motion_params: np.ndarray) -> np.ndarray:
    """
    Orthogonalize time series against motion parameters using nuisance regression.
    
    This implements a standard linear regression approach to remove motion-related
    variance from the fMRI signal.
    
    Args:
        time_series: Shape (n_timepoints, n_regions).
        motion_params: Shape (n_timepoints, n_motion_params) (typically 6 rigid-body parameters).
    
    Returns:
        Residualized time series with motion effects removed.
        Shape: (n_timepoints, n_regions).
    """
    n_timepoints = time_series.shape[0]
    
    if motion_params.shape[0] != n_timepoints:
        raise ValueError(
            f"Time series ({n_timepoints} timepoints) and motion params "
            f"({motion_params.shape[0]} timepoints) length mismatch."
        )
    
    if motion_params.ndim == 1:
        motion_params = motion_params.reshape(-1, 1)
    
    # Design matrix: [intercept, motion_params]
    X = np.column_stack([np.ones(n_timepoints), motion_params])
    
    # Solve for beta using least squares for each region
    # Y = X * beta + error  =>  beta = (X'X)^-1 X'Y
    # We use np.linalg.lstsq for numerical stability
    
    residuals = np.zeros_like(time_series)
    
    for i in range(time_series.shape[1]):
        y = time_series[:, i]
        beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        fitted = X @ beta
        residuals[:, i] = y - fitted
    
    return residuals

def apply_noise_filter_pipeline(
    time_series: np.ndarray, 
    motion_params: np.ndarray, 
    snr_threshold: Optional[float] = None
) -> Tuple[np.ndarray, Dict[str, Union[float, bool]]]:
    """
    Apply full noise filter pipeline:
    1. Calculate and check SNR.
    2. Orthogonalize against motion parameters.
    
    Args:
        time_series: fMRI time series data (n_timepoints, n_regions).
        motion_params: Motion parameters (n_timepoints, 6).
        snr_threshold: Optional SNR threshold override.
    
    Returns:
        Tuple of (cleaned_time_series, metadata_dict).
        metadata_dict contains:
            - 'snr': Calculated SNR value.
            - 'snr_passed': Boolean indicating if SNR threshold was met.
    """
    # Step 1: SNR Check
    snr = calculate_snr(time_series)
    
    if snr_threshold is None:
        config = get_config()
        snr_threshold = config.get('snr_threshold', 1.0)
    
    snr_passed = snr >= snr_threshold
    
    if not snr_passed:
        logger.warning(
            f"Subject data SNR ({snr:.4f}) below threshold ({snr_threshold}). "
            "Proceeding with orthogonalization but flagging for review."
        )
    
    # Step 2: Motion Orthogonalization
    cleaned_ts = orthogonalize_motion_noise(time_series, motion_params)
    
    metadata = {
        'snr': snr,
        'snr_passed': snr_passed
    }
    
    return cleaned_ts, metadata

# CLI Entry Point for standalone testing
if __name__ == "__main__":
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="Test Noise Filter Pipeline")
    parser.add_argument("--test", action="store_true", help="Run unit tests on synthetic data")
    args = parser.parse_args()
    
    if args.test:
        # Generate synthetic test data
        np.random.seed(42)
        n_timepoints = 200
        n_regions = 200
        
        # Simulate signal + noise
        signal = np.random.randn(n_timepoints, n_regions) * 0.5
        noise = np.random.randn(n_timepoints, n_regions) * 0.2
        time_series = signal + noise
        
        # Simulate motion parameters (6 rigid body params)
        motion_params = np.random.randn(n_timepoints, 6) * 0.1
        
        print(f"Input shape: {time_series.shape}")
        print(f"Motion params shape: {motion_params.shape}")
        
        # Run pipeline
        cleaned, meta = apply_noise_filter_pipeline(time_series, motion_params)
        
        print(f"Cleaned shape: {cleaned.shape}")
        print(f"SNR: {meta['snr']:.4f}")
        print(f"SNR Passed: {meta['snr_passed']}")
        
        # Verify shape preservation
        assert cleaned.shape == time_series.shape, "Shape mismatch after orthogonalization"
        print("Test passed: Noise filter pipeline executed successfully.")
    else:
        print("Run with --test to execute verification on synthetic data.")