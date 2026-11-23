import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional
from pathlib import Path

from src.config.logging_config import setup_logger

logger = logging.getLogger(__name__)

def calculate_vif_for_feature(df: pd.DataFrame, feature_name: str, exclude_features: Optional[list] = None) -> float:
    """
    Calculate the Variance Inflation Factor (VIF) for a specific feature.

    VIF = 1 / (1 - R^2)
    where R^2 is the coefficient of determination from regressing the feature
    against all other independent variables.

    Args:
        df: DataFrame containing the features.
        feature_name: The name of the feature to calculate VIF for.
        exclude_features: List of feature names to exclude from the regression (e.g., target variable).

    Returns:
        float: The VIF value for the specified feature.
    """
    if exclude_features is None:
        exclude_features = []

    # Define independent variables: all numeric columns except the target feature and excluded ones
    independent_vars = [col for col in df.select_dtypes(include=[np.number]).columns
                        if col != feature_name and col not in exclude_features]

    if not independent_vars:
        logger.warning(f"No independent variables found for {feature_name}. VIF cannot be calculated.")
        return float('inf')

    try:
        # Run linear regression using OLS to get R^2
        # We use a simple matrix approach: X = independent vars, y = feature_name
        X = df[independent_vars].values
        y = df[feature_name].values

        # Add intercept
        X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])

        # Check for rank deficiency (perfect collinearity)
        if np.linalg.matrix_rank(X_with_intercept) < X_with_intercept.shape[1]:
            logger.warning(f"Perfect collinearity detected in independent variables for {feature_name}.")
            return float('inf')

        # Solve normal equations: (X'X)^-1 X'y
        try:
            coeffs = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
        except np.linalg.LinAlgError:
            logger.warning(f"Singular matrix encountered for {feature_name}. VIF is infinite.")
            return float('inf')

        # Predicted values
        y_pred = X_with_intercept @ coeffs

        # Calculate R^2
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        if ss_tot == 0:
            logger.warning(f"Zero variance in target variable {feature_name}. R^2 undefined.")
            return float('inf')

        r_squared = 1 - (ss_res / ss_tot)

        # Handle edge case where R^2 is very close to 1
        if r_squared >= 1.0:
            logger.warning(f"R^2 is 1.0 for {feature_name}. Perfect fit. VIF is infinite.")
            return float('inf')

        vif = 1.0 / (1.0 - r_squared)
        return vif

    except Exception as e:
        logger.error(f"Error calculating VIF for {feature_name}: {e}")
        raise

def run_vif_diagnostic(data_path: str, threshold: float = 10.0) -> Dict[str, float]:
    """
    Run VIF diagnostic on the generated dataset.

    Args:
        data_path: Path to the parquet file containing the dataset.
        threshold: VIF threshold above which features are considered collinear.

    Returns:
        Dict[str, float]: Dictionary mapping feature names to their VIF values.
    """
    logger.info(f"Loading dataset from {data_path} for VIF diagnostic.")
    try:
        df = pd.read_parquet(data_path)
    except Exception as e:
        logger.error(f"Failed to load dataset from {data_path}: {e}")
        raise

    # Identify feature columns based on the task description
    # Features: gradient_norms, local_curvature
    # Target (to exclude): calculated_kl_divergence
    feature_columns = ['gradient_norms', 'local_curvature']
    target_column = 'calculated_kl_divergence'

    # Validate columns exist
    missing_cols = [col for col in feature_columns + [target_column] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")

    # Calculate VIF for each feature
    vif_results = {}
    for feature in feature_columns:
        vif_val = calculate_vif_for_feature(df, feature, exclude_features=[target_column])
        vif_results[feature] = vif_val
        logger.info(f"VIF for {feature}: {vif_val:.4f}")

        if vif_val > threshold:
            logger.warning(f"High collinearity detected for {feature} (VIF={vif_val:.4f} > {threshold}).")
        else:
            logger.info(f"Collinearity acceptable for {feature} (VIF={vif_val:.4f} <= {threshold}).")

    # Log summary
    logger.info("VIF Diagnostic Summary:")
    for feat, val in vif_results.items():
        status = "HIGH" if val > threshold else "OK"
        logger.info(f"  {feat}: {val:.4f} [{status}]")

    return vif_results

def main():
    """
    Main entry point for running the VIF diagnostic.
    Expects the dataset path from environment or a default.
    """
    import os
    from src.config.env_config import load_config

    config = load_config()
    dataset_path = os.getenv('DATASET_PATH', config.get('DATASET_PATH', 'data/processed/training_sample.parquet'))
    threshold = float(os.getenv('VIF_THRESHOLD', '10.0'))

    setup_logger()
    logger.info("Starting VIF diagnostic check.")

    try:
        results = run_vif_diagnostic(dataset_path, threshold)
        logger.info("VIF diagnostic completed successfully.")
        return results
    except Exception as e:
        logger.error(f"VIF diagnostic failed: {e}")
        raise

if __name__ == "__main__":
    main()