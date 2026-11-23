"""
Norms utility module for loading and validating MFQ distributions against
Gervais et al. psychometric norms.
"""
from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import yaml
import pandas as pd
import numpy as np
from scipy import stats

# Import config for paths
from code.config import get_path

# Configure logger for this module
logger = logging.getLogger(__name__)

# Constants
NORMS_CONFIG_PATH = "data/config/gervais_norms.yaml"
LOG_FILE_PATH = "data/logs/norm_validation.log"

def load_norms() -> Dict[str, Dict[str, float]]:
    """
    Load Gervais et al. psychometric norms from the YAML configuration file.

    Returns:
        Dict[str, Dict[str, float]]: Dictionary with foundation names as keys
            and nested dicts containing 'mean' and 'std' values.
    """
    config_path = get_path(NORMS_CONFIG_PATH)
    if not config_path.exists():
        raise FileNotFoundError(f"Norms configuration not found at {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        norms = yaml.safe_load(f)

    logger.info(f"Loaded norms from {config_path}")
    return norms

def get_correlation_matrix() -> np.ndarray:
    """
    Returns a placeholder correlation matrix for MFQ dimensions.
    In a real implementation, this would be derived from literature or data.
    """
    # 5 foundations: Care, Fairness, Loyalty, Authority, Purity
    # Placeholder: Identity matrix (uncorrelated) or a simple structure
    # Based on typical moral foundations theory, some positive correlations exist.
    # Using a simple symmetric matrix with 0.5 off-diagonals as a placeholder.
    n = 5
    corr = np.ones((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            corr[i, j] = 0.3
            corr[j, i] = 0.3
    return corr

def validate_mfq_distribution(
    mfq_data: pd.DataFrame,
    norms: Optional[Dict[str, Dict[str, float]]] = None,
    tolerance_sd: float = 1.0
) -> Dict[str, Any]:
    """
    Validate that the synthetic MFQ distribution matches the published norms
    within a specified tolerance (default: 1 SD).

    This function performs two checks:
    1. Kolmogorov-Smirnov (KS) test against the theoretical distribution defined
       by the norms (p > 0.05 indicates no significant difference).
    2. Mean comparison: checks if the sample mean is within `tolerance_sd` * std
       of the population mean.

    Args:
        mfq_data: DataFrame containing MFQ scores with columns for each foundation
            (e.g., 'care', 'fairness', 'loyalty', 'authority', 'purity').
        norms: Dictionary of norms. If None, loads from config.
        tolerance_sd: Number of standard deviations allowed for mean difference.

    Returns:
        Dict[str, Any]: Validation report containing:
            - 'status': 'PASS' or 'FAIL'
            - 'details': List of per-foundation results (KS p-value, mean diff, pass/fail)
            - 'log_path': Path to the written log file.
    """
    if norms is None:
        norms = load_norms()

    foundations = ['care', 'fairness', 'loyalty', 'authority', 'purity']
    report_details = []
    all_passed = True

    # Ensure output directory exists
    log_path = get_path(LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare log content
    log_entries = []
    log_entries.append(f"Validation started at {pd.Timestamp.now().isoformat()}")
    log_entries.append(f"Input data shape: {mfq_data.shape}")
    log_entries.append(f"Foundations checked: {foundations}")
    log_entries.append("-" * 50)

    for foundation in foundations:
        # Map to norm keys (case sensitivity check)
        # Norms file uses Title Case, data usually lowercase
        norm_key = foundation.capitalize()
        if norm_key not in norms:
            error_msg = f"Norm not found for {norm_key}"
            log_entries.append(f"[ERROR] {error_msg}")
            report_details.append({
                "foundation": foundation,
                "status": "FAIL",
                "error": error_msg
            })
            all_passed = False
            continue

        target_mean = norms[norm_key]['mean']
        target_std = norms[norm_key]['std']

        if foundation not in mfq_data.columns:
            error_msg = f"Column {foundation} not found in data"
            log_entries.append(f"[ERROR] {error_msg}")
            report_details.append({
                "foundation": foundation,
                "status": "FAIL",
                "error": error_msg
            })
            all_passed = False
            continue

        sample_data = mfq_data[foundation].dropna()
        if len(sample_data) == 0:
            error_msg = f"No data for {foundation}"
            log_entries.append(f"[ERROR] {error_msg}")
            report_details.append({
                "foundation": foundation,
                "status": "FAIL",
                "error": error_msg
            })
            all_passed = False
            continue

        # 1. Kolmogorov-Smirnov Test
        # Compare sample against normal distribution defined by norms
        ks_stat, p_value = stats.kstest(
            sample_data,
            'norm',
            args=(target_mean, target_std)
        )
        ks_pass = p_value > 0.05

        # 2. Mean Comparison
        sample_mean = sample_data.mean()
        mean_diff = abs(sample_mean - target_mean)
        mean_pass = mean_diff <= (tolerance_sd * target_std)

        foundation_pass = ks_pass and mean_pass
        status = "PASS" if foundation_pass else "FAIL"

        if not foundation_pass:
            all_passed = False

        detail = {
            "foundation": foundation,
            "status": status,
            "ks_statistic": float(ks_stat),
            "ks_p_value": float(p_value),
            "ks_pass": ks_pass,
            "sample_mean": float(sample_mean),
            "target_mean": target_mean,
            "mean_diff": float(mean_diff),
            "tolerance_limit": float(tolerance_sd * target_std),
            "mean_pass": mean_pass
        }
        report_details.append(detail)

        log_entries.append(f"Foundation: {foundation}")
        log_entries.append(f"  KS Test: p={p_value:.4f} ({'PASS' if ks_pass else 'FAIL'})")
        log_entries.append(f"  Mean Check: diff={mean_diff:.4f} <= {tolerance_sd * target_std:.4f} ({'PASS' if mean_pass else 'FAIL'})")
        log_entries.append(f"  Overall: {status}")
        log_entries.append("-" * 50)

    final_status = "PASS" if all_passed else "FAIL"
    log_entries.append(f"FINAL STATUS: {final_status}")

    # Write log file
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(log_entries))

    logger.info(f"Validation report written to {log_path}")

    return {
        "status": final_status,
        "details": report_details,
        "log_path": str(log_path)
    }

def run_norm_validation_pipeline(
    mfq_data: pd.DataFrame,
    tolerance_sd: float = 1.0
) -> Dict[str, Any]:
    """
    Wrapper to run the full validation pipeline.
    """
    logger.info("Starting MFQ Norm Validation Pipeline")
    result = validate_mfq_distribution(mfq_data, tolerance_sd=tolerance_sd)
    logger.info(f"Pipeline completed with status: {result['status']}")
    return result

# For backward compatibility if needed
def get_norms() -> Dict[str, Dict[str, float]]:
    return load_norms()