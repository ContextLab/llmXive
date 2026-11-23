"""
HRV Utilities for artifact rejection and signal validation.

This module provides functions to validate ECG/PPG signals, reject artifacts
based on beat validity thresholds, and compute clean RR interval statistics.
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalQualityError(Exception):
    """Exception raised when signal quality is insufficient for analysis."""
    pass


class ArtifactRejectionError(Exception):
    """Exception raised when artifact rejection criteria are not met."""
    pass


def validate_signal_structure(
    signal: np.ndarray,
    sampling_rate: float,
    min_duration_seconds: float = 30.0,
    min_amplitude: float = 0.1,
    max_amplitude: float = 5.0
) -> Dict[str, Any]:
    """
    Validate the structure and quality of a physiological signal.

    Args:
        signal: 1D numpy array of signal values.
        sampling_rate: Sampling rate in Hz.
        min_duration_seconds: Minimum required duration in seconds.
        min_amplitude: Minimum expected signal amplitude.
        max_amplitude: Maximum expected signal amplitude.

    Returns:
        Dictionary with validation results:
        - valid: bool
        - duration: float (seconds)
        - sample_count: int
        - amplitude_range: tuple (min, max)
        - mean_amplitude: float
        - has_nan: bool
        - has_inf: bool

    Raises:
        SignalQualityError: If signal fails basic validation checks.
    """
    if not isinstance(signal, np.ndarray):
        raise SignalQualityError("Signal must be a numpy array.")

    if signal.ndim != 1:
        raise SignalQualityError(f"Signal must be 1D, got {signal.ndim}D.")

    if len(signal) == 0:
        raise SignalQualityError("Signal is empty.")

    # Check for NaN and Inf
    has_nan = np.any(np.isnan(signal))
    has_inf = np.any(np.isinf(signal))

    if has_nan or has_inf:
        raise SignalQualityError(f"Signal contains NaN ({has_nan}) or Inf ({has_inf}).")

    # Calculate duration
    duration = len(signal) / sampling_rate
    if duration < min_duration_seconds:
        raise SignalQualityError(
            f"Signal duration ({duration:.2f}s) is less than minimum "
            f"required ({min_duration_seconds}s)."
        )

    # Check amplitude range
    min_val = np.min(signal)
    max_val = np.max(signal)
    amplitude_range = (min_val, max_val)

    # Check for reasonable amplitude (avoid flat lines or extreme noise)
    if (max_val - min_val) < min_amplitude:
        raise SignalQualityError(
            f"Signal amplitude range ({max_val - min_val:.4f}) is too small "
            f"(min: {min_amplitude})."
        )

    if (max_val - min_val) > max_amplitude:
        logger.warning(
            f"Signal amplitude range ({max_val - min_val:.4f}) exceeds expected "
            f"maximum ({max_amplitude})."
        )

    return {
        "valid": True,
        "duration": duration,
        "sample_count": len(signal),
        "amplitude_range": amplitude_range,
        "mean_amplitude": np.mean(signal),
        "has_nan": has_nan,
        "has_inf": has_inf
    }


def reject_artifacts(
    rr_intervals: np.ndarray,
    valid_beats_threshold: float = 0.05
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Reject artifacts in RR intervals based on physiological plausibility.

    This function identifies and removes RR intervals that are physiologically
    implausible (e.g., < 0.3s or > 2.0s) and ensures that at least a minimum
    percentage of beats remain valid.

    Args:
        rr_intervals: 1D numpy array of RR intervals in seconds.
        valid_beats_threshold: Minimum fraction of valid beats required (default 0.05 = 5%).

    Returns:
        Tuple of:
        - clean_rr: numpy array of valid RR intervals.
        - rejection_mask: boolean array (True = rejected).
        - stats: Dictionary with rejection statistics.

    Raises:
        ArtifactRejectionError: If valid beats fall below the threshold.
    """
    if len(rr_intervals) == 0:
        raise ArtifactRejectionError("No RR intervals provided.")

    # Define physiological bounds for RR intervals (0.3s to 2.0s)
    # Corresponds to heart rates of 200 bpm to 30 bpm
    rr_min = 0.3
    rr_max = 2.0

    # Identify outliers
    rejection_mask = (rr_intervals < rr_min) | (rr_intervals > rr_max)

    clean_rr = rr_intervals[~rejection_mask]

    # Calculate valid beats percentage
    total_beats = len(rr_intervals)
    valid_beats = len(clean_rr)
    valid_percentage = valid_beats / total_beats

    stats = {
        "total_beats": total_beats,
        "rejected_beats": int(np.sum(rejection_mask)),
        "valid_beats": valid_beats,
        "valid_percentage": valid_percentage,
        "rejection_rate": 1.0 - valid_percentage
    }

    # Check if valid beats meet threshold
    if valid_percentage < valid_beats_threshold:
        raise ArtifactRejectionError(
            f"Valid beats percentage ({valid_percentage:.2%}) is below "
            f"threshold ({valid_beats_threshold:.2%}). "
            f"Only {valid_beats} of {total_beats} beats are valid."
        )

    logger.info(
        f"Artifact rejection complete: {stats['rejected_beats']} beats rejected "
        f"({stats['rejection_rate']:.2%}), {valid_percentage:.2%} remaining."
    )

    return clean_rr, rejection_mask, stats


def compute_clean_rr_stats(
    clean_rr: np.ndarray
) -> Dict[str, float]:
    """
    Compute statistics from cleaned RR intervals.

    Args:
        clean_rr: 1D numpy array of valid RR intervals in seconds.

    Returns:
        Dictionary with statistics:
        - mean_rr: Mean RR interval (s)
        - std_rr: Standard deviation of RR intervals (s)
        - min_rr: Minimum RR interval (s)
        - max_rr: Maximum RR interval (s)
        - mean_hr: Mean heart rate (bpm)
        - sdnn: SDNN (Standard Deviation of NN intervals) in ms
        - rmssd: RMSSD (Root Mean Square of Successive Differences) in ms
    """
    if len(clean_rr) == 0:
        raise ValueError("Cannot compute statistics from empty RR intervals.")

    # Basic statistics
    mean_rr = np.mean(clean_rr)
    std_rr = np.std(clean_rr)
    min_rr = np.min(clean_rr)
    max_rr = np.max(clean_rr)

    # Heart rate (bpm)
    mean_hr = 60.0 / mean_rr if mean_rr > 0 else 0.0

    # SDNN (in ms)
    sdnn = std_rr * 1000.0

    # RMSSD (in ms)
    if len(clean_rr) < 2:
        rmssd = 0.0
    else:
        successive_diffs = np.diff(clean_rr)
        rmssd = np.sqrt(np.mean(successive_diffs ** 2)) * 1000.0

    return {
        "mean_rr": mean_rr,
        "std_rr": std_rr,
        "min_rr": min_rr,
        "max_rr": max_rr,
        "mean_hr": mean_hr,
        "sdnn": sdnn,
        "rmssd": rmssd
    }


def validate_hrv_output(
    hrv_metrics: Dict[str, float],
    required_keys: Optional[List[str]] = None
) -> bool:
    """
    Validate that HRV output contains expected keys and valid values.

    Args:
        hrv_metrics: Dictionary of HRV metrics.
        required_keys: List of required keys (default: ['rmssd', 'sdnn']).

    Returns:
        True if validation passes.

    Raises:
        ValueError: If validation fails.
    """
    if required_keys is None:
        required_keys = ['rmssd', 'sdnn']

    # Check for required keys
    missing_keys = [key for key in required_keys if key not in hrv_metrics]
    if missing_keys:
        raise ValueError(f"Missing required HRV keys: {missing_keys}")

    # Check for valid numeric values
    for key, value in hrv_metrics.items():
        if not isinstance(value, (int, float)):
            raise ValueError(f"HRV metric '{key}' is not numeric: {value}")
        if np.isnan(value) or np.isinf(value):
            raise ValueError(f"HRV metric '{key}' is NaN or Inf: {value}")

    # Sanity checks for HRV values
    if hrv_metrics.get('rmssd', 0) < 0:
        raise ValueError("RMSSD cannot be negative.")
    if hrv_metrics.get('sdnn', 0) < 0:
        raise ValueError("SDNN cannot be negative.")
    if hrv_metrics.get('mean_hr', 0) < 20 or hrv_metrics.get('mean_hr', 0) > 200:
        logger.warning(
            f"Mean heart rate ({hrv_metrics.get('mean_hr'):.1f} bpm) outside "
            f"typical range (20-200 bpm)."
        )

    return True


def main():
    """
    Main function for testing HRV utilities.
    """
    logger.info("Testing HRV utilities...")

    # Generate synthetic RR intervals for testing
    np.random.seed(42)
    n_beats = 300
    base_rr = 0.8  # 75 bpm
    rr_intervals = base_rr + np.random.normal(0, 0.05, n_beats)

    # Add some artifacts
    artifact_indices = np.random.choice(n_beats, size=20, replace=False)
    rr_intervals[artifact_indices] = np.random.uniform(0.1, 0.25, 20)  # Too short

    try:
        # Validate signal structure (simulated)
        signal_validation = validate_signal_structure(
            np.random.normal(0, 1, 3000),  # Dummy signal
            sampling_rate=100.0
        )
        logger.info(f"Signal validation: {signal_validation}")

        # Reject artifacts
        clean_rr, mask, stats = reject_artifacts(rr_intervals)
        logger.info(f"Rejection stats: {stats}")

        # Compute statistics
        stats_output = compute_clean_rr_stats(clean_rr)
        logger.info(f"Clean RR stats: {stats_output}")

        # Validate output
        is_valid = validate_hrv_output(stats_output)
        logger.info(f"HRV output validation: {is_valid}")

    except (SignalQualityError, ArtifactRejectionError, ValueError) as e:
        logger.error(f"Validation failed: {e}")
        raise

    logger.info("HRV utilities test completed successfully.")


if __name__ == "__main__":
    main()