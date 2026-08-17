import numpy as np
from typing import List, Tuple, Dict, Optional
from scipy import stats
import pandas as pd
import os
import logging
from pathlib import Path

from src.utils import write_csv, get_logger
from src.config import get_data_root, get_project_root

logger = get_logger(__name__)

def pearson_correlation(x: List[float], y: List[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) == 0:
        return 0.0
    return float(stats.pearsonr(x, y)[0])

def spearman_correlation(x: List[float], y: List[float]) -> float:
    """Calculate Spearman rank correlation coefficient."""
    if len(x) != len(y) or len(x) == 0:
        return 0.0
    return float(stats.spearmanr(x, y)[0])

def bootstrap_confidence_interval(
    x: List[float],
    y: List[float],
    n_bootstraps: int = 1000,
    confidence_level: float = 0.95,
    method: str = 'pearson'
) -> Tuple[float, float, float]:
    """
    Calculate correlation and bootstrap confidence interval.
    
    Returns:
        (correlation, lower_ci, upper_ci)
    """
    if len(x) != len(y) or len(x) == 0:
        return 0.0, 0.0, 0.0
    
    x_arr = np.array(x)
    y_arr = np.array(y)
    n = len(x_arr)
    
    # Calculate point estimate
    if method == 'pearson':
        point_est = stats.pearsonr(x_arr, y_arr)[0]
    else:
        point_est = stats.spearmanr(x_arr, y_arr)[0]
    
    # Bootstrap
    boot_estimates = []
    rng = np.random.default_rng(42)
    for _ in range(n_bootstraps):
        indices = rng.choice(n, size=n, replace=True)
        x_boot = x_arr[indices]
        y_boot = y_arr[indices]
        
        if method == 'pearson':
            est = stats.pearsonr(x_boot, y_boot)[0]
        else:
            est = stats.spearmanr(x_boot, y_boot)[0]
        
        boot_estimates.append(est)
    
    boot_estimates = np.array(boot_estimates)
    lower_ci = float(np.percentile(boot_estimates, (1 - confidence_level) / 2 * 100))
    upper_ci = float(np.percentile(boot_estimates, (1 + confidence_level) / 2 * 100))
    
    return float(point_est), lower_ci, upper_ci

def run_threshold_sweep(
    dimensions: List[str],
    correlations: Dict[str, float],
    thresholds: Optional[List[float]] = None
) -> pd.DataFrame:
    """
    Run threshold sweep analysis for sensitivity analysis (US3).
    
    For each dimension, classify its status at each threshold.
    Status is determined by comparing correlation to threshold:
    - "feature-sufficient": correlation >= threshold
    - "VLM-required": correlation < threshold
    
    Args:
        dimensions: List of dimension names
        correlations: Dict mapping dimension name to correlation value
        thresholds: List of thresholds to test. Defaults to [0.80, 0.85, 0.90]
        
    Returns:
        DataFrame with columns: [dimension, threshold, status]
    """
    if thresholds is None:
        thresholds = [0.80, 0.85, 0.90]
    
    results = []
    
    for dim in dimensions:
        corr = correlations.get(dim, 0.0)
        for thresh in thresholds:
            if corr >= thresh:
                status = "feature-sufficient"
            else:
                status = "VLM-required"
            
            results.append({
                "dimension": dim,
                "threshold": thresh,
                "status": status
            })
    
    df = pd.DataFrame(results)
    return df

def main():
    """
    Main entry point for T026: Threshold sweep implementation.
    
    This function:
    1. Loads dimension correlations from T017 output (simulated here by reading 
       from a standard location or computing from training results)
    2. Runs threshold sweep across {0.80, 0.85, 0.90}
    3. Writes raw classification outcomes to data/sensitivity_sweep_raw.csv
    
    Prerequisite: T017 must have completed and produced dimension classifications.
    """
    logger.info("Starting threshold sweep analysis (T026)")
    
    # Load correlations from training results
    # T016/T015 should have produced these. We expect a file with correlation data.
    data_root = get_data_root()
    processed_dir = Path(data_root) / "processed"
    
    # Try to load from the standard correlation results file
    correlation_file = processed_dir / "correlation_results.csv"
    
    if not correlation_file.exists():
        # Fallback: try to load from training output
        correlation_file = processed_dir / "training_results.csv"
    
    if not correlation_file.exists():
        logger.error(f"Correlation results file not found: {correlation_file}")
        logger.error("Prerequisite T016 (correlation calculation) may not have completed.")
        raise FileNotFoundError(
            f"Required correlation results file not found at {correlation_file}. "
            "Ensure T016 has completed successfully."
        )
    
    # Load correlation data
    df_corr = pd.read_csv(correlation_file)
    
    # Expect columns: dimension, correlation (or similar naming)
    # Adjust based on actual T016 output schema
    if 'dimension' not in df_corr.columns or 'correlation' not in df_corr.columns:
        # Try alternative column names
        possible_corr_cols = ['pearson', 'spearman', 'r_value', 'corr']
        corr_col = None
        for col in possible_corr_cols:
            if col in df_corr.columns:
                corr_col = col
                break
        
        if corr_col is None:
            logger.error(f"Could not find correlation column in {correlation_file}")
            logger.error(f"Available columns: {df_corr.columns.tolist()}")
            raise ValueError("Correlation column not found in results file")
        
        if 'dimension' not in df_corr.columns:
            logger.error("Could not find dimension column")
            raise ValueError("Dimension column not found in results file")
        
        dimensions = df_corr['dimension'].tolist()
        correlations = dict(zip(dimensions, df_corr[corr_col].tolist()))
    else:
        dimensions = df_corr['dimension'].tolist()
        correlations = dict(zip(dimensions, df_corr['correlation'].tolist()))
    
    logger.info(f"Loaded {len(dimensions)} dimensions with correlations")
    
    # Run threshold sweep
    thresholds = [0.80, 0.85, 0.90]
    sweep_df = run_threshold_sweep(dimensions, correlations, thresholds)
    
    # Write output
    output_path = Path(data_root) / "sensitivity_sweep_raw.csv"
    write_csv(sweep_df, str(output_path))
    
    logger.info(f"Threshold sweep completed. Output written to {output_path}")
    logger.info(f"Output shape: {sweep_df.shape}, columns: {sweep_df.columns.tolist()}")
    
    return sweep_df

if __name__ == "__main__":
    main()
