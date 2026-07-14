"""
Collinearity utilities for VIF analysis (T014).

This module provides:
- Variance Inflation Factor (VIF) calculation
- Identification of high collinearity features
"""
import os
import logging
from typing import List, Dict, Optional

import numpy as np
import pandas as pd

from code.utils.logger import get_pipeline_logger
from code.utils.error_handling import DataProcessingError

logger = get_pipeline_logger(__name__)

def calculate_vif(df: pd.DataFrame, column_prefix: str = 'feat_') -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        df: DataFrame with feature columns.
        column_prefix: Prefix of feature columns to analyze.
    
    Returns:
        DataFrame with VIF results.
    """
    logger.info("Calculating VIF...")
    
    # Select feature columns
    feature_cols = [col for col in df.columns if col.startswith(column_prefix)]
    if len(feature_cols) < 2:
        logger.warning("Not enough features for VIF calculation.")
        return pd.DataFrame({'feature': [], 'VIF': []})
    
    X = df[feature_cols].values
    
    # Remove constant columns
    constant_cols = []
    for i, col in enumerate(feature_cols):
        if np.all(X[:, i] == X[0, i]):
            constant_cols.append(col)
    if constant_cols:
        logger.warning(f"Constant columns detected: {constant_cols}. Removing them.")
        X = np.delete(X, [feature_cols.index(c) for c in constant_cols], axis=1)
        feature_cols = [c for c in feature_cols if c not in constant_cols]
    
    if X.shape[1] < 2:
        logger.warning("Not enough features after removing constants.")
        return pd.DataFrame({'feature': feature_cols, 'VIF': [1.0] * len(feature_cols)})
    
    vif_results = []
    for i, col in enumerate(feature_cols):
        # Calculate VIF
        try:
            # VIF = 1 / (1 - R^2)
            # R^2 from regressing col on all other features
            y = X[:, i]
            X_other = np.delete(X, i, axis=1)
            
            # Add intercept
            X_other = np.column_stack([np.ones(len(y)), X_other])
            
            # Ordinary least squares
            beta = np.linalg.lstsq(X_other, y, rcond=None)[0]
            y_pred = X_other @ beta
            
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            vif = 1 / (1 - r_squared) if (1 - r_squared) > 1e-10 else np.inf
            
            vif_results.append({'feature': col, 'VIF': vif})
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {str(e)}")
            vif_results.append({'feature': col, 'VIF': np.inf})
    
    return pd.DataFrame(vif_results)

def identify_high_collinearity(vif_df: pd.DataFrame, threshold: float = 10.0) -> List[str]:
    """
    Identify features with high VIF.
    
    Args:
        vif_df: DataFrame with VIF results.
        threshold: VIF threshold for high collinearity.
    
    Returns:
        List of feature names with high VIF.
    """
    if vif_df.empty:
        return []
    
    high_vif = vif_df[vif_df['VIF'] > threshold]
    return high_vif['feature'].tolist()

if __name__ == "__main__":
    # Test with mock data
    df = pd.DataFrame({
        'feat_a': np.random.rand(100),
        'feat_b': np.random.rand(100),
        'feat_c': np.random.rand(100),
    })
    # Add correlation
    df['feat_d'] = df['feat_a'] * 1.1
    
    vif_results = calculate_vif(df)
    print(vif_results)
    high_vif = identify_high_collinearity(vif_results)
    print(f"High VIF features: {high_vif}")