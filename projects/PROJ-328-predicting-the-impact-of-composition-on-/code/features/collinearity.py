"""
Collinearity analysis utilities for feature engineering.
Calculates Variance Inflation Factor (VIF) to detect multicollinearity.
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from utils.logging_config import get_logger

logger = get_logger(__name__)

def calculate_vif(df: pd.DataFrame, features: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for features in a dataframe.

    Args:
        df: DataFrame containing the features.
        features: List of column names to calculate VIF for. If None, uses all numeric columns.

    Returns:
        DataFrame with feature names and their VIF values.
    """
    if features is None:
        features = df.select_dtypes(include=[np.number]).columns.tolist()

    if len(features) == 0:
        logger.warning("No numeric features found for VIF calculation")
        return pd.DataFrame(columns=['feature', 'vif'])

    X = df[features].values

    # Add constant for intercept
    X_with_const = sm.add_constant(X)

    vif_data = []
    for i, feature in enumerate(features):
        try:
            vif = variance_inflation_factor(X_with_const, i + 1)  # +1 because of constant
            vif_data.append({'feature': feature, 'vif': vif})
        except Exception as e:
            logger.error(f"Error calculating VIF for {feature}: {e}")
            vif_data.append({'feature': feature, 'vif': np.nan})

    return pd.DataFrame(vif_data)

def get_collinear_features(vif_df: pd.DataFrame, threshold: float = 5.0) -> List[str]:
    """
    Identify features with VIF above a threshold.

    Args:
        vif_df: DataFrame from calculate_vif with 'feature' and 'vif' columns.
        threshold: VIF threshold above which features are considered collinear.

    Returns:
        List of feature names with VIF >= threshold.
    """
    if vif_df.empty:
        return []

    collinear = vif_df[vif_df['vif'] >= threshold]['feature'].tolist()
    logger.info(f"Found {len(collinear)} collinear features (VIF >= {threshold}): {collinear}")
    return collinear

def remove_collinear_features(df: pd.DataFrame, vif_df: pd.DataFrame, threshold: float = 5.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Remove collinear features from a dataframe based on VIF analysis.

    Args:
        df: Original DataFrame.
        vif_df: VIF analysis results.
        threshold: VIF threshold.

    Returns:
        Tuple of (cleaned DataFrame, list of removed feature names).
    """
    collinear = get_collinear_features(vif_df, threshold)
    removed_features = []

    if collinear:
        # Remove collinear features
        cleaned_df = df.drop(columns=collinear, errors='ignore')
        removed_features = collinear
        logger.info(f"Removed {len(removed_features)} collinear features: {removed_features}")
    else:
        cleaned_df = df.copy()

    return cleaned_df, removed_features

def save_vif_report(vif_df: pd.DataFrame, output_path: str):
    """
    Save VIF analysis results to a file.

    Args:
        vif_df: VIF analysis DataFrame.
        output_path: Path to save the report (CSV or JSON).
    """
    if vif_df.empty:
        logger.warning("Empty VIF dataframe, skipping save")
        return

    try:
        vif_df.to_csv(output_path, index=False)
        logger.info(f"VIF report saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save VIF report: {e}")
        raise

def main():
    """
    Main entry point for testing collinearity analysis.
    """
    logger.info("Starting collinearity analysis test")

    # Create sample data with some collinearity
    np.random.seed(42)
    n_samples = 100

    # Create features with known relationships
    data = {
        'feature_a': np.random.randn(n_samples),
        'feature_b': np.random.randn(n_samples),
        'feature_c': np.random.randn(n_samples),
        'feature_d': np.random.randn(n_samples)
    }

    # Add strong collinearity between feature_a and feature_b
    data['feature_b'] = data['feature_a'] * 2 + np.random.randn(n_samples) * 0.1

    df = pd.DataFrame(data)

    # Calculate VIF
    vif_df = calculate_vif(df)
    logger.info("VIF Analysis Results:")
    logger.info(vif_df.to_string())

    # Identify collinear features
    collinear = get_collinear_features(vif_df, threshold=5.0)
    logger.info(f"Collinear features (VIF >= 5.0): {collinear}")

    # Remove collinear features
    cleaned_df, removed = remove_collinear_features(df, vif_df, threshold=5.0)
    logger.info(f"Removed features: {removed}")
    logger.info(f"Remaining features: {list(cleaned_df.columns)}")

    logger.info("Collinearity analysis test completed successfully")

if __name__ == "__main__":
    main()