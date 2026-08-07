"""
Collinearity detection and Variance Inflation Factor (VIF) calculation.

Provides tools for detecting multicollinearity in feature sets
and removing highly correlated features.
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from utils.logging_config import get_logger
from config import get_vif_threshold

logger = get_logger(__name__)


def calculate_vif(X: pd.DataFrame, threshold: Optional[float] = None) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.

    VIF measures how much the variance of an estimated regression coefficient
    increases if your predictors are correlated.

    Args:
        X: DataFrame with features (no target variable)
        threshold: Optional threshold for flagging high VIF. If None, uses config.

    Returns:
        Dictionary mapping feature names to their VIF scores
    """
    if threshold is None:
        threshold = get_vif_threshold()

    logger.debug(f"Calculating VIF with threshold={threshold}")

    # Handle constant columns
    for col in X.columns:
        if X[col].std() == 0:
            logger.warning(f"Column {col} has zero variance, removing from VIF calculation")

    # Filter out constant columns
    X_clean = X.loc[:, X.std() > 0]

    if X_clean.empty:
        logger.warning("All columns have zero variance")
        return {}

    vif_scores = {}
    for i, col in enumerate(X_clean.columns):
        try:
            # Calculate VIF for this column
            vif = variance_inflation_factor(X_clean.values, i)
            vif_scores[col] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_scores[col] = np.inf

    # Log results
    high_vif_features = [k for k, v in vif_scores.items() if v >= threshold]
    if high_vif_features:
        logger.warning(f"Found {len(high_vif_features)} features with VIF >= {threshold}: {high_vif_features}")

    return vif_scores


def get_collinear_features(vif_scores: Dict[str, float], threshold: Optional[float] = None) -> List[str]:
    """
    Get list of features with VIF above threshold.

    Args:
        vif_scores: Dictionary of VIF scores from calculate_vif
        threshold: Optional threshold. If None, uses config.

    Returns:
        List of feature names with VIF >= threshold
    """
    if threshold is None:
        threshold = get_vif_threshold()

    collinear = [k for k, v in vif_scores.items() if v >= threshold]
    logger.info(f"Found {len(collinear)} collinear features with VIF >= {threshold}")
    return collinear


def remove_collinear_features(
    X: pd.DataFrame,
    threshold: Optional[float] = None,
    verbose: bool = True
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Remove features with VIF above threshold.

    Iteratively removes the feature with the highest VIF until
    all remaining features are below the threshold.

    Args:
        X: DataFrame with features
        threshold: Optional threshold. If None, uses config.
        verbose: Whether to log removal steps

    Returns:
        Tuple of (cleaned DataFrame, list of removed feature names)
    """
    if threshold is None:
        threshold = get_vif_threshold()

    X_clean = X.copy()
    removed_features = []

    while True:
        vif_scores = calculate_vif(X_clean, threshold)
        if not vif_scores:
            break

        max_vif_feature = max(vif_scores, key=vif_scores.get)
        max_vif = vif_scores[max_vif_feature]

        if max_vif < threshold:
            break

        if verbose:
            logger.info(f"Removing {max_vif_feature} (VIF={max_vif:.2f})")

        X_clean = X_clean.drop(columns=[max_vif_feature])
        removed_features.append(max_vif_feature)

        # Safety check: don't remove all features
        if X_clean.empty:
            logger.error("Removed all features, stopping")
            break

    if verbose:
        logger.info(f"Removed {len(removed_features)} collinear features: {removed_features}")

    return X_clean, removed_features


def main():
    """
    Main function for testing collinearity detection.
    """
    from seed import init_reproducibility
    init_reproducibility()

    logger.info("Testing collinearity detection")

    # Create sample data with some collinearity
    np.random.seed(42)
    n_samples = 100

    # Independent features
    X1 = np.random.normal(0, 1, n_samples)
    X2 = np.random.normal(0, 1, n_samples)

    # Collinear features
    X3 = X1 * 2 + np.random.normal(0, 0.1, n_samples)  # Highly correlated with X1
    X4 = X2 * 1.5 + np.random.normal(0, 0.1, n_samples)  # Highly correlated with X2
    X5 = np.random.normal(0, 1, n_samples)  # Independent

    df = pd.DataFrame({
        'X1': X1,
        'X2': X2,
        'X3': X3,
        'X4': X4,
        'X5': X5,
    })

    # Calculate VIF
    vif_scores = calculate_vif(df)
    logger.info(f"VIF scores: {vif_scores}")

    # Identify collinear features
    threshold = get_vif_threshold()
    collinear = get_collinear_features(vif_scores, threshold)
    logger.info(f"Collinear features (VIF >= {threshold}): {collinear}")

    # Remove collinear features
    df_clean, removed = remove_collinear_features(df, threshold)
    logger.info(f"Removed features: {removed}")
    logger.info(f"Remaining features: {list(df_clean.columns)}")

    # Verify remaining features are below threshold
    vif_clean = calculate_vif(df_clean)
    logger.info(f"VIF after cleaning: {vif_clean}")

    all_below = all(v < threshold for v in vif_clean.values())
    if all_below:
        logger.info("✓ All remaining features have VIF < threshold")
    else:
        logger.warning("✗ Some features still have high VIF")

if __name__ == "__main__":
    main()