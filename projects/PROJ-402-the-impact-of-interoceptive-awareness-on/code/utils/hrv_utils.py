import numpy as np
from typing import Tuple, Dict, Any, Optional
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

class SignalQualityError(Exception):
    """Exception raised when signal quality is insufficient for analysis."""
    pass

class ArtifactRejectionError(Exception):
    """Exception raised when artifact rejection criteria are not met."""
    pass

def validate_signal_structure(signal: np.ndarray, sampling_rate: float) -> Dict[str, Any]:
    """
    Validate the structure and basic quality of a physiological signal.
    
    Args:
        signal: 1D numpy array of signal values.
        sampling_rate: Sampling rate in Hz.
        
    Returns:
        Dictionary containing validation results and metadata.
        
    Raises:
        SignalQualityError: If signal structure is invalid.
    """
    if not isinstance(signal, np.ndarray):
        raise SignalQualityError("Signal must be a numpy array.")
    
    if signal.ndim != 1:
        raise SignalQualityError(f"Signal must be 1D, got {signal.ndim}D.")
    
    if len(signal) == 0:
        raise SignalQualityError("Signal is empty.")
    
    if np.all(np.isnan(signal)):
        raise SignalQualityError("Signal contains only NaN values.")
    
    # Check for reasonable amplitude range (heuristic for ECG/PPG)
    # Assuming normalized or typical ECG/PPG ranges
    signal_range = np.nanmax(signal) - np.nanmin(signal)
    if signal_range < 1e-6:
        raise SignalQualityError("Signal range is too small, likely flatline or noise.")
    
    # Check for saturation (e.g., > 99% of values at max/min)
    if np.sum(np.isclose(signal, np.nanmax(signal))) > 0.99 * len(signal) or \
       np.sum(np.isclose(signal, np.nanmin(signal))) > 0.99 * len(signal):
        raise SignalQualityError("Signal appears saturated.")
    
    return {
        "valid": True,
        "length": len(signal),
        "sampling_rate": sampling_rate,
        "duration_seconds": len(signal) / sampling_rate,
        "min_val": float(np.nanmin(signal)),
        "max_val": float(np.nanmax(signal)),
        "mean_val": float(np.nanmean(signal)),
        "std_val": float(np.nanstd(signal))
    }

def reject_artifacts(
    rr_intervals: np.ndarray,
    threshold_percent: float = 5.0
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Reject artifacts from RR intervals based on a threshold of valid beats.
    
    This function filters RR intervals by removing outliers that deviate
    significantly from the local median, then checks if the remaining
    valid beats meet the minimum percentage threshold.
    
    Args:
        rr_intervals: 1D numpy array of RR intervals in seconds.
        threshold_percent: Minimum percentage of valid beats required (default 5%).
        
    Returns:
        Tuple of:
            - Cleaned RR intervals (numpy array)
            - Boolean mask indicating valid beats (True = valid)
            - Dictionary with rejection statistics
            
    Raises:
        ArtifactRejectionError: If valid beats fall below threshold_percent.
    """
    if len(rr_intervals) == 0:
        raise ArtifactRejectionError("RR intervals array is empty.")
    
    if np.all(np.isnan(rr_intervals)):
        raise ArtifactRejectionError("All RR intervals are NaN.")
    
    # Initial mask for non-NaN values
    valid_mask = ~np.isnan(rr_intervals)
    current_valid_count = np.sum(valid_mask)
    total_count = len(rr_intervals)
    
    if current_valid_count == 0:
        raise ArtifactRejectionError("No valid RR intervals found (all NaN).")
    
    # Iterative outlier removal based on median absolute deviation
    clean_rr = rr_intervals.copy()
    mask = valid_mask.copy()
    
    max_iterations = 10
    for i in range(max_iterations):
        current_rr = clean_rr[mask]
        if len(current_rr) == 0:
            break
            
        median_rr = np.median(current_rr)
        mad = np.median(np.abs(current_rr - median_rr))
        
        # Avoid division by zero if all values are identical
        if mad == 0:
            mad = 1e-6
        
        # Threshold for outlier detection (e.g., 3.5 MADs)
        # Adjusted to be robust but not overly aggressive
        lower_bound = median_rr - 3.5 * mad
        upper_bound = median_rr + 3.5 * mad
        
        # Update mask
        new_mask = mask & (clean_rr >= lower_bound) & (clean_rr <= upper_bound)
        
        # If no change, stop
        if np.array_equal(new_mask, mask):
            break
            
        mask = new_mask
    
    final_valid_count = np.sum(mask)
    valid_percentage = (final_valid_count / total_count) * 100
    
    stats = {
        "total_beats": total_count,
        "rejected_beats": total_count - final_valid_count,
        "valid_beats": final_valid_count,
        "valid_percentage": valid_percentage,
        "rejection_threshold": threshold_percent,
        "iterations": i + 1
    }
    
    if valid_percentage < threshold_percent:
        raise ArtifactRejectionError(
            f"Valid beats ({valid_percentage:.2f}%) below threshold ({threshold_percent}%). "
            f"Rejected {total_count - final_valid_count} out of {total_count} beats."
        )
    
    return clean_rr, mask, stats

def compute_clean_rr_stats(
    rr_intervals: np.ndarray,
    valid_mask: np.ndarray
) -> Dict[str, float]:
    """
    Compute statistics on cleaned RR intervals.
    
    Args:
        rr_intervals: 1D numpy array of RR intervals.
        valid_mask: Boolean mask indicating valid beats.
        
    Returns:
        Dictionary with RR interval statistics.
    """
    clean_rr = rr_intervals[valid_mask]
    
    if len(clean_rr) == 0:
        return {
            "mean_rr": np.nan,
            "median_rr": np.nan,
            "std_rr": np.nan,
            "min_rr": np.nan,
            "max_rr": np.nan,
            "n_valid": 0
        }
    
    return {
        "mean_rr": float(np.mean(clean_rr)),
        "median_rr": float(np.median(clean_rr)),
        "std_rr": float(np.std(clean_rr)),
        "min_rr": float(np.min(clean_rr)),
        "max_rr": float(np.max(clean_rr)),
        "n_valid": int(len(clean_rr))
    }

def validate_hrv_output(
    hrv_metrics: Dict[str, Any],
    required_keys: Optional[list] = None
) -> bool:
    """
    Validate the output of HRV calculation functions.
    
    Args:
        hrv_metrics: Dictionary containing HRV metrics.
        required_keys: List of required keys (default: ['RMSSD', 'SDNN']).
        
    Returns:
        True if validation passes, False otherwise.
        
    Raises:
        SignalQualityError: If validation fails.
    """
    if required_keys is None:
        required_keys = ['RMSSD', 'SDNN']
    
    if not isinstance(hrv_metrics, dict):
        raise SignalQualityError("HRV metrics must be a dictionary.")
    
    missing_keys = [key for key in required_keys if key not in hrv_metrics]
    if missing_keys:
        raise SignalQualityError(f"Missing required HRV metrics: {missing_keys}")
    
    for key in required_keys:
        value = hrv_metrics[key]
        if not isinstance(value, (int, float)):
            raise SignalQualityError(f"HRV metric '{key}' must be numeric, got {type(value)}.")
        
        if np.isnan(value) or np.isinf(value):
            raise SignalQualityError(f"HRV metric '{key}' is NaN or Inf.")
        
        if value < 0:
            raise SignalQualityError(f"HRV metric '{key}' is negative ({value}), which is invalid.")
    
    logger.info("HRV output validation passed.")
    return True

def main():
    """Main entry point for HRV utils - demonstration of functionality."""
    logging.basicConfig(level=logging.INFO)
    
    # Demonstrate signal validation
    logger.info("Demonstrating signal validation...")
    try:
        test_signal = np.random.randn(1000) * 0.5 + 1.0  # Simulated ECG-like signal
        sampling_rate = 1000.0  # Hz
        validation_result = validate_signal_structure(test_signal, sampling_rate)
        logger.info(f"Signal validation result: {validation_result}")
    except SignalQualityError as e:
        logger.error(f"Signal validation failed: {e}")
    
    # Demonstrate artifact rejection
    logger.info("Demonstrating artifact rejection...")
    try:
        # Generate synthetic RR intervals with some outliers
        rr_intervals = np.random.exponential(0.8, 100)  # Mean RR ~ 0.8s
        # Inject some artifacts
        rr_intervals[10] = 0.1  # Too short
        rr_intervals[20] = 2.0  # Too long
        rr_intervals[30] = np.nan  # Missing value
        
        clean_rr, mask, stats = reject_artifacts(rr_intervals, threshold_percent=5.0)
        logger.info(f"Artifact rejection stats: {stats}")
        logger.info(f"Cleaned RR intervals shape: {clean_rr[mask].shape}")
        
        # Compute stats on clean data
        clean_stats = compute_clean_rr_stats(rr_intervals, mask)
        logger.info(f"Clean RR stats: {clean_stats}")
        
    except ArtifactRejectionError as e:
        logger.error(f"Artifact rejection failed: {e}")
    
    # Demonstrate HRV output validation
    logger.info("Demonstrating HRV output validation...")
    try:
        sample_hrv = {"RMSSD": 45.0, "SDNN": 50.0}
        is_valid = validate_hrv_output(sample_hrv)
        logger.info(f"HRV output valid: {is_valid}")
    except SignalQualityError as e:
        logger.error(f"HRV validation failed: {e}")
    
    logger.info("HRV utils demonstration completed.")

if __name__ == "__main__":
    main()