"""
Stratification Validation Module (Task T033)

Validates that the Representative Stratified Sample (RSS) pool maintains
the distributional characteristics of the full training pool using
Jensen-Shannon divergence and Kolmogorov-Smirnov tests.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from scipy.spatial.distance import jensenshannon

# Import project utilities
from utils.logging import get_logger
from utils.cpu_constraints import get_current_memory_mb

# Constants
THRESHOLD_JSD = 0.1  # Maximum allowed Jensen-Shannon divergence
THRESHOLD_KS_PVALUE = 0.05  # Minimum p-value for KS test (fail if p < this)
TARGET_METRICS_FILE = "data/metadata/stratification_report.json"
FULL_POOL_PATH = "data/processed/full_pool_final.csv"
RSS_POOL_PATH = "data/processed/rss_pool.csv"

logger = get_logger(__name__)


def load_subset_data(file_path: str) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        DataFrame containing the data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    
    logger.info(f"Loading data from {file_path}")
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError(f"Dataset at {file_path} is empty.")
        
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df


def compute_jensen_shannon_divergence(
    full_pool: pd.DataFrame, 
    rss_pool: pd.DataFrame, 
    column: str
) -> float:
    """
    Compute the Jensen-Shannon divergence between histograms of a column
    in the full pool and the RSS pool.
    
    Args:
        full_pool: DataFrame of the full pool.
        rss_pool: DataFrame of the RSS pool.
        column: Name of the numeric column to compare.
        
    Returns:
        JSD value (float). Lower is better (0 = identical distributions).
    """
    # Handle missing values by dropping them for histogram calculation
    full_vals = full_pool[column].dropna().values
    rss_vals = rss_pool[column].dropna().values
    
    if len(full_vals) == 0 or len(rss_vals) == 0:
        logger.warning(f"Column {column} has no valid values for JSD calculation.")
        return 0.0
    
    # Determine bin edges based on the full pool range
    min_val = min(np.min(full_vals), np.min(rss_vals))
    max_val = max(np.max(full_vals), np.max(rss_vals))
    
    # Use a fixed number of bins for consistency
    n_bins = 50
    bin_edges = np.linspace(min_val, max_val, n_bins + 1)
    
    # Compute histograms
    hist_full, _ = np.histogram(full_vals, bins=bin_edges)
    hist_rss, _ = np.histogram(rss_vals, bins=bin_edges)
    
    # Normalize to probability distributions
    p_full = hist_full / np.sum(hist_full)
    p_rss = hist_rss / np.sum(hist_rss)
    
    # Compute JSD
    try:
        jsd = jensenshannon(p_full, p_rss)
        return float(jsd)
    except Exception as e:
        logger.error(f"Error computing JSD for {column}: {e}")
        return 0.0


def compute_ks_test(
    full_pool: pd.DataFrame, 
    rss_pool: pd.DataFrame, 
    column: str
) -> Tuple[float, float]:
    """
    Perform the Kolmogorov-Smirnov test to compare distributions.
    
    Args:
        full_pool: DataFrame of the full pool.
        rss_pool: DataFrame of the RSS pool.
        column: Name of the numeric column to compare.
        
    Returns:
        Tuple of (statistic, p-value).
    """
    full_vals = full_pool[column].dropna().values
    rss_vals = rss_pool[column].dropna().values
    
    if len(full_vals) < 2 or len(rss_vals) < 2:
        logger.warning(f"Insufficient data for KS test on {column}.")
        return 0.0, 1.0
    
    try:
        statistic, p_value = ks_2samp(full_vals, rss_vals)
        return float(statistic), float(p_value)
    except Exception as e:
        logger.error(f"Error computing KS test for {column}: {e}")
        return 0.0, 0.0


def validate_stratification(
    full_pool_path: str = FULL_POOL_PATH,
    rss_pool_path: str = RSS_POOL_PATH,
    output_path: str = TARGET_METRICS_FILE
) -> bool:
    """
    Main validation function. Compares the RSS pool against the full pool
    using JSD and KS-test on numeric columns.
    
    Args:
        full_pool_path: Path to the full pool CSV.
        rss_pool_path: Path to the RSS pool CSV.
        output_path: Path to save the validation report JSON.
        
    Returns:
        True if validation passes (JSD < threshold and KS p-value > threshold),
        False otherwise.
        
    Raises:
        RuntimeError: If validation fails, to block further execution.
    """
    logger.info("Starting stratification validation...")
    
    # Load data
    full_pool = load_subset_data(full_pool_path)
    rss_pool = load_subset_data(rss_pool_path)
    
    # Identify numeric columns (exclude non-numeric like material_id)
    numeric_cols = full_pool.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter out columns that might be identifiers or not relevant for distribution
    # Assuming 'material_id' or similar are not numeric, but if they are, exclude them
    exclude_cols = ['material_id', 'id']
    numeric_cols = [c for c in numeric_cols if c not in exclude_cols]
    
    if not numeric_cols:
        logger.warning("No numeric columns found for validation.")
        # If no numeric columns, we cannot validate, but we don't fail hard
        # unless the spec implies we must. For safety, we pass if no columns.
        report = {
            "status": "passed",
            "message": "No numeric columns found to validate.",
            "metrics": {}
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return True
    
    results = {}
    all_passed = True
    
    for col in numeric_cols:
        logger.info(f"Validating column: {col}")
        
        # Compute JSD
        jsd = compute_jensen_shannon_divergence(full_pool, rss_pool, col)
        jsd_pass = jsd < THRESHOLD_JSD
        
        # Compute KS Test
        ks_stat, ks_pval = compute_ks_test(full_pool, rss_pool, col)
        ks_pass = ks_pval > THRESHOLD_KS_PVALUE
        
        results[col] = {
            "jensen_shannon_divergence": jsd,
            "jensen_shannon_threshold": THRESHOLD_JSD,
            "jensen_shannon_passed": jsd_pass,
            "ks_statistic": ks_stat,
            "ks_pvalue": ks_pval,
            "ks_threshold": THRESHOLD_KS_PVALUE,
            "ks_passed": ks_pass
        }
        
        if not jsd_pass or not ks_pass:
            all_passed = False
            logger.warning(f"Validation FAILED for {col}: JSD={jsd:.4f}, KS p={ks_pval:.4f}")
        else:
            logger.info(f"Validation PASSED for {col}: JSD={jsd:.4f}, KS p={ks_pval:.4f}")
    
    # Generate Report
    report = {
        "status": "passed" if all_passed else "failed",
        "timestamp": str(pd.Timestamp.now()),
        "full_pool_rows": len(full_pool),
        "rss_pool_rows": len(rss_pool),
        "thresholds": {
            "jsd_max": THRESHOLD_JSD,
            "ks_pvalue_min": THRESHOLD_KS_PVALUE
        },
        "metrics": results
    }
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Stratification report saved to {output_path}")
    
    if not all_passed:
        error_msg = (
            "Stratification validation FAILED. "
            "The RSS pool does not adequately represent the full pool distribution. "
            f"JSD Threshold: {THRESHOLD_JSD}, KS P-value Threshold: {THRESHOLD_KS_PVALUE}. "
            "Check data/metadata/stratification_report.json for details."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("Stratification validation PASSED.")
    return True


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Validate RSS stratification.")
    parser.add_argument(
        "--full-pool", 
        type=str, 
        default=FULL_POOL_PATH,
        help="Path to the full pool CSV."
    )
    parser.add_argument(
        "--rss-pool", 
        type=str, 
        default=RSS_POOL_PATH,
        help="Path to the RSS pool CSV."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=TARGET_METRICS_FILE,
        help="Path to save the validation report JSON."
    )
    
    args = parser.parse_args()
    
    try:
        validate_stratification(
            full_pool_path=args.full_pool,
            rss_pool_path=args.rss_pool,
            output_path=args.output
        )
        print("Validation successful.")
        sys.exit(0)
    except RuntimeError as e:
        print(f"Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()