"""
Preprocessing module for calcium imaging data (US1).

This module implements:
- dF/F normalization
- Detrending
- Missing data handling (interpolation if ≤5% missing)
- Deconvolution using OASIS algorithm
- Resampling for behavioral alignment

Note: This is a stub implementation for task T010 testing.
Full implementation will be in T013 and T014.
"""

import numpy as np
from typing import Optional, Tuple
from utils.logger import get_logger, log_stage_start, log_stage_end
from utils.memory_monitor import check_memory_limit, MemoryExceededError

logger = get_logger(__name__)

class PreprocessingError(Exception):
    """Custom exception for preprocessing errors."""
    pass

def dF_f_normalization(
    traces: np.ndarray,
    baseline_window: int = 100
) -> np.ndarray:
    """
    Calculate dF/F normalization for calcium traces.
    
    Args:
        traces: 2D array of ROI traces (time x ROIs)
        baseline_window: Number of frames to use for baseline calculation
        
    Returns:
        Normalized dF/F traces
        
    Raises:
        PreprocessingError: If input is invalid
    """
    if traces.ndim != 2:
        raise PreprocessingError("Input traces must be 2D array")
    
    if traces.shape[0] < baseline_window:
        raise PreprocessingError(f"Traces too short for baseline window: {traces.shape[0]} < {baseline_window}")
    
    # Calculate baseline as rolling mean
    baseline = np.mean(traces[:baseline_window], axis=0)
    
    # Avoid division by zero
    baseline = np.where(baseline == 0, 1e-8, baseline)
    
    # Calculate dF/F
    df_f = (traces - baseline) / baseline
    
    return df_f

def detrend(
    traces: np.ndarray,
    order: int = 2
) -> np.ndarray:
    """
    Remove linear trends from calcium traces.
    
    Args:
        traces: 2D array of traces (time x ROIs)
        order: Polynomial order for detrending
        
    Returns:
        Detrended traces
    """
    from scipy.signal import detrend as scipy_detrend
    
    # Detrend each ROI independently
    detrended = np.apply_along_axis(
        lambda x: scipy_detrend(x, type='linear'),
        axis=0,
        arr=traces
    )
    
    return detrended

def handle_missing_data(
    traces: np.ndarray,
    max_missing_percent: float = 0.05
) -> Tuple[np.ndarray, bool]:
    """
    Handle missing data in traces.
    
    Args:
        traces: 2D array of traces (time x ROIs)
        max_missing_percent: Maximum allowed missing data percentage
        
    Returns:
        Tuple of (interpolated traces, success flag)
        
    Raises:
        PreprocessingError: If missing data exceeds threshold
    """
    total_elements = traces.size
    missing_count = np.sum(np.isnan(traces))
    missing_percent = missing_count / total_elements
    
    if missing_percent > max_missing_percent:
        raise PreprocessingError(
            f"Missing data exceeds 5% threshold: {missing_percent:.2%}"
        )
    
    if missing_count == 0:
        return traces, True
    
    # Interpolate missing values
    from scipy.interpolate import interp1d
    
    time_axis = np.arange(traces.shape[0])
    interpolated = traces.copy()
    
    for i in range(traces.shape[1]):
        col = traces[:, i]
        valid_mask = ~np.isnan(col)
        
        if np.sum(valid_mask) < 2:
            # Not enough valid points for interpolation
            col_filled = np.nan_to_num(col, nan=0.0)
        else:
            f = interp1d(
                time_axis[valid_mask],
                col[valid_mask],
                kind='linear',
                fill_value='extrapolate'
            )
            col_filled = f(time_axis)
        
        interpolated[:, i] = col_filled
    
    return interpolated, True

def deconvolve_oasis(
    traces: np.ndarray,
    tau: float = 1.0,
    fs: float = 30.0
) -> np.ndarray:
    """
    Deconvolve calcium traces using OASIS algorithm.
    
    Args:
        traces: 2D array of traces (time x ROIs)
        tau: Time constant of calcium indicator
        fs: Sampling frequency
        
    Returns:
        Estimated spike rates
    """
    # Placeholder for OASIS implementation
    # In real implementation, this would use the OASIS algorithm
    # For now, we'll use a simple exponential decay model
    
    dt = 1.0 / fs
    alpha = np.exp(-dt / tau)
    
    # Simple deconvolution approximation
    deconvolved = np.zeros_like(traces)
    deconvolved[0] = traces[0]
    
    for t in range(1, traces.shape[0]):
        deconvolved[t] = traces[t] - alpha * deconvolved[t-1]
    
    # Ensure non-negative
    deconvolved = np.maximum(deconvolved, 0)
    
    return deconvolved

def resample_to_behavior(
    traces: np.ndarray,
    traces_fs: float,
    behavior_fs: float,
    method: str = 'linear'
) -> np.ndarray:
    """
    Resample traces to match behavioral metadata sampling rate.
    
    Args:
        traces: 2D array of traces (time x ROIs)
        traces_fs: Original sampling frequency
        behavior_fs: Target sampling frequency
        method: Interpolation method
        
    Returns:
        Resampled traces
    """
    from scipy.interpolate import interp1d
    
    n_frames_original = traces.shape[0]
    n_frames_target = int(n_frames_original * behavior_fs / traces_fs)
    
    if n_frames_target == n_frames_original:
        return traces
    
    time_original = np.arange(n_frames_original) / traces_fs
    time_target = np.arange(n_frames_target) / behavior_fs
    
    resampled = np.zeros((n_frames_target, traces.shape[1]))
    
    for i in range(traces.shape[1]):
        f = interp1d(
            time_original,
            traces[:, i],
            kind=method,
            fill_value='extrapolate'
        )
        resampled[:, i] = f(time_target)
    
    return resampled

def preprocess_pipeline(
    raw_traces: np.ndarray,
    memory_limit_gb: float = 5.0,
    baseline_window: int = 100,
    tau: float = 1.0,
    fs: float = 30.0,
    behavior_fs: Optional[float] = None
) -> np.ndarray:
    """
    Complete preprocessing pipeline.
    
    Args:
        raw_traces: Raw calcium traces
        memory_limit_gb: Memory limit in GB
        baseline_window: Window for dF/F calculation
        tau: Calcium time constant
        fs: Sampling frequency
        behavior_fs: Target sampling frequency for behavioral alignment
        
    Returns:
        Preprocessed and deconvolved traces
    """
    log_stage_start("preprocess_pipeline", {"memory_limit_gb": memory_limit_gb})
    
    # Check memory limit
    check_memory_limit(memory_limit_gb)
    
    # Step 1: Handle missing data
    logger.info("Handling missing data...")
    traces, success = handle_missing_data(raw_traces)
    
    # Step 2: dF/F normalization
    logger.info("Applying dF/F normalization...")
    traces = dF_f_normalization(traces, baseline_window)
    
    # Step 3: Detrend
    logger.info("Detrending traces...")
    traces = detrend(traces)
    
    # Step 4: Deconvolution
    logger.info("Deconvolving traces...")
    traces = deconvolve_oasis(traces, tau, fs)
    
    # Step 5: Resample if behavior frequency specified
    if behavior_fs is not None:
        logger.info(f"Resampling to {behavior_fs} Hz...")
        traces = resample_to_behavior(traces, fs, behavior_fs)
    
    log_stage_end("preprocess_pipeline", {"output_shape": traces.shape})
    
    return traces

def main():
    """Main entry point for preprocessing."""
    logger.info("Starting preprocessing pipeline...")
    
    # Example usage with mock data
    np.random.seed(42)
    mock_traces = np.random.randn(1000, 50) * 0.1
    mock_traces[10:15, 10] = np.nan  # Introduce some NaNs
    
    try:
        result = preprocess_pipeline(mock_traces)
        logger.info(f"Preprocessing complete. Output shape: {result.shape}")
    except PreprocessingError as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()