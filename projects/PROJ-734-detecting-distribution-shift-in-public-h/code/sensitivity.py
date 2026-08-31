"""
Sensitivity Analysis Module (T029, T030, T032 integration).

This module handles the grid search for kernel bandwidths and window lengths,
as well as the week-alignment tolerance sweep.

It produces:
- data/processed/grid_results.csv (for T029)
- data/processed/tolerance_results.csv (for T030)

T032 will aggregate these into sensitivity.csv.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional

# Import from existing modules
from main import load_config
from preprocess import preprocess_pipeline, load_ili_data, remove_missing_weeks, log_transform, standardize
from mmd_detector import detect_shifts
from evaluate import compute_metrics, load_ground_truth

logger = logging.getLogger(__name__)

# Grid parameters for T029
BANDWIDTHS = ['median', 'cv']  # median and coefficient of variation
WINDOW_SIZES = [8, 12, 16]

# Tolerance parameters for T030
TOLERANCES = [1, 2, 3]  # weeks

GRID_RESULTS_PATH = "data/processed/grid_results.csv"
TOLERANCE_RESULTS_PATH = "data/processed/tolerance_results.csv"

def run_grid_search(config: Dict) -> pd.DataFrame:
    """
    Run MMD detection with different bandwidths and window sizes.
    
    Args:
        config: Configuration dictionary.
    
    Returns:
        pd.DataFrame: Results of the grid search.
    """
    logger.info("Starting grid search for bandwidth and window size.")
    
    results = []
    
    # Load and preprocess data once
    try:
        ili_data = load_ili_data()
        ili_data = remove_missing_weeks(ili_data)
        ili_data = log_transform(ili_data)
        ili_data = standardize(ili_data)
    except Exception as e:
        logger.error(f"Failed to preprocess data for grid search: {e}")
        raise
    
    # Load ground truth for metrics calculation
    try:
        ground_truth = load_ground_truth()
    except Exception as e:
        logger.error(f"Failed to load ground truth for grid search: {e}")
        raise
    
    for bw in BANDWIDTHS:
        for ws in WINDOW_SIZES:
            logger.info(f"Running grid config: bandwidth={bw}, window_size={ws}")
            
            try:
                # Adjust config for this run
                run_config = config.copy()
                run_config['window_size'] = ws
                # Bandwidth is handled inside detect_shifts, but we can pass it as a hint
                # or modify the config if needed. Assuming detect_shifts calculates it internally.
                # We might need to force a specific bandwidth calculation method.
                # For now, we assume 'bw' parameter is passed to detect_shifts.
                
                # Run detection
                flags = detect_shifts(ili_data, config=run_config, bandwidth_method=bw)
                
                # Evaluate
                metrics = compute_metrics(flags, ground_truth, tolerance=2)  # Default tolerance for grid
                
                result = {
                    'bandwidth': bw,
                    'window_size': ws,
                    'precision': metrics['precision'],
                    'recall': metrics['recall'],
                    'f1_score': metrics['f1_score'],
                    'detection_delay': metrics['detection_delay']
                }
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error in grid config (bw={bw}, ws={ws}): {e}")
                # Continue to next config
                continue
    
    df = pd.DataFrame(results)
    logger.info(f"Grid search completed. Found {len(df)} successful configurations.")
    return df

def run_tolerance_sweep(config: Dict) -> pd.DataFrame:
    """
    Run MMD detection with different week-alignment tolerances.
    
    Args:
        config: Configuration dictionary.
    
    Returns:
        pd.DataFrame: Results of the tolerance sweep.
    """
    logger.info("Starting tolerance sweep.")
    
    results = []
    
    # Use default grid parameters for tolerance sweep
    # Or use the best parameters from the grid search if available.
    # For simplicity, we use the default config's window_size and median bandwidth.
    default_window_size = config.get('window_size', 12)
    bandwidth_method = 'median'
    
    # Load and preprocess data once
    try:
        ili_data = load_ili_data()
        ili_data = remove_missing_weeks(ili_data)
        ili_data = log_transform(ili_data)
        ili_data = standardize(ili_data)
    except Exception as e:
        logger.error(f"Failed to preprocess data for tolerance sweep: {e}")
        raise
    
    # Load ground truth
    try:
        ground_truth = load_ground_truth()
    except Exception as e:
        logger.error(f"Failed to load ground truth for tolerance sweep: {e}")
        raise
    
    # Run detection once with default params (since tolerance is only for evaluation)
    try:
        run_config = config.copy()
        run_config['window_size'] = default_window_size
        flags = detect_shifts(ili_data, config=run_config, bandwidth_method=bandwidth_method)
    except Exception as e:
        logger.error(f"Failed to run detection for tolerance sweep: {e}")
        raise
    
    for tol in TOLERANCES:
        logger.info(f"Running tolerance: {tol} weeks")
        
        try:
            metrics = compute_metrics(flags, ground_truth, tolerance=tol)
            
            result = {
                'tolerance': tol,
                'precision': metrics['precision'],
                'recall': metrics['recall'],
                'f1_score': metrics['f1_score'],
                'detection_delay': metrics['detection_delay']
            }
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error in tolerance {tol}: {e}")
            continue
    
    df = pd.DataFrame(results)
    logger.info(f"Tolerance sweep completed. Found {len(df)} successful configurations.")
    return df

def save_grid_results(df: pd.DataFrame, path: str):
    """Save grid results to CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Grid results saved to {path}")

def save_tolerance_results(df: pd.DataFrame, path: str):
    """Save tolerance results to CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Tolerance results saved to {path}")

def main():
    """Main entry point for sensitivity analysis."""
    from logging_setup import setup_logging
    setup_logging()
    
    logger.info("Starting sensitivity analysis (T029, T030).")
    
    try:
        config = load_config()
        
        # Run grid search
        grid_df = run_grid_search(config)
        save_grid_results(grid_df, GRID_RESULTS_PATH)
        
        # Run tolerance sweep
        tolerance_df = run_tolerance_sweep(config)
        save_tolerance_results(tolerance_df, TOLERANCE_RESULTS_PATH)
        
        logger.info("Sensitivity analysis completed.")
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
