"""
HRV Utility functions for signal validation and artifact rejection.

This module provides functions to:
- Validate signal structure
- Reject artifacts based on thresholds (< 5% valid beats)
- Compute clean RR interval statistics (RMSSD, SDNN)
"""
import numpy as np
from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SignalQualityError(Exception):
    """Raised when signal quality is insufficient for analysis."""
    pass


class ArtifactRejectionError(Exception):
    """Raised when artifact rejection fails or results in insufficient data."""
    pass


def validate_signal_structure(rr_intervals: np.ndarray) -> bool:
    """
    Validate the structure of RR interval data.
    
    Args:
        rr_intervals: Array of RR intervals in milliseconds.
        
    Returns:
        True if valid, False otherwise.
        
    Raises:
        SignalQualityError: If the input is invalid for analysis.
    """
    if not isinstance(rr_intervals, np.ndarray):
        raise SignalQualityError("Input must be a numpy array.")
    
    if len(rr_intervals) < 5:
        raise SignalQualityError("Insufficient data points for HRV analysis (need >= 5).")
    
    if np.any(rr_intervals <= 0):
        raise SignalQualityError("RR intervals must be positive values.")
    
    if np.any(np.isnan(rr_intervals)) or np.any(np.isinf(rr_intervals)):
        raise SignalQualityError("RR intervals contain NaN or Inf values.")
            
    return True


def reject_artifacts(rr_intervals: np.ndarray, threshold_percent: float = 5.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reject artifacts in RR intervals based on a threshold.
    
    This function identifies outliers that deviate significantly from the median
    and marks them as invalid. It enforces the constraint that at least 5% of beats
    must remain valid after rejection.
    
    Args:
        rr_intervals: Array of RR intervals in milliseconds.
        threshold_percent: Percentage deviation from median to consider an artifact.
                           Default is 5% (0.05).
                           
    Returns:
        Tuple of (cleaned_rr_intervals, valid_mask)
        - cleaned_rr_intervals: Array with artifacts removed (replaced by NaN or filtered)
        - valid_mask: Boolean array where True indicates valid data
        
    Raises:
        SignalQualityError: If input structure is invalid.
        ArtifactRejectionError: If fewer than 5% of beats remain valid.
    """
    validate_signal_structure(rr_intervals)
    
    median_rr = np.median(rr_intervals)
    deviation = np.abs(rr_intervals - median_rr)
    threshold = median_rr * (threshold_percent / 100.0)
    
    valid_mask = deviation <= threshold
    valid_count = np.sum(valid_mask)
    total_count = len(rr_intervals)
    
    if valid_count / total_count < 0.05: # < 5% valid beats
        raise ArtifactRejectionError(
            f"Insufficient valid beats after artifact rejection: "
            f"{valid_count}/{total_count} ({100*valid_count/total_count:.1f}%). "
            f"Threshold requires >= 5%."
        )
            
    # Return the original array with a mask for valid data
    # The caller should use the mask to filter data before calculation
    return rr_intervals, valid_mask


def compute_clean_rr_stats(rr_intervals: np.ndarray, valid_mask: Optional[np.ndarray] = None) -> Dict[str, float]:
    """
    Compute HRV metrics from clean RR intervals.
    
    Calculates RMSSD (Root Mean Square of Successive Differences) and SDNN
    (Standard Deviation of NN intervals).
    
    Args:
        rr_intervals: Array of RR intervals in milliseconds.
        valid_mask: Optional boolean array indicating valid data points.
                    If None, all data is assumed valid.
                    
    Returns:
        Dictionary containing:
        - rmssd: Root Mean Square of Successive Differences (ms)
        - sdnn: Standard Deviation of NN intervals (ms)
        - n_points: Number of valid data points used
        
    Raises:
        SignalQualityError: If insufficient valid data points remain for calculation.
    """
    if valid_mask is not None:
        rr_clean = rr_intervals[valid_mask]
    else:
        rr_clean = rr_intervals
        
    if len(rr_clean) < 2:
        raise SignalQualityError("Insufficient valid data points for HRV calculation.")
    
    # Calculate RMSSD
    # RMSSD = sqrt(mean((diff(RR))^2))
    diff_rr = np.diff(rr_clean)
    rmssd = np.sqrt(np.mean(diff_rr ** 2))
    
    # Calculate SDNN
    sdnn = np.std(rr_clean, ddof=1) # ddof=1 for sample standard deviation
    
    return {
        'rmssd': float(rmssd),
        'sdnn': float(sdnn),
        'n_points': int(len(rr_clean))
    }


def validate_hrv_output(stats: Dict[str, float]) -> bool:
    """
    Validate the output of HRV calculations.
    
    Args:
        stats: Dictionary containing HRV metrics.
        
    Returns:
        True if valid, False otherwise.
    """
    required_keys = ['rmssd', 'sdnn']
    if not all(key in stats for key in required_keys):
        logger.warning(f"HRV output missing required keys: {required_keys}")
        return False
        
    if stats['rmssd'] < 0 or stats['sdnn'] < 0:
        logger.warning("HRV metrics are negative.")
        return False
        
    return True