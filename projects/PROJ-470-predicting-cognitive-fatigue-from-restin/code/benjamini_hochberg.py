"""Benjamini-Hochberg correction for multiple comparisons across electrodes.

Implements FR-005: Apply BH correction to p-values from correlation analysis.
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np

# Import from local utils
from utils.logging import get_logger, save_exclusion_log_csv

# Import from analysis module if needed for config
# Note: We assume config is loaded via standard path or passed
# For this task, we focus on the correction logic

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return json.load(f) if config_path.endswith('.json') else __import__('yaml').safe_load(f)

def setup_logger(name, log_file=None):
    """Setup a logger that writes to file and console."""
    logger = get_logger(name, log_file)
    return logger

def run_benjamini_hochberg(input_file, output_file, alpha=0.05):
    """
    Apply Benjamini-Hochberg correction to p-values.

    Args:
        input_file (str): Path to CSV containing correlation results with p-values.
        output_file (str): Path to write corrected p-values.
        alpha (float): Significance threshold.

    Returns:
        pd.DataFrame: DataFrame with corrected p-values and significance flags.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Load correlation results
    df = pd.read_csv(input_file)

    # Identify p-value column(s). Usually 'p_value' or 'pval'
    p_col = None
    for col in ['p_value', 'pval', 'p']:
        if col in df.columns:
            p_col = col
            break

    if p_col is None:
        # Try to find any column containing 'p' and numeric
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        p_candidates = [c for c in numeric_cols if 'p' in c.lower()]
        if p_candidates:
            p_col = p_candidates[0]
        else:
            raise ValueError("No p-value column found in input file.")

    # Extract p-values
    p_values = df[p_col].values

    # Ensure no NaNs
    if np.any(np.isnan(p_values)):
        logging.warning("NaN p-values detected. Handling by exclusion.")
        valid_mask = ~np.isnan(p_values)
        valid_indices = np.where(valid_mask)[0]
        valid_p = p_values[valid_mask]
    else:
        valid_indices = np.arange(len(p_values))
        valid_p = p_values

    # Apply BH correction using statsmodels
    try:
        from statsmodels.stats.multitest import multipletests
        # multipletests returns (reject, p_adjusted, p_corrected, alphacSidak)
        # We use method='fdr_bh'
        reject, p_adjusted, _, _ = multipletests(valid_p, alpha=alpha, method='fdr_bh')
    except ImportError:
        raise ImportError("statsmodels is required for BH correction. Install with: pip install statsmodels")

    # Map back to original indices
    df['p_corrected'] = np.nan
    df.loc[valid_indices, 'p_corrected'] = p_adjusted
    df['significant_bh'] = False
    df.loc[valid_indices, 'significant_bh'] = reject

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Save to CSV
    df.to_csv(output_file, index=False)

    return df

def main():
    """Main entry point for BH correction task."""
    logger = setup_logger("benjamini_hochberg")
    logger.info("Starting Benjamini-Hochberg correction pipeline.")

    # Load config
    try:
        config = load_config()
    except FileNotFoundError:
        print("Warning: config.yaml not found. Using defaults.")
        config = {}

    # Define paths based on task description
    input_file = "data/analysis/correlation_results.csv"
    output_file = "data/analysis/bh_corrected_pvalues.csv"
    alpha = config.get('alpha', 0.05)

    # Check input exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        print(f"ERROR: Correlation results file not found at {input_file}.")
        print("Please run code/analysis.py first to generate correlation results.")
        sys.exit(1)

    try:
        df = run_benjamini_hochberg(input_file, output_file, alpha)
        logger.info(f"BH correction complete. Results saved to {output_file}")
        print(f"Success: BH-corrected p-values written to {output_file}")
        print(f"Significant electrodes at alpha={alpha}: {df['significant_bh'].sum()}")
    except Exception as e:
        logger.error(f"Error during BH correction: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
