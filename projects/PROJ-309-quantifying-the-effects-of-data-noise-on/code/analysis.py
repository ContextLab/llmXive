import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

def calculate_metric_error(
    computed_value: float,
    ground_truth_value: float
) -> float:
    """
    Calculate relative error percentage.

    Formula: |computed_value - ground_truth_value| / |ground_truth_value| × 100

    Args:
        computed_value: Value computed from noisy data.
        ground_truth_value: Value from clean data (T017 output).

    Returns:
        Error percentage. Returns 0.0 if both are 0, inf if ground truth is 0 but computed is not.
    """
    if ground_truth_value == 0:
        return 0.0 if computed_value == 0 else float('inf')
    return abs(computed_value - ground_truth_value) / abs(ground_truth_value) * 100.0

def identify_critical_threshold(
    snr_levels: List[float],
    errors: List[float],
    threshold_percent: float = 50.0
) -> Optional[float]:
    """
    Identify the SNR level where error exceeds a threshold.

    Args:
        snr_levels: List of SNR levels.
        errors: List of error percentages.
        threshold_percent: Error threshold (default 50%).

    Returns:
        Critical SNR level or None if threshold not exceeded.
    """
    for snr, err in zip(snr_levels, errors):
        if err > threshold_percent:
            return snr
    return None

def load_ground_truth_metrics(
    ground_truth_path: Path
) -> Dict[str, float]:
    """
    Load ground truth metrics from the JSON file produced by T017.

    Args:
        ground_truth_path: Path to the ground truth metrics JSON file.

    Returns:
        Dictionary mapping metric names to their ground truth values.
    """
    try:
        with open(ground_truth_path, 'r') as f:
            data = json.load(f)
        
        # Expected structure: {"metrics": {"correlation_dimension": ..., "lyapunov_exponent": ...}}
        if 'metrics' not in data:
            raise ValueError(f"Ground truth file {ground_truth_path} missing 'metrics' key")
        
        return data['metrics']
    except FileNotFoundError:
        logger.error(f"Ground truth file not found: {ground_truth_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in ground truth file {ground_truth_path}: {e}")
        raise

def analyze_results(
    results: List[Dict[str, Any]],
    ground_truth: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Analyze results against ground truth.

    Computes error for each metric using calculate_metric_error.
    The ground_truth MUST be sourced from Task T017 (Clean Trajectory Metrics).

    Args:
        results: List of result dictionaries, each containing 'metrics' dict.
        ground_truth: Ground truth values from clean data (T017 output).

    Returns:
        Annotated results list with 'errors' dict added to each entry.
    """
    analyzed = []
    for res in results:
        res_copy = res.copy()
        res_copy['errors'] = {}
        
        metrics = res.get('metrics', {})
        for metric, val in metrics.items():
            if metric in ground_truth:
                err = calculate_metric_error(val, ground_truth[metric])
                res_copy['errors'][metric] = err
            else:
                logger.warning(f"Metric '{metric}' not found in ground truth, skipping error calculation")
        
        analyzed.append(res_copy)
    
    return analyzed

def analyze_results_from_files(
    noisy_metrics_paths: List[Path],
    ground_truth_path: Path
) -> List[Dict[str, Any]]:
    """
    Load noisy metrics from multiple files and analyze against ground truth.

    This function loads metrics computed from noisy trajectories (US3) and
    compares them against the ground truth metrics from clean trajectories (T017).

    Args:
        noisy_metrics_paths: List of paths to noisy trajectory metric JSON files.
        ground_truth_path: Path to the ground truth metrics JSON file (T017 output).

    Returns:
        List of analyzed results with error calculations.
    """
    # Load ground truth
    ground_truth = load_ground_truth_metrics(ground_truth_path)
    logger.info(f"Loaded ground truth metrics: {list(ground_truth.keys())}")
    
    # Load and analyze each noisy result
    results = []
    for path in noisy_metrics_paths:
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Ensure metrics key exists
            if 'metrics' not in data:
                logger.warning(f"Skipping {path}: missing 'metrics' key")
                continue
            
            # Add metadata for tracking
            result = data.copy()
            result['source_file'] = str(path)
            results.append(result)
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load {path}: {e}")
            continue
    
    if not results:
        logger.warning("No valid noisy metrics files found to analyze")
        return []
    
    # Perform analysis
    analyzed = analyze_results(results, ground_truth)
    
    logger.info(f"Analyzed {len(analyzed)} results against ground truth")
    return analyzed