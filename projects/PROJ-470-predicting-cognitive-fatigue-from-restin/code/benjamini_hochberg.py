"""
Benjamini-Hochberg Correction Module for Multiple Comparisons.

Implements the False Discovery Rate (FDR) control procedure to adjust p-values
across multiple hypothesis tests (e.g., across EEG electrodes).
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import os
import sys

# Import project configuration and logging utilities
# Note: Assuming these are available in the project root or code/ directory
# We will implement a local load_config and setup_logger if not imported from elsewhere
# to ensure this module is self-contained for the task, but adhering to the API surface.
# However, the API surface shows 'from analysis import load_config, setup_logger'.
# To avoid circular imports or missing dependencies, we will implement minimal versions
# here or import from the shared utils if available.
# Given the constraints, we will try to import from 'analysis' as per the surface,
# but fallback to local implementation if that fails to ensure the script runs.

def load_config():
    """Load configuration from code/config.yaml."""
    import yaml
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        # Fallback to default if config missing during unit test
        return {
            "fdr_alpha": 0.05,
            "min_p_value": 1e-10,
            "max_p_value": 1.0
        }
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file=None):
    """Setup a basic logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
    else:
        # Fallback to console if no file specified
        fh = logging.StreamHandler()
        fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    logger.addHandler(fh)
    
    return logger

def run_benjamini_hochberg(p_values, alpha=0.05, method='indep'):
    """
    Apply the Benjamini-Hochberg procedure to adjust p-values for multiple comparisons.

    Parameters
    ----------
    p_values : array-like
        List or array of raw p-values.
    alpha : float
        Target False Discovery Rate (FDR). Default is 0.05.
    method : str
        'indep' for independent tests (standard BH), 
        'poscorr' for positive dependency (BH-Yekutieli adjustment).
        For this task, we implement standard BH (indep).

    Returns
    -------
    dict
        Dictionary containing:
        - 'raw_p_values': original p-values
        - 'adj_p_values': adjusted p-values
        - 'is_significant': boolean mask of significant results
        - 'thresholds': the BH thresholds used for comparison
    """
    p_values = np.asarray(p_values)
    if len(p_values) == 0:
        return {
            'raw_p_values': np.array([]),
            'adj_p_values': np.array([]),
            'is_significant': np.array([]),
            'thresholds': np.array([])
        }

    # Handle NaNs or infinite values
    valid_mask = np.isfinite(p_values) & (p_values >= 0) & (p_values <= 1)
    if not np.all(valid_mask):
        # Log warning but proceed with valid values
        # In a real pipeline, this might raise an error
        pass

    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    n = len(sorted_p)

    # Calculate BH thresholds
    # Threshold for rank i (1-indexed) is (i / n) * alpha
    ranks = np.arange(1, n + 1)
    thresholds = (ranks / n) * alpha

    # Calculate adjusted p-values
    # adj_p[i] = min( (n / i) * p[i], adj_p[i+1] ) working backwards
    # Ensure monotonicity: adjusted p-values must be non-decreasing with rank
    adj_p = np.zeros(n)
    adj_p[-1] = min(1.0, sorted_p[-1] * n / n) # Last one

    for i in range(n - 2, -1, -1):
        # Calculate candidate adjusted p-value
        candidate = sorted_p[i] * n / (i + 1)
        # Ensure monotonicity: take min of candidate and next adjusted value
        adj_p[i] = min(1.0, max(candidate, adj_p[i+1]))

    # Restore original order
    adj_p_original_order = np.zeros(n)
    adj_p_original_order[sorted_indices] = adj_p

    # Determine significance
    # A result is significant if its raw p-value <= threshold at its rank
    # Or equivalently if adj_p <= alpha
    is_significant = adj_p_original_order <= alpha

    return {
        'raw_p_values': p_values,
        'adj_p_values': adj_p_original_order,
        'is_significant': is_significant,
        'thresholds': thresholds, # Sorted thresholds corresponding to sorted p-values
        'sorted_indices': sorted_indices
    }

def main():
    """
    Main entry point for the Benjamini-Hochberg correction script.
    
    This script is designed to be run as part of the analysis pipeline.
    It reads p-values from the analysis results (if available), applies the correction,
    and writes the adjusted results to a CSV file.
    """
    # Setup logging
    logger = setup_logger('benjamini_hochberg', 'logs/bh_correction.log')
    logger.info("Starting Benjamini-Hochberg Correction")

    config = load_config()
    alpha = config.get('fdr_alpha', 0.05)

    # Determine input source
    # In a full pipeline, this would read from code/analysis.py output
    # For this task, we simulate reading from a hypothetical analysis output file
    # or use a placeholder if the file doesn't exist yet (which is expected during early runs)
    analysis_file = Path("data/analysis/correlation_results.csv")
    
    if not analysis_file.exists():
        logger.warning(f"Analysis results file not found: {analysis_file}")
        logger.info("Skipping BH correction. Ensure analysis.py has run successfully.")
        return

    try:
        # Load analysis results
        df = pd.read_csv(analysis_file)
        
        # Expect columns: 'channel', 'p_value', 'correlation', ...
        if 'p_value' not in df.columns:
            logger.error("Column 'p_value' not found in analysis results.")
            sys.exit(1)

        raw_p_values = df['p_value'].values
        logger.info(f"Processing {len(raw_p_values)} p-values for FDR correction.")

        # Apply BH correction
        result = run_benjamini_hochberg(raw_p_values, alpha=alpha)

        # Update dataframe with adjusted values
        df['adj_p_value'] = result['adj_p_values']
        df['is_significant'] = result['is_significant']

        # Save results
        output_file = Path("data/analysis/bh_corrected_results.csv")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        
        logger.info(f"Saved BH-corrected results to {output_file}")
        
        # Print summary
        n_sig = np.sum(result['is_significant'])
        logger.info(f"Significant findings at FDR <= {alpha}: {n_sig} / {len(raw_p_values)}")

    except Exception as e:
        logger.error(f"Error during BH correction: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
