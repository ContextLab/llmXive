"""
Variance Inflation Factor (VIF) checker for training features.

Calculates VIF for gradient norms and local curvature to detect
multicollinearity before model training. Results are logged to
logs/pipeline.log as required by the Assumption validation step.
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, float
from pathlib import Path

# Import the logging configuration helper to ensure we log to the correct file
from src.config.logging_config import setup_logger

# Threshold for high collinearity
VIF_THRESHOLD = 10.0

def calculate_vif_for_feature(df: pd.DataFrame, feature_name: str) -> float:
    """
    Calculate the Variance Inflation Factor (VIF) for a specific feature.

    VIF = 1 / (1 - R^2)
    where R^2 is the coefficient of determination when regressing the
    feature against all other features.

    Args:
        df: DataFrame containing the feature and other predictors.
        feature_name: The name of the feature to calculate VIF for.

    Returns:
        float: The VIF value.
    """
    # Ensure we have a copy to avoid SettingWithCopyWarning
    features = df.copy()

    # Drop rows with NaN or Inf in any relevant column
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.dropna(subset=[feature_name] + [c for c in features.columns if c != feature_name])

    if len(features) < 2:
        logging.warning(f"Not enough data points to calculate VIF for {feature_name}.")
        return float('nan')

    # Prepare X (all other features) and y (target feature)
    y = features[feature_name]
    X = features.drop(columns=[feature_name])

    # If no other features exist, VIF is undefined (or 1.0 by convention if no collinearity possible)
    if X.shape[1] == 0:
        return 1.0

    # Simple linear regression to get R^2
    # Using numpy for speed and to avoid heavy sklearn dependency if not strictly needed for this small calculation
    # X with intercept
    X_intercept = np.column_stack([np.ones(X.shape[0]), X.values])

    try:
        # Solve least squares: (X^T X)^-1 X^T y
        coeffs, residuals, rank, s = np.linalg.lstsq(X_intercept, y.values, rcond=None)

        # Calculate predicted values
        y_pred = X_intercept @ coeffs

        # Calculate R^2
        ss_res = np.sum((y.values - y_pred) ** 2)
        ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)

        if ss_tot == 0:
            # No variance in y, R^2 is undefined, VIF is undefined
            return float('nan')

        r_squared = 1 - (ss_res / ss_tot)

        # Prevent division by zero if R^2 is exactly 1 (perfect collinearity)
        if r_squared >= 1.0:
            return float('inf')

        vif = 1 / (1 - r_squared)
        return vif

    except np.linalg.LinAlgError:
        logging.error(f"Singular matrix encountered while calculating VIF for {feature_name}.")
        return float('inf')

def run_vif_diagnostic(data_path: str, output_log_path: str = None) -> Dict[str, float]:
    """
    Load the generated dataset, calculate VIF for gradient norms and curvature,
    and log the results.

    Args:
        data_path: Path to the training_sample.parquet file.
        output_log_path: Optional path to a specific log file. Defaults to logs/pipeline.log.

    Returns:
        Dict mapping feature names to their VIF values.
    """
    # Ensure logger is configured
    logger = setup_logger(output_log_path or "logs/pipeline.log")
    logger.info(f"Starting VIF diagnostic on {data_path}")

    # Load data
    try:
        df = pd.read_parquet(data_path)
    except FileNotFoundError:
        logger.error(f"Data file not found: {data_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load data from {data_path}: {e}")
        raise

    # Identify features of interest
    # Based on T015: columns include 'gradient_norms', 'local_curvature'
    target_features = ['gradient_norms', 'local_curvature']
    available_features = [f for f in target_features if f in df.columns]

    if not available_features:
        logger.warning(f"None of the expected features {target_features} found in {data_path}. Columns found: {df.columns.tolist()}")
        return {}

    # Also include other numerical columns as potential predictors if they exist
    # to get a true VIF (regressing against ALL other features)
    # But for the specific check of "gradient_norms vs curvature", we focus on these two.
    # If we want to check if 'gradient_norms' is collinear with 'local_curvature',
    # we regress 'gradient_norms' on 'local_curvature' and vice versa.

    results = {}

    for feature in available_features:
        vif = calculate_vif_for_feature(df, feature)
        results[feature] = vif

        status = "HIGH" if vif > VIF_THRESHOLD else "OK"
        logger.warning(f"VIF for '{feature}': {vif:.4f} ({status})") if vif > VIF_THRESHOLD else logger.info(f"VIF for '{feature}': {vif:.4f} ({status})")

    return results

def main():
    """
    CLI entry point for running the VIF diagnostic.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Calculate VIF for training features.")
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/processed/training_sample.parquet",
        help="Path to the training_sample.parquet file."
    )
    parser.add_argument(
        "--log-path",
        type=str,
        default="logs/pipeline.log",
        help="Path to the log file."
    )

    args = parser.parse_args()

    try:
        results = run_vif_diagnostic(args.data_path, args.log_path)
        if not results:
            print("No VIF results calculated. Check logs for errors.")
            sys.exit(1)
        
        print(f"\nVIF Diagnostic Results:")
        for feat, val in results.items():
            status = "HIGH COLLINEARITY" if val > VIF_THRESHOLD else "OK"
            print(f"  {feat}: {val:.4f} ({status})")
        
        # Check for high collinearity
        high_vif = [k for k, v in results.items() if v > VIF_THRESHOLD]
        if high_vif:
            print(f"\nWARNING: High collinearity detected for: {high_vif}")
            sys.exit(0) # Exit 0 but warn, as per task requirement to log warning not error
        else:
            print("\nNo high collinearity detected.")
            sys.exit(0)

    except Exception as e:
        print(f"Error running VIF diagnostic: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()