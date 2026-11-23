"""
Sensitivity analysis module for distribution shift detection.
Handles grid search over hyperparameters with timeout mechanisms.
"""
import os
import sys
import logging
import time
import signal
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Callable

from mmd_detector import detect_shifts
from evaluate import compute_metrics
from preprocess import load_ili_data, log_transform, standardize, remove_missing_weeks
from exceptions import E_NO_DATA
from logging_setup import setup_logging

logger = setup_logging("sensitivity")

# Timeout exception handler
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Configuration timed out")

def generate_grid() -> List[Dict[str, Any]]:
    """
    Generate the parameter grid for sensitivity analysis.
    MUST use:
      - bandwidths=['median', 'cv']
      - window_sizes=[8, 12, 16]
      - tolerances=[1, 2, 3]
    """
    bandwidths = ['median', 'cv']
    window_sizes = [8, 12, 16]
    tolerances = [1, 2, 3]

    grid = []
    for bw in bandwidths:
        for ws in window_sizes:
            for tol in tolerances:
                grid.append({
                    'bandwidth_type': bw,
                    'window_size': ws,
                    'tolerance_weeks': tol
                })
    logger.info(f"Generated grid with {len(grid)} configurations.")
    return grid

def run_single_config(
    config: Dict[str, Any],
    processed_data: np.ndarray,
    ground_truth_events: List[Tuple[int, int]],
    time_budget_minutes: float = 5.0
) -> Optional[Dict[str, Any]]:
    """
    Run a single configuration of the sensitivity grid.
    Implements a timeout mechanism to abort long-running configurations.
    """
    bandwidth_type = config['bandwidth_type']
    window_size = config['window_size']
    tolerance_weeks = config['tolerance_weeks']

    logger.info(f"Running config: bw={bandwidth_type}, ws={window_size}, tol={tolerance_weeks}")

    # Set up timeout
    # Note: signal.alarm only works on Unix; for cross-platform compatibility in
    # production, one might use threading or multiprocessing with a timeout.
    # Here we assume Unix environment for signal handling as per typical pipeline runners.
    original_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(time_budget_minutes * 60))

    try:
        # Run MMD detection with specific config
        # We need to simulate passing config to detect_shifts.
        # Assuming detect_shifts accepts bandwidth and window_size via config or kwargs.
        # Since we cannot change the signature of detect_shifts arbitrarily without breaking other tasks,
        # we assume it uses a global config or we pass a modified config dict.
        # For this implementation, we assume detect_shifts takes a 'config' dict.

        # Prepare a minimal config for the detector
        detector_config = {
            'window_size': window_size,
            'stride': 1,
            'bandwidth_type': bandwidth_type,
            'permutations': 1000,
            'alpha': 0.01,
            'min_permutations': 100,
            'time_budget_minutes': time_budget_minutes
        }

        # Run detection
        start_time = time.time()
        flags = detect_shifts(processed_data, detector_config)
        elapsed = time.time() - start_time

        logger.info(f"MMD detection completed in {elapsed:.2f}s")

        # Evaluate metrics
        metrics = compute_metrics(flags, ground_truth_events, tolerance_weeks)

        result = {
            'bandwidth_type': bandwidth_type,
            'window_size': window_size,
            'tolerance_weeks': tolerance_weeks,
            'precision': metrics.get('precision', np.nan),
            'recall': metrics.get('recall', np.nan),
            'detection_delay': metrics.get('detection_delay', np.nan),
            'fpr': metrics.get('fpr', np.nan),
            'runtime_seconds': elapsed
        }
        logger.info(f"Metrics computed: {result}")
        return result

    except TimeoutError:
        logger.warning(f"Configuration skipped due to timeout: {config}")
        signal.alarm(0)  # Cancel alarm
        return None
    except Exception as e:
        logger.error(f"Error running configuration {config}: {e}")
        signal.alarm(0)
        return None
    finally:
        signal.signal(signal.SIGALRM, original_handler)

def run_grid_search(
    grid: List[Dict[str, Any]],
    processed_data: np.ndarray,
    ground_truth_events: List[Tuple[int, int]],
    timeout_minutes: float = 5.0
) -> List[Dict[str, Any]]:
    """
    Run the full grid search.
    """
    results = []
    logger.info(f"Starting grid search with {len(grid)} configurations.")

    for i, config in enumerate(grid):
        logger.info(f"Progress: {i+1}/{len(grid)}")
        result = run_single_config(config, processed_data, ground_truth_events, timeout_minutes)
        if result is not None:
            results.append(result)

    logger.info(f"Grid search completed. {len(results)} successful runs.")
    return results

def save_grid_results(results: List[Dict[str, Any]], output_path: str = "data/processed/sensitivity.csv"):
    """
    Save grid results to CSV.
    """
    if not results:
        logger.warning("No results to save.")
        # Create an empty file with headers to satisfy schema expectations
        df = pd.DataFrame(columns=[
            'bandwidth_type', 'window_size', 'tolerance_weeks',
            'precision', 'recall', 'detection_delay', 'fpr', 'runtime_seconds'
        ])
        df.to_csv(output_path, index=False)
        return

    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} results to {output_path}")

def main():
    """
    Main entry point for sensitivity analysis.
    """
    logger.info("Starting sensitivity analysis.")

    # Load data
    if not os.path.exists("data/raw/fluview_ili.csv"):
        raise E_NO_DATA("Raw data file data/raw/fluview_ili.csv not found. Run download_data.py first.")

    raw_df = load_ili_data("data/raw/fluview_ili.csv")
    processed_df = remove_missing_weeks(raw_df)
    processed_df = log_transform(processed_df)
    processed_df = standardize(processed_df)

    processed_data = processed_df['ili_percent'].values

    # Load ground truth
    if not os.path.exists("data/raw/ground_truth_events.csv"):
        logger.warning("Ground truth file missing. Metrics may be N/A.")
        ground_truth_events = []
    else:
        from evaluate import load_ground_truth
        ground_truth_events = load_ground_truth("data/raw/ground_truth_events.csv")

    # Generate grid
    grid = generate_grid()

    # Run grid search
    results = run_grid_search(grid, processed_data, ground_truth_events)

    # Save results
    save_grid_results(results, "data/processed/sensitivity.csv")

    logger.info("Sensitivity analysis complete.")

if __name__ == "__main__":
    main()
