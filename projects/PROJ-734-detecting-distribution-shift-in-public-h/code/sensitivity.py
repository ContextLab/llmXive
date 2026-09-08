"""
Sensitivity analysis for distribution shift detection.
Includes BOCPD prior sensitivity analysis.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional

from main import load_config
from mmd_detector import detect_shifts
from bocpd import run_bocpd_rolling_window
from pettitt import run_pettitt_rolling_window
from evaluate import compute_metrics

logger = logging.getLogger(__name__)

def generate_grid() -> List[Dict]:
    """
    Generate parameter grid for sensitivity analysis.
    Includes BOCPD prior variations.
    """
    config = load_config()
    
    # Base configurations
    bandwidths = ["median", "cv"]
    windows = [8, 12, 16]
    tolerances = [1, 2, 3]
    
    # BOCPD prior configurations
    bocpd_priors = [
        {"run_length_prior": "geometric", "geometric_lambda": 0.1},
        {"run_length_prior": "geometric", "geometric_lambda": 0.05},
        {"run_length_prior": "uniform", "bocpd_uniform_max": 100},
        {"run_length_prior": "uniform", "bocpd_uniform_max": 50}
    ]
    
    grid = []
    
    # MMD sensitivity grid
    for bw in bandwidths:
        for win in windows:
            for tol in tolerances:
                grid.append({
                    "method": "MMD",
                    "bandwidth_type": bw,
                    "window_size": win,
                    "tolerance_weeks": tol,
                    "config": {}
                })
    
    # BOCPD prior sensitivity grid
    for prior in bocpd_priors:
        for win in windows:
            grid.append({
                "method": "BOCPD",
                "prior_config": prior,
                "window_size": win,
                "tolerance_weeks": 2,  # Standard tolerance for BOCPD
                "config": {}
            })
    
    # Pettitt sensitivity grid (window only)
    for win in windows:
        grid.append({
            "method": "Pettitt",
            "window_size": win,
            "tolerance_weeks": 2,
            "config": {}
        })
    
    logger.info(f"Generated grid with {len(grid)} configurations")
    return grid

def run_single_config(config_params: Dict, ground_truth: pd.DataFrame, 
                      processed_data: pd.Series) -> Dict:
    """
    Run detection with single configuration.
    
    Args:
        config_params: Configuration parameters
        ground_truth: Ground truth events
        processed_data: Preprocessed time series
        
    Returns:
        Metrics dictionary
    """
    method = config_params.get("method", "MMD")
    window_size = config_params.get("window_size", 12)
    tolerance = config_params.get("tolerance_weeks", 2)
    
    try:
        if method == "MMD":
            # Run MMD detection
            mmd_config = {
                "window_size": window_size,
                "stride": 1,
                "bandwidth_type": config_params.get("bandwidth_type", "median"),
                "permutations": 100,  # Reduced for sensitivity analysis speed
                "alpha": 0.01
            }
            
            flags = detect_shifts(processed_data, config=mmd_config)
            
        elif method == "BOCPD":
            # Run BOCPD with specific prior
            prior_config = config_params.get("prior_config", {})
            bocpd_config = {
                "window_size": window_size,
                "stride": 1,
                "prior_config": prior_config
            }
            
            change_points = run_bocpd_rolling_window(
                processed_data,
                window_size=window_size,
                stride=1,
                prior_config=prior_config
            )
            
            # Convert change points to flags format
            flags = [{"week_id": cp["week_id"], "p_value": cp["statistic"]} 
                    for cp in change_points]
            
        elif method == "Pettitt":
            # Run Pettitt test
            pettitt_config = {
                "window_size": window_size,
                "stride": 1
            }
            
            change_points = run_pettitt_rolling_window(
                processed_data,
                window_size=window_size,
                stride=1
            )
            
            flags = [{"week_id": cp["week_id"], "p_value": cp["statistic"]} 
                    for cp in change_points]
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Calculate metrics
        detected_weeks = [f["week_id"] for f in flags]
        metrics = compute_metrics(detected_weeks, ground_truth, tolerance)
        
        # Add configuration details
        metrics["method"] = method
        metrics["window_size"] = window_size
        metrics["tolerance_weeks"] = tolerance
        
        if method == "BOCPD":
            metrics["prior_used"] = prior_config.get("run_length_prior", "unknown")
            if "geometric_lambda" in prior_config:
                metrics["prior_lambda"] = prior_config["geometric_lambda"]
            if "bocpd_uniform_max" in prior_config:
                metrics["prior_uniform_max"] = prior_config["bocpd_uniform_max"]
        
        if method == "MMD":
            metrics["bandwidth_type"] = config_params.get("bandwidth_type", "median")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error running config {config_params}: {e}")
        return {
            "method": method,
            "window_size": window_size,
            "tolerance_weeks": tolerance,
            "precision": np.nan,
            "recall": np.nan,
            "detection_delay": np.nan,
            "fpr": np.nan,
            "error": str(e)
        }

def run_grid_search(ground_truth: pd.DataFrame, processed_data: pd.Series) -> pd.DataFrame:
    """
    Run full grid search for sensitivity analysis.
    
    Args:
        ground_truth: Ground truth events
        processed_data: Preprocessed time series
        
    Returns:
        DataFrame with all results
    """
    grid = generate_grid()
    results = []
    
    logger.info(f"Starting sensitivity analysis with {len(grid)} configurations")
    
    for i, config_params in enumerate(grid):
        logger.info(f"Running configuration {i+1}/{len(grid)}: {config_params}")
        metrics = run_single_config(config_params, ground_truth, processed_data)
        results.append(metrics)
        
        # Log BOCPD prior sensitivity results
        if config_params.get("method") == "BOCPD":
            prior = config_params.get("prior_config", {})
            prior_type = prior.get("run_length_prior", "unknown")
            if "geometric_lambda" in prior:
                logger.info(f"BOCPD prior: {prior_type}, lambda={prior['geometric_lambda']}")
            elif "bocpd_uniform_max" in prior:
                logger.info(f"BOCPD prior: {prior_type}, max={prior['bocpd_uniform_max']}")
    
    df_results = pd.DataFrame(results)
    return df_results

def save_grid_results(results: pd.DataFrame, output_path: str = "data/processed/sensitivity.csv"):
    """Save sensitivity analysis results."""
    results.to_csv(output_path, index=False)
    logger.info(f"Saved sensitivity results to {output_path}")

def main():
    """Main entry point for sensitivity analysis."""
    import logging_setup
    logger = logging_setup.setup_logging("sensitivity")
    
    try:
        config = load_config()
        
        # Load processed data
        processed_path = "data/processed/ili_processed.csv"
        if not os.path.exists(processed_path):
            raise FileNotFoundError(f"Processed data not found: {processed_path}")
        
        data = pd.read_csv(processed_path)
        if 'ili_standardized' not in data.columns:
            raise ValueError("Column 'ili_standardized' not found")
        
        processed_series = data['ili_standardized']
        
        # Load ground truth
        gt_path = "data/raw/ground_truth_events.csv"
        if not os.path.exists(gt_path):
            raise FileNotFoundError(f"Ground truth not found: {gt_path}")
        
        ground_truth = pd.read_csv(gt_path)
        
        # Run sensitivity analysis
        results = run_grid_search(ground_truth, processed_series)
        
        # Save results
        save_grid_results(results)
        
        logger.info("Sensitivity analysis completed")
        
    except Exception as e:
        logger.error(f"Error in sensitivity analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
