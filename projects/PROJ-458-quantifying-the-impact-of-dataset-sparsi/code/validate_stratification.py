import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
from scipy.spatial.distance import jensenshannon

# Import existing utilities from the project
from utils.logging import get_logger
from utils.cpu_constraints import enforce_memory_limit

# Configuration constants
DIVERGENCE_THRESHOLD = 0.05
RSS_POOL_PATH = "data/processed/rss_pool.csv"
FULL_POOL_PATH = "data/processed/full_pool_final.csv"
METADATA_DIR = "data/metadata"
REPORT_PATH = os.path.join(METADATA_DIR, "stratification_report.json")

logger = get_logger(__name__)

def load_subset_data(path: str) -> pd.DataFrame:
    """Load a CSV dataset, failing loudly if the file is missing."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required input file missing: {path}. "
                                "Ensure prerequisite tasks (T027, T031) have completed successfully.")
    logger.info(f"Loading data from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def compute_jensen_shannon_divergence(dist1: pd.Series, dist2: pd.Series) -> float:
    """
    Compute Jensen-Shannon divergence between two distributions.
    We bin the continuous variable (formation_energy) to create histograms.
    """
    # Determine common bins based on the union of both distributions
    min_val = min(dist1.min(), dist2.min())
    max_val = max(dist1.max(), dist2.max())
    
    # Avoid division by zero or empty ranges
    if min_val == max_val:
        return 0.0

    # Use a fixed number of bins for consistency
    n_bins = 50
    bins = np.linspace(min_val, max_val, n_bins + 1)
    
    # Calculate histograms (density=True ensures normalization)
    hist1, _ = np.histogram(dist1, bins=bins, density=True)
    hist2, _ = np.histogram(dist2, bins=bins, density=True)
    
    # Normalize to sum to 1 (probabilities) to satisfy JS divergence requirements
    # Adding a small epsilon to avoid log(0)
    epsilon = 1e-10
    p = hist1 + epsilon
    q = hist2 + epsilon
    p = p / p.sum()
    q = q / q.sum()
    
    # Calculate JS divergence
    js_div = jensenshannon(p, q) ** 2  # scipy returns sqrt(JS), so square it to get JS
    
    return float(js_div)

def compute_ks_test(dist1: pd.Series, dist2: pd.Series) -> Tuple[float, float]:
    """
    Perform Kolmogorov-Smirnov test to compare distributions.
    Returns (statistic, p-value).
    """
    stat, pvalue = ks_2samp(dist1, dist2)
    return float(stat), float(pvalue)

def validate_stratification(rss_df: pd.DataFrame, full_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate that the RSS pool is representative of the full pool.
    Uses Jensen-Shannon divergence on formation_energy distribution.
    
    Args:
        rss_df: DataFrame containing the RSS subset
        full_df: DataFrame containing the full pool (before RSS capping)
    
    Returns:
        Dictionary with validation metrics and status
    
    Raises:
        RuntimeError: If divergence exceeds threshold
    """
    target_column = "formation_energy"
    
    if target_column not in rss_df.columns or target_column not in full_df.columns:
        raise ValueError(f"Target column '{target_column}' not found in datasets.")
    
    rss_vals = rss_df[target_column].dropna()
    full_vals = full_df[target_column].dropna()
    
    if len(rss_vals) == 0 or len(full_vals) == 0:
        raise ValueError("No valid data found for stratification validation.")
    
    # Compute JS Divergence
    js_div = compute_jensen_shannon_divergence(rss_vals, full_vals)
    
    # Compute KS Test
    ks_stat, ks_pval = compute_ks_test(rss_vals, full_vals)
    
    # Determine pass/fail
    is_valid = js_div <= DIVERGENCE_THRESHOLD
    
    result = {
        "status": "PASS" if is_valid else "FAIL",
        "js_divergence": js_div,
        "ks_statistic": ks_stat,
        "ks_p_value": ks_pval,
        "threshold": DIVERGENCE_THRESHOLD,
        "rss_count": len(rss_df),
        "full_count": len(full_df),
        "message": "Stratification validated successfully." if is_valid else f"Stratification failed: JS divergence ({js_div:.6f}) exceeds threshold ({DIVERGENCE_THRESHOLD})."
    }
    
    return result

def main(args=None):
    """
    Main entry point for the stratification validation script.
    Reads RSS pool and Full pool, validates, and saves report.
    """
    parser = argparse.ArgumentParser(description="Validate stratification of RSS pool against full pool.")
    parser.add_argument("--rss-path", type=str, default=RSS_POOL_PATH, help="Path to RSS pool CSV")
    parser.add_argument("--full-path", type=str, default=FULL_POOL_PATH, help="Path to full pool CSV")
    parser.add_argument("--output-path", type=str, default=REPORT_PATH, help="Path to output JSON report")
    parser.add_argument("--memory-limit-mb", type=int, default=8000, help="Memory limit in MB")
    
    parsed_args = parser.parse_args(args) if args else parser.parse_args()
    
    # Enforce memory constraints if needed
    try:
        enforce_memory_limit(parsed_args.memory_limit_mb)
    except MemoryError:
        logger.error("Memory limit exceeded before processing.")
        return 1

    # Ensure output directory exists
    output_dir = os.path.dirname(parsed_args.output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        # Load data
        rss_df = load_subset_data(parsed_args.rss_path)
        full_df = load_subset_data(parsed_args.full_path)
        
        logger.info("Starting stratification validation...")
        
        # Perform validation
        report = validate_stratification(rss_df, full_df)
        
        # Log results
        logger.info(f"Validation Status: {report['status']}")
        logger.info(f"JS Divergence: {report['js_divergence']:.6f}")
        logger.info(f"KS Statistic: {report['ks_statistic']:.6f}, P-value: {report['ks_p_value']:.6f}")
        
        # Save report
        with open(parsed_args.output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {parsed_args.output_path}")
        
        # Fail loudly if validation fails to block further execution
        if not report['status'] == 'PASS':
            logger.error(report['message'])
            raise RuntimeError(report['message'])
            
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File missing error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except RuntimeError as e:
        logger.error(f"Stratification validation failed: {e}")
        # Re-raise to ensure the pipeline stops
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
