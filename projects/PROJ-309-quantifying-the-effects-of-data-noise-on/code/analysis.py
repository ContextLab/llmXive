import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from metrics import compute_correlation_dimension, compute_lyapunov_exponent_rosenstein, compute_false_nearest_neighbors
from utils.data_models import MetricResult
from config import get_literature_bounds
import logging
import os
import json
from utils.io import write_json_artifact

logger = logging.getLogger(__name__)

def calculate_metric_error(
    computed_value: float,
    ground_truth_value: float,
    metric_name: str
) -> float:
    """
    Calculate the absolute percentage error between a computed metric value
    and its ground truth reference.

    Formula: |computed_value - ground_truth_value| / |ground_truth_value| * 100

    Args:
        computed_value: The metric value calculated from noisy data.
        ground_truth_value: The reference metric value from clean data (T017).
        metric_name: Name of the metric for logging purposes.

    Returns:
        float: The percentage error.

    Raises:
        ZeroDivisionError: If ground_truth_value is zero.
    """
    if ground_truth_value == 0.0:
        # Handle the edge case where ground truth is zero (e.g., FNN might be 0)
        # In this case, if computed is also 0, error is 0. If computed > 0, error is effectively infinite.
        # We return a large number or handle specifically. For now, standard float division rules apply.
        if computed_value == 0.0:
            return 0.0
        else:
            # Avoid division by zero; return a sentinel or handle as per project needs.
            # Given the formula, if GT is 0, relative error is undefined.
            # We will raise to be explicit, or return float('inf') if preferred.
            # For this implementation, we raise to ensure the caller handles it.
            raise ZeroDivisionError(f"Cannot calculate relative error for {metric_name}: ground truth is 0.")

    error = abs(computed_value - ground_truth_value) / abs(ground_truth_value) * 100.0
    logger.debug(f"Error for {metric_name}: computed={computed_value:.4f}, gt={ground_truth_value:.4f}, error={error:.2f}%")
    return error

def analyze_metric_degradation(
    ground_truth_metrics: Dict[str, Dict[str, float]],
    noisy_metrics_list: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Analyze the degradation of metrics across noisy trajectories compared to ground truth.

    Args:
        ground_truth_metrics: A dictionary mapping metric names (e.g., 'correlation_dimension')
            to their ground truth values. Expected format:
            {
                "correlation_dimension": float,
                "lyapunov_exponent": float,
                "fnn_rate": float
            }
            Note: T017 produces a JSON file. This function expects the loaded dictionary.
            If the structure is nested (e.g., {"Lorenz": {...}}), the caller should flatten it.
            Assuming flat structure based on T017 description "Store results in ... ground_truth_metrics_{seed}.json".
            If T017 stores per-seed, this function should be called per-seed or aggregated.
            We assume the input `ground_truth_metrics` is the specific reference for the current analysis context.

        noisy_metrics_list: A list of dictionaries, each containing metric results for a noisy trajectory.
            Expected format for each item:
            {
                "snr_db": float,
                "noise_type": str,
                "correlation_dimension": float,
                "lyapunov_exponent": float,
                "fnn_rate": float,
                ... other metadata
            }

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing the error analysis for each noisy trajectory.
            Each item includes:
            {
                "snr_db": float,
                "noise_type": str,
                "metric_name": str,
                "computed_value": float,
                "ground_truth_value": float,
                "error_percent": float
            }
    """
    results = []

    # Define the metrics to compare
    metric_keys = ["correlation_dimension", "lyapunov_exponent", "fnn_rate"]

    for noisy_item in noisy_metrics_list:
        snr_db = noisy_item.get("snr_db", 0.0)
        noise_type = noisy_item.get("noise_type", "unknown")

        for metric_key in metric_keys:
            if metric_key not in ground_truth_metrics:
                logger.warning(f"Ground truth for {metric_key} not found. Skipping.")
                continue

            computed_val = noisy_item.get(metric_key)
            if computed_val is None:
                logger.warning(f"Computed value for {metric_key} missing in noisy item. Skipping.")
                continue

            gt_val = ground_truth_metrics[metric_key]

            try:
                error_pct = calculate_metric_error(computed_val, gt_val, metric_key)
            except ZeroDivisionError as e:
                logger.error(f"Skipping {metric_key} due to error: {e}")
                error_pct = float('inf') # Or handle as needed

            results.append({
                "snr_db": snr_db,
                "noise_type": noise_type,
                "metric_name": metric_key,
                "computed_value": computed_val,
                "ground_truth_value": gt_val,
                "error_percent": error_pct
            })

    return results

def identify_fnn_threshold(
    analysis_results: List[Dict[str, Any]],
    threshold_percent: float = 50.0
) -> Optional[float]:
    """
    Identify the critical SNR threshold where the False Nearest Neighbors (FNN) error rate
    exceeds a specified majority level (default 50%).

    Args:
        analysis_results: The list of error analysis results from `analyze_metric_degradation`.
        threshold_percent: The error percentage threshold to trigger the critical point detection.

    Returns:
        Optional[float]: The SNR value (in dB) where the threshold is first crossed.
            Returns None if the threshold is never crossed.
    """
    # Filter for FNN error results
    fnn_results = [
        r for r in analysis_results
        if r["metric_name"] == "fnn_rate"
    ]

    if not fnn_results:
        logger.warning("No FNN results found to identify threshold.")
        return None

    # Sort by SNR descending (usually noise increases as SNR decreases, so we look for the point where error spikes)
    # Or ascending SNR? The task says "identify critical SNR threshold".
    # Typically, as SNR decreases (noise increases), error increases.
    # We want the SNR value where error > 50%.
    # Let's sort by SNR descending (high SNR -> low SNR) to find the transition point.
    fnn_results.sort(key=lambda x: x["snr_db"], reverse=True)

    critical_snr = None
    for res in fnn_results:
        if res["error_percent"] >= threshold_percent:
            critical_snr = res["snr_db"]
            # We found the first point (from high SNR) where it exceeds.
            # Depending on definition, this might be the "threshold".
            # If we want the *lowest* SNR where it stays above, we'd continue.
            # But "identify critical SNR threshold" usually implies the point of degradation.
            # Let's return the first one encountered in the high-to-low scan.
            break

    if critical_snr is not None:
        logger.info(f"Critical FNN threshold identified at SNR: {critical_snr} dB")
    else:
        logger.info("No critical FNN threshold found (error never exceeded 50%).")

    return critical_snr

def get_analysis_functions() -> Dict[str, Any]:
    """
    Returns a dictionary of available analysis functions for external access.
    """
    return {
        "calculate_metric_error": calculate_metric_error,
        "analyze_metric_degradation": analyze_metric_degradation,
        "identify_fnn_threshold": identify_fnn_threshold
    }
