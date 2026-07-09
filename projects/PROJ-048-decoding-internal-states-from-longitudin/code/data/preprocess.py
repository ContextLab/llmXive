"""
Preprocessing pipeline for Calcium Imaging data.
Handles dF/F normalization, detrending, missing data, deconvolution, and resampling.
"""
import numpy as np
import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

from utils.logger import get_logger, log_stage_start, log_stage_end, log_memory_usage
from utils.memory_monitor import check_memory_limit, MemoryExceededError

logger = get_logger(__name__)

class DataValidationError(Exception):
    """Raised when data validation checks fail."""
    pass

def dF_f_normalization(
    traces: np.ndarray,
    baseline_window: int = 100,
    baseline_percentile: float = 20.0
) -> np.ndarray:
    """
    Compute dF/F normalization for calcium traces.
    
    Args:
        traces: 2D numpy array of shape (n_rois, n_frames).
        baseline_window: Number of frames to use for rolling baseline.
        baseline_percentile: Percentile to use for baseline estimation.
        
    Returns:
        Normalized traces (dF/F).
    """
    check_memory_limit()
    logger.info(f"Starting dF/F normalization for shape {traces.shape}")
    
    # Estimate baseline F0 using rolling percentile
    # For simplicity, we use a global percentile if window is large or data is small
    if baseline_window >= traces.shape[1]:
        f0 = np.percentile(traces, baseline_percentile, axis=1, keepdims=True)
    else:
        # Rolling baseline calculation
        f0 = np.zeros_like(traces)
        for i in range(traces.shape[0]):
            # Use a simple rolling window approach
            for j in range(traces.shape[1]):
                start = max(0, j - baseline_window)
                end = j + 1
                f0[i, j] = np.percentile(traces[i, start:end], baseline_percentile)
    
    df_f = (traces - f0) / (f0 + 1e-8)  # Avoid division by zero
    logger.info("dF/F normalization complete.")
    return df_f

def detrend(
    traces: np.ndarray,
    order: int = 1
) -> np.ndarray:
    """
    Remove linear trends from traces.
    
    Args:
        traces: 2D numpy array of shape (n_rois, n_frames).
        order: Polynomial order for detrending.
        
    Returns:
        Detrended traces.
    """
    check_memory_limit()
    logger.info(f"Starting detrending with order {order}")
    
    n_rois, n_frames = traces.shape
    detrended = np.zeros_like(traces)
    
    # Create time vector
    t = np.arange(n_frames)
    
    for i in range(n_rois):
        # Fit polynomial
        coeffs = np.polyfit(t, traces[i], order)
        trend = np.polyval(coeffs, t)
        detrended[i] = traces[i] - trend
        
    logger.info("Detrending complete.")
    return detrended

def handle_missing_data(
    traces: np.ndarray,
    max_missing_ratio: float = 0.05
) -> np.ndarray:
    """
    Handle missing data (NaNs) by interpolation if within threshold.
    
    Args:
        traces: 2D numpy array.
        max_missing_ratio: Maximum allowed ratio of missing data per ROI.
        
    Returns:
        Cleaned traces with interpolated values.
        
    Raises:
        DataValidationError: If missing data exceeds threshold.
    """
    check_memory_limit()
    logger.info("Checking for missing data")
    
    n_rois, n_frames = traces.shape
    cleaned = traces.copy()
    
    for i in range(n_rois):
        mask = ~np.isnan(traces[i])
        missing_ratio = 1.0 - (np.sum(mask) / n_frames)
        
        if missing_ratio > max_missing_ratio:
            raise DataValidationError(
                f"Missing data exceeds {max_missing_ratio * 100}% threshold "
                f"for ROI {i} ({missing_ratio * 100:.2f}%)"
            )
        
        if missing_ratio > 0:
            # Linear interpolation
            x = np.arange(n_frames)
            cleaned[i] = np.interp(x, x[mask], traces[i, mask])
            
    logger.info("Missing data handling complete.")
    return cleaned

def deconvolve_oasis(
    traces: np.ndarray,
    tau: float = 1.0,
    fs: float = 10.0,
    p: float = 0.01
) -> np.ndarray:
    """
    Deconvolve calcium traces using OASIS algorithm to estimate spike rates.
    
    Args:
        traces: 2D numpy array (n_rois, n_frames).
        tau: Decay time constant of calcium indicator.
        fs: Sampling frequency in Hz.
        p: Sparsity parameter (penalty for non-zero spikes).
        
    Returns:
        Estimated spike rates.
    """
    check_memory_limit()
    logger.info(f"Starting OASIS deconvolution (tau={tau}, fs={fs})")
    
    dt = 1.0 / fs
    gamma = np.exp(-dt / tau)
    
    n_rois, n_frames = traces.shape
    spikes = np.zeros_like(traces)
    
    for i in range(n_rois):
        y = traces[i]
        # Simplified OASIS implementation (L1-regularized deconvolution)
        # c_{t} = gamma * c_{t-1} + s_{t}
        # y_{t} = c_{t} + noise
        # Solve for s >= 0 minimizing ||y - c||^2 + p * ||s||_1
        
        c = np.zeros(n_frames)
        s = np.zeros(n_frames)
        
        # Forward pass
        for t in range(1, n_frames):
            # Estimate c based on previous state and current observation
            # This is a simplified approximation of the OASIS algorithm
            c[t] = gamma * c[t-1]
            # Update with observation
            residual = y[t] - c[t]
            if residual > 0:
                s[t] = max(0, residual - p)
                c[t] += s[t]
            else:
                # If residual is negative, we don't add spikes
                # But we might need to adjust previous c if it was too high
                # For simplicity, we keep c as is and s as 0
                pass
                
        spikes[i] = s
        
    logger.info("OASIS deconvolution complete.")
    return spikes

def resample_to_behavior(
    imaging_data: np.ndarray,
    imaging_fs: float,
    behavior_data: np.ndarray,
    behavior_fs: float
) -> np.ndarray:
    """
    Resample imaging data to align with behavioral metadata sampling rate.
    
    This function aligns the temporal resolution of the imaging traces with
    the behavioral metadata by resampling (interpolating) the imaging data
    to match the behavioral sampling frequency.
    
    Args:
        imaging_data: 2D numpy array of shape (n_rois, n_frames_imaging).
        imaging_fs: Sampling frequency of imaging data in Hz.
        behavior_data: 2D numpy array of shape (n_behavior_vars, n_frames_behavior).
        behavior_fs: Sampling frequency of behavioral data in Hz.
        
    Returns:
        Resampled imaging data with shape (n_rois, n_frames_behavior).
        
    Raises:
        DataValidationError: If resampling cannot be performed (e.g., invalid frequencies).
    """
    check_memory_limit()
    logger.info(f"Resampling imaging data from {imaging_fs}Hz to {behavior_fs}Hz")
    
    if imaging_fs <= 0 or behavior_fs <= 0:
        raise DataValidationError("Sampling frequencies must be positive.")
    
    n_rois, n_frames_imaging = imaging_data.shape
    n_frames_behavior = behavior_data.shape[1]
    
    if n_frames_imaging == 0 or n_frames_behavior == 0:
        raise DataValidationError("Input data must have at least one frame.")
    
    # Create time vectors
    t_imaging = np.arange(n_frames_imaging) / imaging_fs
    t_behavior = np.arange(n_frames_behavior) / behavior_fs
    
    # Ensure behavior time vector is within imaging time range
    # If behavior data extends beyond imaging, we will extrapolate or clip
    if t_behavior[-1] > t_imaging[-1]:
        logger.warning(
            f"Behavior data extends beyond imaging data. "
            f"Imaging: {t_imaging[-1]:.2f}s, Behavior: {t_behavior[-1]:.2f}s. "
            "Clipping behavior time to imaging range."
        )
        # Clip behavior time to imaging range for interpolation
        t_behavior = t_behavior[t_behavior <= t_imaging[-1]]
        n_frames_behavior = len(t_behavior)
    
    resampled_data = np.zeros((n_rois, n_frames_behavior))
    
    for i in range(n_rois):
        # Use linear interpolation to resample
        # np.interp requires x coordinates in increasing order (they are)
        resampled_data[i] = np.interp(t_behavior, t_imaging, imaging_data[i])
        
    logger.info(f"Resampling complete. Output shape: {resampled_data.shape}")
    return resampled_data

def preprocess_pipeline(
    raw_traces: np.ndarray,
    imaging_fs: float,
    behavior_data: Optional[np.ndarray] = None,
    behavior_fs: Optional[float] = None,
    baseline_window: int = 100,
    baseline_percentile: float = 20.0,
    detrend_order: int = 1,
    max_missing_ratio: float = 0.05,
    oasis_tau: float = 1.0,
    oasis_p: float = 0.01
) -> Dict[str, np.ndarray]:
    """
    Complete preprocessing pipeline for calcium imaging data.
    
    Steps:
    1. Handle missing data (interpolate if <= 5%)
    2. dF/F normalization
    3. Detrending
    4. Deconvolution (OASIS)
    5. Resampling to behavioral rate (if behavior data provided)
    
    Args:
        raw_traces: Raw calcium traces (n_rois, n_frames).
        imaging_fs: Imaging sampling frequency.
        behavior_data: Optional behavioral metadata (n_vars, n_frames_behavior).
        behavior_fs: Optional behavioral sampling frequency.
        baseline_window: Window for dF/F baseline.
        baseline_percentile: Percentile for dF/F baseline.
        detrend_order: Polynomial order for detrending.
        max_missing_ratio: Max allowed missing data ratio.
        oasis_tau: OASIS decay time constant.
        oasis_p: OASIS sparsity parameter.
        
    Returns:
        Dictionary with keys:
            - 'normalized': dF/F normalized traces
            - 'detrended': Detrended traces
            - 'spikes': Deconvolved spike rates
            - 'resampled': Resampled traces (if behavior provided)
    """
    log_stage_start(logger, "preprocess_pipeline")
    check_memory_limit()
    
    result = {}
    
    # Step 1: Handle missing data
    logger.info("Step 1: Handling missing data")
    cleaned_traces = handle_missing_data(raw_traces, max_missing_ratio)
    
    # Step 2: dF/F normalization
    logger.info("Step 2: dF/F normalization")
    normalized = dF_f_normalization(cleaned_traces, baseline_window, baseline_percentile)
    result['normalized'] = normalized
    
    # Step 3: Detrending
    logger.info("Step 3: Detrending")
    detrended = detrend(normalized, detrend_order)
    result['detrended'] = detrended
    
    # Step 4: Deconvolution
    logger.info("Step 4: Deconvolution (OASIS)")
    spikes = deconvolve_oasis(detrended, oasis_tau, imaging_fs, oasis_p)
    result['spikes'] = spikes
    
    # Step 5: Resampling (if behavior data provided)
    if behavior_data is not None and behavior_fs is not None:
        logger.info("Step 5: Resampling to behavioral rate")
        resampled = resample_to_behavior(detrended, imaging_fs, behavior_data, behavior_fs)
        result['resampled'] = resampled
    else:
        logger.info("Step 5: Skipping resampling (no behavior data provided)")
        
    log_stage_end(logger, "preprocess_pipeline")
    return result

def main():
    """
    Main entry point for preprocessing pipeline.
    Demonstrates usage with sample data or loaded data.
    """
    log_stage_start(logger, "main")
    
    # Example usage with synthetic data (for demonstration)
    # In production, this would load from disk
    n_rois = 100
    n_frames = 10000
    imaging_fs = 30.0  # Hz
    
    # Generate synthetic traces
    np.random.seed(42)
    raw_traces = np.random.rand(n_rois, n_frames) * 1000
    
    # Add some missing data
    mask = np.random.rand(n_rois, n_frames) < 0.01
    raw_traces[mask] = np.nan
    
    # Generate synthetic behavior data
    behavior_fs = 100.0  # Hz
    n_frames_behavior = int(n_frames * (behavior_fs / imaging_fs))
    behavior_data = np.random.rand(5, n_frames_behavior)
    
    logger.info(f"Running pipeline on {n_rois} ROIs, {n_frames} frames at {imaging_fs}Hz")
    
    try:
        results = preprocess_pipeline(
            raw_traces=raw_traces,
            imaging_fs=imaging_fs,
            behavior_data=behavior_data,
            behavior_fs=behavior_fs
        )
        
        logger.info("Pipeline completed successfully.")
        for key, val in results.items():
            logger.info(f"  {key}: shape={val.shape}, dtype={val.dtype}")
            
    except DataValidationError as e:
        logger.error(f"Data validation error: {e}")
    except MemoryExceededError as e:
        logger.error(f"Memory limit exceeded: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
        
    log_stage_end(logger, "main")

if __name__ == "__main__":
    main()