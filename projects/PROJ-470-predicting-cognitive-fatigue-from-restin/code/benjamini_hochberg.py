"""
Benjamini-Hochberg Correction Module for Multiple Comparisons.

Implements the Benjamini-Hochberg (BH) procedure to control the False Discovery Rate (FDR)
across multiple hypothesis tests (e.g., correlations across EEG electrodes).

This module is designed to be run as a standalone script or imported as a library.
It reads analysis results from `data/analysis/correlation_results.csv`, applies the BH correction,
and writes the corrected results to `data/analysis/bh_corrected_results.csv`.
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ANALYSIS_DIR = DATA_DIR / "analysis"
INPUT_FILE = ANALYSIS_DIR / "correlation_results.csv"
OUTPUT_FILE = ANALYSIS_DIR / "bh_corrected_results.csv"

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = PROJECT_ROOT / "code" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name):
    """Setup a logger that writes to console and a file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler (optional, for pipeline logs)
        log_dir = PROJECT_ROOT / "logs"
        log_dir.mkdir(exist_ok=True)
        fh = logging.FileHandler(log_dir / f"{name}.log")
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

def run_benjamini_hochberg(p_values, alpha=0.05):
    """
    Apply the Benjamini-Hochberg procedure to a list of p-values.

    Parameters
    ----------
    p_values : array-like
        Array of p-values to correct.
    alpha : float
        Desired False Discovery Rate (FDR) threshold.

    Returns
    -------
    dict
        A dictionary containing:
        - 'rejected': Boolean array indicating which hypotheses are rejected.
        - 'adjusted_p_values': The BH-adjusted p-values.
        - 'thresholds': The BH thresholds used for comparison.
    """
    p_values = np.asarray(p_values)
    n = len(p_values)
    
    if n == 0:
        return {
            'rejected': np.array([]),
            'adjusted_p_values': np.array([]),
            'thresholds': np.array([])
        }

    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate BH thresholds
    # The threshold for the i-th smallest p-value is (i+1)/n * alpha
    ranks = np.arange(1, n + 1)
    thresholds = (ranks / n) * alpha
    
    # Determine rejection
    # Find the largest k such that p_(k) <= (k/n) * alpha
    # Then reject all hypotheses 1..k
    # We do this by checking from the largest rank downwards
    rejected = np.zeros(n, dtype=bool)
    
    # Standard BH step-down procedure
    # Find the largest i such that p_(i) <= (i/n) * alpha
    # Note: ranks are 1-based here
    for i in range(n - 1, -1, -1):
        if sorted_p_values[i] <= thresholds[i]:
            rejected[:i+1] = True
            break
    
    # Calculate adjusted p-values (q-values)
    # adjusted_p[i] = min( (n/k) * p_(k) for k >= i )
    # To ensure monotonicity, we take the cumulative minimum from the right
    adjusted = np.zeros(n)
    for i in range(n):
        # The adjusted p-value for the i-th sorted p-value is the minimum of
        # (n/k) * p_k for all k >= i
        candidates = (n / ranks[i:]) * sorted_p_values[i:]
        adjusted[i] = np.min(candidates)
    
    # Ensure adjusted p-values do not exceed 1.0
    adjusted = np.minimum(adjusted, 1.0)
    
    # Map back to original order
    final_rejected = np.zeros(n, dtype=bool)
    final_adjusted = np.zeros(n)
    
    final_rejected[sorted_indices] = rejected
    final_adjusted[sorted_indices] = adjusted
    
    return {
        'rejected': final_rejected,
        'adjusted_p_values': final_adjusted,
        'thresholds': thresholds  # Note: thresholds are aligned with sorted order, useful for debugging
    }

def main():
    """
    Main entry point for the Benjamini-Hochberg correction script.
    
    Reads correlation results from data/analysis/correlation_results.csv,
    applies BH correction across electrodes, and writes results to
    data/analysis/bh_corrected_results.csv.
    """
    logger = setup_logger("benjamini_hochberg")
    logger.info("Starting Benjamini-Hochberg correction pipeline.")
    
    # Load configuration
    try:
        config = load_config()
        alpha = config.get('fdr_threshold', 0.05)
        logger.info(f"Using FDR threshold (alpha): {alpha}")
    except Exception as e:
        logger.warning(f"Could not load config or find fdr_threshold, using default 0.05. Error: {e}")
        alpha = 0.05

    # Check input file
    if not INPUT_FILE.exists():
        logger.error(f"Input file not found: {INPUT_FILE}")
        logger.error("This script requires 'data/analysis/correlation_results.csv' to be generated by analysis.py first.")
        sys.exit(1)

    # Load data
    try:
        df = pd.read_csv(INPUT_FILE)
        logger.info(f"Loaded {len(df)} correlation results from {INPUT_FILE}")
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        sys.exit(1)

    # Validate required columns
    required_cols = ['p_value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in input file: {missing_cols}")
        logger.error(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    # Apply BH correction
    logger.info("Applying Benjamini-Hochberg correction...")
    results = run_benjamini_hochberg(df['p_value'].values, alpha=alpha)
    
    # Add results to dataframe
    df['is_significant_bh'] = results['rejected']
    df['p_value_adjusted'] = results['adjusted_p_values']
    
    # Sort by adjusted p-value for readability
    df_sorted = df.sort_values('p_value_adjusted')
    
    # Write output
    try:
        ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
        df_sorted.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Successfully wrote corrected results to {OUTPUT_FILE}")
        
        # Log summary
        num_rejected = np.sum(results['rejected'])
        logger.info(f"Summary: {num_rejected} out of {len(df)} hypotheses rejected at FDR {alpha}")
        
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        sys.exit(1)

    return 0

if __name__ == "__main__":
    sys.exit(main())