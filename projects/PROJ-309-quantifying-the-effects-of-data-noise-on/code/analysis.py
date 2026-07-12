import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from metrics import compute_correlation_dimension, compute_lyapunov_exponent_rosenstein, compute_false_nearest_neighbors
from utils.data_models import MetricResult
from config import get_literature_bounds
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_metric_error(computed_value: float, ground_truth_value: float) -> float:
    """
    Calculate the absolute percentage error of a computed metric relative to ground truth.
    
    Formula: |computed_value - ground_truth_value| / |ground_truth_value| * 100
    
    Args:
        computed_value: The metric value computed from noisy data.
        ground_truth_value: The metric value computed from clean data (T017 output).
        
    Returns:
        float: The percentage error.
        
    Raises:
        ZeroDivisionError: If ground_truth_value is zero.
    """
    if ground_truth_value == 0.0:
        raise ZeroDivisionError("Ground truth value cannot be zero for relative error calculation.")
    
    return abs(computed_value - ground_truth_value) / abs(ground_truth_value) * 100.0

def analyze_metric_degradation(
    noise_levels: List[float],
    metric_values: List[float],
    metric_name: str
) -> Dict[str, Any]:
    """
    Analyze the degradation of a specific metric across increasing noise levels.
    
    This function computes the error relative to a baseline (assumed to be the first
    value or provided separately in a full pipeline context) and identifies trends.
    
    Args:
        noise_levels: List of SNR levels (dB) corresponding to the measurements.
        metric_values: List of computed metric values for each noise level.
        metric_name: Name of the metric being analyzed (e.g., 'Lyapunov', 'Correlation_Dimension').
        
    Returns:
        Dict containing:
            - 'metric_name': str
            - 'noise_levels': list
            - 'values': list
            - 'errors': list (percentage error relative to the clean baseline)
            - 'trend': str ('increasing', 'decreasing', 'stable')
    """
    if len(noise_levels) != len(metric_values):
        raise ValueError("noise_levels and metric_values must have the same length.")
    
    if len(metric_values) == 0:
        return {
            'metric_name': metric_name,
            'noise_levels': [],
            'values': [],
            'errors': [],
            'trend': 'stable'
        }

    # Assume the first value (lowest noise/cleanest) is the ground truth baseline
    # In a full pipeline, this would be explicitly passed from T017 results
    baseline = metric_values[0]
    
    errors = []
    for val in metric_values:
        try:
            err = calculate_metric_error(val, baseline)
            errors.append(err)
        except ZeroDivisionError:
            logger.warning(f"Zero ground truth for {metric_name} at index {metric_values.index(val)}, setting error to 0.")
            errors.append(0.0)

    # Determine trend (simple linear regression slope sign)
    if len(noise_levels) < 2:
        trend = 'stable'
    else:
        # Calculate slope
        x = np.array(noise_levels)
        y = np.array(metric_values)
        if np.std(x) == 0:
            trend = 'stable'
        else:
            slope = np.polyfit(x, y, 1)[0]
            if slope > 1e-6:
                trend = 'increasing'
            elif slope < -1e-6:
                trend = 'decreasing'
            else:
                trend = 'stable'

    return {
        'metric_name': metric_name,
        'noise_levels': noise_levels,
        'values': metric_values,
        'errors': errors,
        'trend': trend
    }

def identify_fnn_threshold(
    snr_levels: List[float],
    fnn_rates: List[float],
    threshold_percentile: float = 50.0
) -> Optional[float]:
    """
    Identify the critical SNR threshold where the False Nearest Neighbors (FNN) rate
    exceeds a specified percentile of the maximum observed rate.
    
    This implements FR-008 (SC-003): identifying the point where reconstruction quality
    degrades significantly.
    
    Args:
        snr_levels: List of SNR levels (dB), sorted ascending or descending.
        fnn_rates: List of FNN rates corresponding to the SNR levels.
        threshold_percentile: The percentile of the max FNN rate to use as the critical threshold (default 50%).
        
    Returns:
        Optional[float]: The SNR level where the FNN rate first exceeds the threshold.
                         Returns None if the threshold is never reached.
    """
    if len(snr_levels) != len(fnn_rates):
        raise ValueError("snr_levels and fnn_rates must have the same length.")
    
    if len(fnn_rates) == 0:
        return None

    max_fnn = max(fnn_rates)
    critical_value = max_fnn * (threshold_percentile / 100.0)
    
    # Sort by SNR to find the transition point (assuming SNR decreases -> FNN increases)
    # We want the highest SNR where degradation starts.
    # Pair them up
    pairs = list(zip(snr_levels, fnn_rates))
    # Sort by SNR descending (high SNR -> low SNR)
    pairs.sort(key=lambda x: x[0], reverse=True)
    
    critical_snr = None
    
    for snr, fnn in pairs:
        if fnn >= critical_value:
            # We found a point with high degradation.
            # If we are iterating from high SNR to low SNR, the first one we hit
            # is the "critical" point where quality starts to fail.
            critical_snr = snr
            break
    
    # If no point exceeded the threshold, return None or the lowest SNR?
    # Per spec: "identify critical SNR threshold where FNN rate exceeds a majority level"
    # If it never exceeds, we can't identify a threshold.
    return critical_snr

def get_analysis_functions() -> List[str]:
    """
    Return a list of public function names in this module.
    
    Returns:
        List[str]: ['calculate_metric_error', 'analyze_metric_degradation', 'identify_fnn_threshold']
    """
    return [
        'calculate_metric_error',
        'analyze_metric_degradation',
        'identify_fnn_threshold'
    ]