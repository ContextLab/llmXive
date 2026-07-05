"""
Diagnostics module for statistical modeling.

Implements Variance Inflation Factor (VIF) calculation and collinearity
flagging for User Story 2 (US2).
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Set, Tuple
import logging

import statsmodels.api as sm

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor in the dataframe.
    
    VIF measures how much the variance of an estimated regression coefficient
    increases if your predictors are correlated.
    
    Formula: VIF = 1 / (1 - R^2) where R^2 is from regressing the variable
    against all other predictors.
    
    Args:
        df: DataFrame containing only numeric predictor variables.
            
    Returns:
        pd.Series: VIF scores for each column.
            
    Raises:
        ValueError: If dataframe contains non-numeric data or is empty.
    """
    if df.empty:
        logger.warning("Empty dataframe provided to calculate_vif")
        return pd.Series(dtype=float)
    
    # Ensure all columns are numeric
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty or len(numeric_df.columns) != len(df.columns):
        raise ValueError("All columns in the dataframe must be numeric for VIF calculation.")
    
    vif_scores = pd.Series(dtype=float, index=numeric_df.columns)
    
    for col in numeric_df.columns:
        # Create a model where 'col' is the target and other columns are predictors
        y = numeric_df[col]
        X = numeric_df.drop(columns=[col])
        
        if X.empty:
            # Only one variable, VIF is 1 by definition
            vif_scores[col] = 1.0
            continue
        
        # Add constant for intercept
        X_const = sm.add_constant(X)
        
        try:
            # Fit OLS model
            model = sm.OLS(y, X_const).fit()
            r_squared = model.rsquared
            
            # Handle perfect collinearity (R^2 = 1)
            if r_squared >= 1.0:
                vif_scores[col] = np.inf
            else:
                vif_scores[col] = 1.0 / (1.0 - r_squared)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_scores[col] = np.nan
    
    return vif_scores

def flag_collinearity(df: pd.DataFrame, threshold: float = 5.0) -> List[str]:
    """
    Identify predictors with VIF exceeding the specified threshold.
    
    This function calculates VIF for all predictors in the provided DataFrame
    and returns a list of column names that exceed the threshold.
    
    Args:
        df: DataFrame containing predictor variables.
        threshold: VIF threshold above which a variable is considered collinear.
                   Default is 5.0 as per specification.
                    
    Returns:
        List of column names that exceed the threshold.
    """
    if df.empty:
        return []
    
    try:
        vif_scores = calculate_vif(df)
    except ValueError as e:
        logger.error(f"Failed to calculate VIF: {e}")
        return []
    
    flagged_vars = []
    
    for col, score in vif_scores.items():
        if np.isinf(score) or score > threshold:
            flagged_vars.append(col)
            if np.isinf(score):
                logger.warning(f"Collinearity detected: {col} has VIF = inf (perfect collinearity)")
            else:
                logger.warning(f"Collinearity detected: {col} has VIF = {score:.2f} (threshold: {threshold})")
    
    return flagged_vars

def get_collinearity_report(df: pd.DataFrame, threshold: float = 5.0) -> Dict[str, any]:
    """
    Generate a comprehensive collinearity report.
    
    Args:
        df: DataFrame containing predictor variables.
        threshold: VIF threshold for flagging.
        
    Returns:
        Dictionary containing VIF scores, flagged variables, and summary statistics.
    """
    if df.empty:
        return {
            "vif_scores": pd.Series(dtype=float),
            "flagged_variables": [],
            "max_vif": 0.0,
            "mean_vif": 0.0,
            "count_flagged": 0
        }
    
    vif_scores = calculate_vif(df)
    flagged_vars = flag_collinearity(df, threshold)
    
    valid_scores = vif_scores.dropna()
    
    return {
        "vif_scores": vif_scores,
        "flagged_variables": flagged_vars,
        "max_vif": float(valid_scores.max()) if not valid_scores.empty else 0.0,
        "mean_vif": float(valid_scores.mean()) if not valid_scores.empty else 0.0,
        "count_flagged": len(flagged_vars),
        "total_predictors": len(df.columns)
    }