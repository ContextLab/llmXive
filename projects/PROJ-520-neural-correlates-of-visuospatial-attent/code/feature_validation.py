"""
Feature Validation Module for User Story 2.

Implements validation logic for extracted time-frequency features to ensure
physiological plausibility and data integrity before classification.

Addresses Claim: c_c24bc9cf (Feature Validation)
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

from config import get_paths, get_seed
from logging_config import get_pipeline_logger, log_stage_start, log_stage_end, log_warning_count

# Constants for physiological plausibility checks
# Alpha power (8-13 Hz) typical range in dB: -20 to 40 dB
# Beta power (13-30 Hz) typical range in dB: -20 to 30 dB
# These are broad ranges to accommodate individual variability
PHYSIOLOGICAL_BOUNDS = {
    'alpha': {'min': -30.0, 'max': 50.0},
    'beta': {'min': -30.0, 'max': 50.0},
}

# Threshold for NaN/Inf ratio before failing validation
MAX_INVALID_RATIO = 0.05  # 5%

logger = get_pipeline_logger(__name__)

def load_features(file_path: str) -> pd.DataFrame:
    """
    Load the features matrix from CSV.

    Args:
        file_path: Path to the features CSV file.

    Returns:
        DataFrame containing the feature matrix.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Features file not found: {file_path}")

    logger.info(f"Loading features from {file_path}")
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError("Features file is empty.")
    
    logger.info(f"Loaded features with shape: {df.shape}")
    return df

def check_nan_inf_ratio(df: pd.DataFrame, threshold: float = MAX_INVALID_RATIO) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if the ratio of NaN or Inf values exceeds the threshold.

    Args:
        df: DataFrame to check.
        threshold: Maximum allowed ratio of invalid values.

    Returns:
        Tuple of (is_valid, details_dict)
    """
    total_cells = df.size
    if total_cells == 0:
        return True, {"message": "Empty dataframe"}

    # Check for NaN and Inf
    nan_count = df.isna().sum().sum()
    inf_count = np.isinf(df.select_dtypes(include=[np.number])).sum().sum()
    invalid_count = nan_count + inf_count
    invalid_ratio = invalid_count / total_cells

    details = {
        "total_cells": total_cells,
        "nan_count": int(nan_count),
        "inf_count": int(inf_count),
        "invalid_count": int(invalid_count),
        "invalid_ratio": float(invalid_ratio),
        "threshold": threshold,
        "valid": invalid_ratio <= threshold
    }

    if invalid_ratio > threshold:
        logger.error(f"Invalid value ratio ({invalid_ratio:.4f}) exceeds threshold ({threshold})")
        return False, details
    
    logger.info(f"NaN/Inf check passed: {invalid_ratio:.4f} <= {threshold}")
    return True, details

def check_physiological_bounds(df: pd.DataFrame, bounds: Dict[str, Dict[str, float]]) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if feature values fall within physiologically plausible ranges.
    
    This function assumes the DataFrame columns are named with the band name
    (e.g., 'alpha_power_Pz', 'beta_power_F3') or contains a 'band' indicator.
    It attempts to infer bands from column names or validates all numeric columns
    against a generic range if specific band mapping isn't explicit in column names.
    
    For this implementation, we assume columns contain 'alpha' or 'beta' in their name
    to determine which bounds to apply.

    Args:
        df: DataFrame with feature values.
        bounds: Dictionary mapping band names to min/max bounds.

    Returns:
        Tuple of (is_valid, details_dict)
    """
    issues = []
    valid = True

    for col in df.select_dtypes(include=[np.number]).columns:
        col_lower = col.lower()
        band = None
        
        if 'alpha' in col_lower:
            band = 'alpha'
        elif 'beta' in col_lower:
            band = 'beta'
        
        if band and band in bounds:
            min_val = bounds[band]['min']
            max_val = bounds[band]['max']
            
            # Check for out of bounds values (excluding NaN/Inf which are handled elsewhere)
            numeric_series = df[col].dropna()
            numeric_series = numeric_series[~np.isinf(numeric_series)]
            
            out_of_bounds = (numeric_series < min_val) | (numeric_series > max_val)
            count = out_of_bounds.sum()
            
            if count > 0:
                ratio = count / len(numeric_series)
                issues.append({
                    "column": col,
                    "band": band,
                    "out_of_bounds_count": int(count),
                    "total_valid_values": int(len(numeric_series)),
                    "ratio": float(ratio),
                    "min_bound": min_val,
                    "max_bound": max_val,
                    "sample_out_of_bounds": numeric_series[out_of_bounds].head(3).tolist()
                })
                valid = False
                logger.warning(f"Column '{col}' has {count} values out of physiological bounds for {band} band.")

    details = {
        "valid": valid,
        "issues": issues,
        "checked_columns": len(df.select_dtypes(include=[np.number]).columns)
    }

    if not valid:
        logger.warning(f"Physiological bounds check failed for {len(issues)} columns.")
    else:
        logger.info("Physiological bounds check passed for all columns.")

    return valid, details

def validate_features(
    file_path: str,
    output_log_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main validation function. Runs all checks and logs failures.

    Args:
        file_path: Path to the features CSV.
        output_log_path: Optional path to write detailed validation report.

    Returns:
        Dictionary containing validation results.
    """
    log_stage_start(logger, "Feature Validation")
    results = {
        "file_path": file_path,
        "overall_valid": True,
        "checks": {}
    }

    try:
        # Load data
        df = load_features(file_path)
        results["shape"] = list(df.shape)
        results["columns"] = list(df.columns)

        # Check 1: NaN/Inf ratio
        nan_valid, nan_details = check_nan_inf_ratio(df)
        results["checks"]["nan_inf_ratio"] = nan_details
        if not nan_valid:
            results["overall_valid"] = False

        # Check 2: Physiological bounds
        bound_valid, bound_details = check_physiological_bounds(df, PHYSIOLOGICAL_BOUNDS)
        results["checks"]["physiological_bounds"] = bound_details
        if not bound_valid:
            results["overall_valid"] = False

        # Check 3: Dimensionality consistency (rows should match epochs)
        # This is a structural check; we expect at least some rows
        if df.shape[0] == 0:
            results["overall_valid"] = False
            results["checks"]["dimensionality"] = {"valid": False, "reason": "No rows in features"}
        else:
            results["checks"]["dimensionality"] = {"valid": True, "rows": df.shape[0]}

        # Log failures
        if not results["overall_valid"]:
            failure_reasons = []
            if not nan_details.get("valid", True):
                failure_reasons.append(f"NaN/Inf ratio too high: {nan_details['invalid_ratio']:.4f}")
            if not bound_details.get("valid", True):
                failure_reasons.append(f"Physiological bounds violations in {len(bound_details['issues'])} columns")
            
            logger.error(f"Feature validation FAILED: {'; '.join(failure_reasons)}")
            results["failure_reasons"] = failure_reasons
        else:
            logger.info("Feature validation PASSED.")

        # Write detailed log if path provided
        if output_log_path:
            os.makedirs(os.path.dirname(output_log_path), exist_ok=True)
            with open(output_log_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Validation report written to {output_log_path}")

    except Exception as e:
        logger.exception(f"Validation process failed with error: {e}")
        results["overall_valid"] = False
        results["error"] = str(e)

    log_stage_end(logger, "Feature Validation")
    return results

def main():
    """Entry point for running feature validation."""
    paths = get_paths()
    features_file = paths.get("processed_features", str(paths["processed"] / "features_matrix.csv"))
    log_file = paths.get("processed_features_log", str(paths["processed"] / "feature_validation_report.json"))

    logger.info(f"Starting feature validation for {features_file}")
    
    results = validate_features(features_file, output_log_path=log_file)
    
    if not results["overall_valid"]:
        logger.critical("Feature validation failed. The pipeline should halt or flag results.")
        # In a strict pipeline, we might exit with error code here
        # sys.exit(1) 
    else:
        logger.info("Feature validation successful.")

    return results

if __name__ == "__main__":
    main()
