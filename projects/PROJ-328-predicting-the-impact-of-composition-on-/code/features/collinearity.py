"""
Collinearity diagnostics for solder alloy descriptors.

This module provides tools to calculate Variance Inflation Factors (VIF)
to detect multicollinearity among predictor variables.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
import yaml
from pathlib import Path

from config import get_vif_threshold, get_data_processed_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

VIF_THRESHOLD = get_vif_threshold()


def calculate_vif(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each numeric column in the dataframe.

    Args:
        df: Input DataFrame containing predictor variables.
        exclude_cols: List of column names to exclude from VIF calculation.

    Returns:
        Dictionary mapping column names to their VIF scores.
    """
    if exclude_cols:
        feature_cols = [c for c in df.columns if c not in exclude_cols]
    else:
        feature_cols = [c for c in df.columns if df[c].dtype in [np.float64, np.float32, np.int64, np.int32]]

    if len(feature_cols) < 2:
        logger.warning("Not enough features to calculate VIF.")
        return {}

    X = df[feature_cols].dropna()
    if X.empty:
        logger.warning("No valid data remaining after dropping NaNs.")
        return {}

    vif_scores = {}
    n_samples = len(X)

    for i, col in enumerate(feature_cols):
        # Regress this feature against all other features
        y = X[col]
        X_other = X.drop(columns=[col])

        # Check for constant variance in y (VIF is undefined if variance is 0)
        if y.std() < 1e-10:
            vif_scores[col] = 0.0
            continue

        # Add intercept
        X_design = np.column_stack([np.ones(n_samples), X_other.values])

        # Solve least squares: (X'X)^-1 X'y
        try:
            # Use pseudo-inverse for stability
            coeffs, residuals, rank, s = np.linalg.lstsq(X_design, y.values, rcond=None)
            
            # Calculate R-squared for this regression
            y_pred = X_design @ coeffs
            ss_res = np.sum((y.values - y_pred) ** 2)
            ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)
            
            if ss_tot < 1e-10:
                r_squared = 0.0
            else:
                r_squared = 1.0 - (ss_res / ss_tot)

            # VIF = 1 / (1 - R^2)
            if r_squared >= 1.0:
                vif_scores[col] = float('inf')
            else:
                vif_scores[col] = 1.0 / (1.0 - r_squared)

        except np.linalg.LinAlgError:
            logger.warning(f"Singularity detected for feature {col}, setting VIF to infinity.")
            vif_scores[col] = float('inf')

    return vif_scores


def get_collinear_features(vif_scores: Dict[str, float], threshold: float = VIF_THRESHOLD) -> List[str]:
    """
    Identify features that exceed the VIF threshold.

    Args:
        vif_scores: Dictionary of VIF scores.
        threshold: VIF threshold above which a feature is considered collinear.

    Returns:
        List of feature names with VIF >= threshold.
    """
    return [col for col, score in vif_scores.items() if score >= threshold]


def remove_collinear_features(
    df: pd.DataFrame, 
    vif_scores: Dict[str, float], 
    threshold: float = VIF_THRESHOLD
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Iteratively remove the feature with the highest VIF until all remaining features are below threshold.

    Args:
        df: Input DataFrame.
        vif_scores: Initial VIF scores.
        threshold: VIF threshold.

    Returns:
        Tuple of (cleaned DataFrame, list of removed feature names).
    """
    removed_features = []
    current_df = df.copy()
    current_vif = vif_scores.copy()

    # Only consider numeric columns for VIF
    numeric_cols = [c for c in current_df.columns if current_df[c].dtype in [np.float64, np.float32, np.int64, np.int32]]
    
    # Filter vif_scores to only numeric cols present
    current_vif = {k: v for k, v in current_vif.items() if k in numeric_cols}

    while True:
        # Find max VIF among current features
        if not current_vif:
            break
        
        max_vif_feature = max(current_vif, key=current_vif.get)
        max_vif = current_vif[max_vif_feature]

        if max_vif < threshold:
            break

        # Remove the feature with highest VIF
        logger.info(f"Removing feature '{max_vif_feature}' with VIF={max_vif:.2f} (threshold={threshold})")
        removed_features.append(max_vif_feature)
        current_df = current_df.drop(columns=[max_vif_feature])

        # Recalculate VIF for remaining features
        if len(current_df.columns) < 2:
            break
        
        # We need to recalculate VIFs for the remaining set
        # For simplicity in this iterative removal, we recalculate all
        new_vif = calculate_vif(current_df)
        current_vif = {k: v for k, v in new_vif.items() if k in current_df.columns}

    return current_df, removed_features


def save_vif_report(
    vif_scores: Dict[str, float],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save VIF analysis results to a YAML report file.

    Args:
        vif_scores: Dictionary of VIF scores.
        output_path: Path to write the report. Defaults to data/processed/vif_report.yaml.

    Returns:
        Path to the written report file.
    """
    if output_path is None:
        output_path = get_data_processed_dir() / "vif_report.yaml"
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "vif_threshold": VIF_THRESHOLD,
        "total_predictors": len(vif_scores),
        "collinear_predictors": [],
        "predictors": []
    }

    for feature, score in sorted(vif_scores.items(), key=lambda x: x[1], reverse=True):
        is_collinear = score >= VIF_THRESHOLD
        entry = {
            "feature_name": feature,
            "vif_score": score if score != float('inf') else "infinity",
            "is_collinear": is_collinear
        }
        report_data["predictors"].append(entry)
        
        if is_collinear:
            report_data["collinear_predictors"].append(feature)

    report_data["summary"] = {
        "max_vif": max(vif_scores.values()) if vif_scores else 0,
        "min_vif": min(vif_scores.values()) if vif_scores else 0,
        "mean_vif": np.mean(list(vif_scores.values())) if vif_scores else 0,
        "collinear_count": len(report_data["collinear_predictors"])
    }

    with open(output_path, 'w') as f:
        yaml.dump(report_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"VIF report saved to {output_path}")
    return output_path


def main():
    """
    Main entry point for running VIF analysis on the cleaned descriptors.
    """
    logger.info("Starting VIF analysis...")
    
    # Load descriptors
    descriptors_path = get_data_processed_dir() / "descriptors.csv"
    if not descriptors_path.exists():
        logger.error(f"Descriptors file not found: {descriptors_path}. Run T023c first.")
        return

    df = pd.read_csv(descriptors_path)
    logger.info(f"Loaded {len(df)} records from {descriptors_path}")

    # Identify numeric descriptor columns (exclude metadata like 'alloy_family' if present)
    # Typically descriptors are numeric columns generated by descriptor_engine
    # We assume columns starting with specific prefixes or all numeric columns except target
    numeric_cols = [c for c in df.columns if df[c].dtype in [np.float64, np.float32, np.int64, np.int32]]
    
    # If there's a target column 'hardness_hv', exclude it
    if 'hardness_hv' in numeric_cols:
        numeric_cols.remove('hardness_hv')
    
    if len(numeric_cols) < 2:
        logger.warning("Not enough numeric descriptor columns to calculate VIF.")
        return

    logger.info(f"Calculating VIF for {len(numeric_cols)} features: {numeric_cols}")
    
    vif_scores = calculate_vif(df[numeric_cols])
    
    if not vif_scores:
        logger.warning("VIF calculation returned no results.")
        return

    # Save report
    report_path = save_vif_report(vif_scores)
    
    # Print summary
    collinear = get_collinear_features(vif_scores)
    if collinear:
        logger.warning(f"Collinear features detected (VIF >= {VIF_THRESHOLD}): {collinear}")
    else:
        logger.info(f"No collinear features detected (threshold={VIF_THRESHOLD}).")
        
    logger.info("VIF analysis complete.")


if __name__ == "__main__":
    main()