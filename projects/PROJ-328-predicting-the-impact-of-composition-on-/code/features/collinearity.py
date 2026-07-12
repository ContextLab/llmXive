"""
Collinearity diagnostics for feature engineering.

This module provides tools for detecting multicollinearity among
engineered features using Variance Inflation Factors (VIF).
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple
from statsmodels.stats.outliers_influence import variance_inflation_factor

logger = logging.getLogger(__name__)


def calculate_vif(
    features: pd.DataFrame, 
    feature_names: Optional[List[str]] = None,
    threshold: float = 5.0
) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factors (VIF) for a set of features.
    
    VIF measures how much the variance of an estimated regression coefficient
    increases because of collinearity. A VIF > 5 indicates significant multicollinearity.
    
    Args:
        features: DataFrame containing the features to analyze.
        feature_names: Optional list of feature names to use. If None, uses DataFrame columns.
        threshold: VIF threshold above which features are flagged as collinear.
    
    Returns:
        Dictionary mapping feature names to their VIF values.
    """
    if feature_names is None:
        feature_names = features.columns.tolist()
    
    logger.info(f"Calculating VIF for {len(feature_names)} features")
    
    # Add intercept column for VIF calculation
    X = features.values
    if X.shape[0] == 0:
        raise ValueError("Cannot calculate VIF for empty feature set")
    
    vif_results = {}
    
    for i, name in enumerate(feature_names):
        # Exclude the current feature when calculating its VIF
        # VIF_i = 1 / (1 - R_i^2) where R_i^2 is from regressing feature_i on all other features
        try:
            vif = variance_inflation_factor(X, i)
            vif_results[name] = float(vif)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for feature {name}: {e}")
            vif_results[name] = float('nan')
    
    # Flag high VIF features
    high_vif = {k: v for k, v in vif_results.items() if v >= threshold}
    if high_vif:
        logger.warning(f"Found {len(high_vif)} features with VIF >= {threshold}: {list(high_vif.keys())}")
    
    return vif_results


def get_collinear_features(
    vif_results: Dict[str, float],
    threshold: float = 5.0
) -> List[str]:
    """
    Get list of features with VIF above the threshold.
    
    Args:
        vif_results: Dictionary of VIF values from calculate_vif().
        threshold: VIF threshold for flagging collinearity.
    
    Returns:
        List of feature names with high VIF.
    """
    return [name for name, vif in vif_results.items() if vif >= threshold]


def remove_collinear_features(
    features: pd.DataFrame,
    vif_results: Dict[str, float],
    threshold: float = 5.0
) -> pd.DataFrame:
    """
    Remove features with VIF above the threshold.
    
    Args:
        features: Original feature DataFrame.
        vif_results: Dictionary of VIF values.
        threshold: VIF threshold for removal.
    
    Returns:
        DataFrame with collinear features removed.
    """
    collinear = get_collinear_features(vif_results, threshold)
    logger.info(f"Removing {len(collinear)} collinear features: {collinear}")
    
    return features.drop(columns=collinear, errors='ignore')
