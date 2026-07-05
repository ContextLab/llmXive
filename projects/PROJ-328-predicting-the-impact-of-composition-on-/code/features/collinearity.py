"""
Collinearity diagnostics module.
Calculates Variance Inflation Factor (VIF) to detect multicollinearity in features.
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple
from statsmodels.stats.outliers_influence import variance_inflation_factor

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, threshold: float = 5.0) -> Tuple[Dict[str, float], List[str]]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature in the dataframe.
    
    Args:
        df: DataFrame of features (numeric only).
        threshold: Threshold above which a feature is considered to have high collinearity.
    
    Returns:
        Tuple of:
            - vif_scores: Dictionary mapping feature name to VIF score.
            - high_vif_features: List of feature names with VIF >= threshold.
    """
    if df.empty:
        return {}, []
    
    # Ensure only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        logger.warning("No numeric features found for VIF calculation.")
        return {}, []
    
    vif_scores = {}
    
    # Add a constant term for the intercept in the regression
    # VIF calculation typically requires an intercept in the auxiliary regression
    X = numeric_df.values
    if X.shape[0] < 2:
        logger.warning("Not enough samples to calculate VIF.")
        return {}, []
    
    # Calculate VIF for each feature
    # VIF_i = 1 / (1 - R_i^2) where R_i^2 is from regressing feature i on all other features
    for i, col in enumerate(numeric_df.columns):
        try:
            # statsmodels VIF function requires a constant column for the intercept
            # But the function variance_inflation_factor expects X with constant?
            # Actually, the function calculates VIF for the i-th column of X.
            # We need to include a constant column in X for the regression to be valid?
            # The standard implementation in statsmodels does:
            # vif = variance_inflation_factor(X_with_const, i)
            # But if we pass X without const, it might fail or be incorrect.
            # Let's add a constant column.
            X_with_const = np.column_stack([np.ones(X.shape[0]), X])
            vif = variance_inflation_factor(X_with_const, i+1) # i+1 because 0 is the constant
            vif_scores[col] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_scores[col] = np.nan
    
    high_vif_features = [col for col, score in vif_scores.items() if score >= threshold and not np.isnan(score)]
    
    if high_vif_features:
        logger.warning(f"High collinearity detected for features: {high_vif_features} (VIF >= {threshold})")
    else:
        logger.info("No high collinearity detected (all VIF < {threshold}).")
        
    return vif_scores, high_vif_features
