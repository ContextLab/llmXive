"""
Stratification Validation Module (T033).

Implements statistical validation for sparsity subsets using:
1. Jensen-Shannon Divergence (threshold < 0.05)
2. Kolmogorov-Smirnov Test (p-value > 0.05)

Blocks training if thresholds are exceeded.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import jensenshannon

# Project imports
from utils.logging import get_logger
from utils.data_models import SparsitySubset

logger = get_logger(__name__)

# Constants
JS_THRESHOLD = 0.05
KS_PVALUE_THRESHOLD = 0.05

def load_subset_data(subset_path: str) -> pd.DataFrame:
    """Load a subset CSV file."""
    if not os.path.exists(subset_path):
        raise FileNotFoundError(f"Subset file not found: {subset_path}")
    
    df = pd.read_csv(subset_path)
    required_cols = ['formation_energy']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns in {subset_path}. Expected: {required_cols}")
    
    # Drop rows with NaN formation_energy
    df = df.dropna(subset=['formation_energy'])
    logger.info(f"Loaded {len(df)} rows from {subset_path}")
    return df

def compute_jensen_shannon_divergence(
    dist1: np.ndarray, 
    dist2: np.ndarray, 
    bins: int = 50
) -> float:
    """
    Compute Jensen-Shannon Divergence between two distributions.
    
    Args:
        dist1: First distribution (1D array)
        dist2: Second distribution (1D array)
        bins: Number of bins for histogram
      
    Returns:
        JS divergence value (0 = identical, 1 = maximally different)
    """
    if len(dist1) == 0 or len(dist2) == 0:
        raise ValueError("Cannot compute JS divergence on empty distributions")

    # Create histograms with shared range
    min_val = min(dist1.min(), dist2.min())
    max_val = max(dist1.max(), dist2.max())
    
    if min_val == max_val:
        # Degenerate case: all values are the same
        return 0.0

    hist1, _ = np.histogram(dist1, bins=bins, range=(min_val, max_val), density=True)
    hist2, _ = np.histogram(dist2, bins=bins, range=(min_val, max_val), density=True)

    # Normalize to ensure valid probability distributions
    hist1 = hist1 / (hist1.sum() + 1e-10)
    hist2 = hist2 / (hist2.sum() + 1e-10)

    # Compute JS divergence
    js_div = jensenshannon(hist1, hist2, base=2)
    return float(js_div)

def compute_ks_test(
    dist1: np.ndarray, 
    dist2: np.ndarray
) -> Tuple[float, float]:
    """
    Compute Kolmogorov-Smirnov test between two distributions.
    
    Args:
        dist1: First distribution
        dist2: Second distribution
    
    Returns:
        Tuple of (KS statistic, p-value)
    """
    if len(dist1) == 0 or len(dist2) == 0:
        raise ValueError("Cannot compute KS test on empty distributions")
    
    statistic, p_value = stats.ks_2samp(dist1, dist2)
    return float(statistic), float(p_value)

def validate_stratification(
    subset_path: str, 
    reference_path: str,
    output_log_path: str = "data/results/stratification_validation.json"
) -> bool:
    """
    Validate stratification of a subset against a reference pool.
    
    Criteria:
    1. Jensen-Shannon Divergence < 0.05
    2. KS-test p-value > 0.05
    
    Args:
        subset_path: Path to the subset CSV
        reference_path: Path to the reference (RSS) pool CSV
        output_log_path: Path to write validation results JSON
    
    Returns:
        True if validation passes, False otherwise.
    
    Raises:
        ValueError: If validation fails (thresholds exceeded)
    """
    logger.info(f"Validating stratification: {subset_path} vs {reference_path}")
    
    # Load data
    subset_df = load_subset_data(subset_path)
    reference_df = load_subset_data(reference_path)
    
    subset_energy = subset_df['formation_energy'].values
    reference_energy = reference_df['formation_energy'].values
    
    # 1. Jensen-Shannon Divergence
    try:
        js_div = compute_jensen_shannon_divergence(subset_energy, reference_energy)
        js_pass = js_div < JS_THRESHOLD
        logger.info(f"JS Divergence: {js_div:.4f} (Threshold: {JS_THRESHOLD}, Pass: {js_pass})")
    except Exception as e:
        logger.error(f"JS Divergence calculation failed: {e}")
        raise
    
    # 2. Kolmogorov-Smirnov Test
    try:
        ks_stat, ks_pval = compute_ks_test(subset_energy, reference_energy)
        ks_pass = ks_pval > KS_PVALUE_THRESHOLD
        logger.info(f"KS Statistic: {ks_stat:.4f}, p-value: {ks_pval:.4f} (Threshold: {KS_PVALUE_THRESHOLD}, Pass: {ks_pass})")
    except Exception as e:
        logger.error(f"KS test calculation failed: {e}")
        raise
    
    # Compile results
    validation_result = {
        "subset_path": subset_path,
        "reference_path": reference_path,
        "js_divergence": js_div,
        "js_threshold": JS_THRESHOLD,
        "js_passed": js_pass,
        "ks_statistic": ks_stat,
        "ks_p_value": ks_pval,
        "ks_threshold": KS_PVALUE_THRESHOLD,
        "ks_passed": ks_pass,
        "overall_passed": js_pass and ks_pass,
        "sample_sizes": {
            "subset": len(subset_energy),
            "reference": len(reference_energy)
        }
    }
    
    # Ensure output directory exists
    output_path = Path(output_log_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results to JSON
    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)
    logger.info(f"Validation results written to {output_log_path}")
    
    # Block training if thresholds exceeded
    if not validation_result["overall_passed"]:
        error_msg = (
            f"Stratification validation FAILED for {subset_path}.\n"
            f"JS Divergence: {js_div:.4f} >= {JS_THRESHOLD} (FAIL)\n"
            f"KS p-value: {ks_pval:.4f} <= {KS_PVALUE_THRESHOLD} (FAIL)\n"
            "Training blocked."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Stratification validation PASSED for {subset_path}")
    return True

def main():
    """CLI entry point for stratification validation."""
    parser = argparse.ArgumentParser(description="Validate stratification of sparsity subsets.")
    parser.add_argument(
        "--subset", 
        type=str, 
        required=True, 
        help="Path to the subset CSV file to validate"
    )
    parser.add_argument(
        "--reference", 
        type=str, 
        required=True, 
        help="Path to the reference (RSS) pool CSV file"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/results/stratification_validation.json",
        help="Path to output validation JSON"
    )
    
    args = parser.parse_args()
    
    try:
        validate_stratification(args.subset, args.reference, args.output)
        print("SUCCESS: Stratification validation passed.")
        sys.exit(0)
    except ValueError as e:
        print(f"FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()