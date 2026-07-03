"""
Diagnostics utilities for statistical analysis.

Implements Variance Inflation Factor (VIF) calculations to detect
multicollinearity among predictor variables.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from config import get_config
from utils.logging import get_logger

def get_logger_wrapper(func):
    """Decorator to add logging to functions."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__name__)
        logger.info(f"Starting {func.__name__}")
        result = func(*args, **logger, **kwargs)
        logger.info(f"Completed {func.__name__}")
        return result
    return wrapper

def calculate_vif_for_pair(df: pd.DataFrame, var1: str, var2: str) -> float:
    """
    Calculate VIF for a pair of variables by fitting a regression of one on the other.
    
    VIF for var1 = 1 / (1 - R^2) where R^2 is from regressing var1 on var2.
    For two variables, VIF(var1) == VIF(var2).
    
    Args:
        df: DataFrame containing the variables
        var1: First variable name
        var2: Second variable name
        
    Returns:
        VIF value (float)
    """
    logger = get_logger("calculate_vif_for_pair")
    
    # Drop rows with missing values in either variable
    valid_df = df[[var1, var2]].dropna()
    
    if len(valid_df) < 3:
        logger.warning(f"Insufficient data for VIF calculation between {var1} and {var2}")
        return np.inf
    
    # Regress var1 on var2
    X = valid_df[[var2]].values
    y = valid_df[var1].values
    
    # Add intercept
    X_with_intercept = np.column_stack([np.ones(len(X)), X])
    
    # Calculate R^2
    try:
        # Ordinary Least Squares
        beta = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
        y_pred = X_with_intercept @ beta
        
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        
        if ss_tot == 0:
            logger.warning(f"Zero variance in {var1}, cannot calculate R^2")
            return np.inf
        
        r_squared = 1 - (ss_res / ss_tot)
        
        # VIF = 1 / (1 - R^2)
        if r_squared >= 1.0:
            logger.warning(f"Perfect collinearity detected between {var1} and {var2}")
            return np.inf
        
        vif = 1.0 / (1.0 - r_squared)
        return vif
        
    except Exception as e:
        logger.error(f"Error calculating VIF for pair ({var1}, {var2}): {e}")
        return np.inf

def calculate_vif(df: pd.DataFrame, variables: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate VIF for multiple variables in a DataFrame.
    
    For each variable, regress it on all other variables and calculate VIF.
    
    Args:
        df: DataFrame containing predictor variables
        variables: List of variable names to calculate VIF for. 
                  If None, uses all numeric columns.
                  
    Returns:
        Dictionary mapping variable names to their VIF values
    """
    logger = get_logger("calculate_vif")
    
    if variables is None:
        # Select all numeric columns
        variables = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(variables) < 2:
        logger.warning("Need at least 2 variables to calculate VIF")
        return {var: np.inf for var in variables}
    
    vif_results = {}
    
    for var in variables:
        # Get other variables
        other_vars = [v for v in variables if v != var]
        
        # Create regression matrix
        valid_cols = [var] + other_vars
        valid_df = df[valid_cols].dropna()
        
        if len(valid_df) < len(other_vars) + 1:
            logger.warning(f"Insufficient data for VIF of {var}")
            vif_results[var] = np.inf
            continue
        
        X = valid_df[other_vars].values
        y = valid_df[var].values
        
        # Add intercept
        X_with_intercept = np.column_stack([np.ones(len(X)), X])
        
        try:
            # Calculate R^2
            beta = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
            y_pred = X_with_intercept @ beta
            
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            
            if ss_tot == 0:
                vif_results[var] = np.inf
                continue
            
            r_squared = 1 - (ss_res / ss_tot)
            
            if r_squared >= 1.0:
                vif_results[var] = np.inf
            else:
                vif_results[var] = 1.0 / (1.0 - r_squared)
                
        except Exception as e:
            logger.error(f"Error calculating VIF for {var}: {e}")
            vif_results[var] = np.inf
    
    return vif_results

def flag_high_vif_variables(vif_results: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Identify variables with VIF above a threshold.
    
    Args:
        vif_results: Dictionary of variable names to VIF values
        threshold: VIF threshold for flagging (default 5.0)
        
    Returns:
        List of variable names with VIF >= threshold
    """
    logger = get_logger("flag_high_vif_variables")
    
    high_vif_vars = [
        var for var, vif in vif_results.items() 
        if vif >= threshold and not np.isinf(vif)
    ]
    
    infinite_vif_vars = [
        var for var, vif in vif_results.items() 
        if np.isinf(vif)
    ]
    
    if high_vif_vars:
        logger.warning(f"High VIF detected for variables: {high_vif_vars} (threshold={threshold})")
    
    if infinite_vif_vars:
        logger.error(f"Perfect collinearity detected for variables: {infinite_vif_vars}")
    
    return high_vif_vars + infinite_vif_vars

def summary_vif_report(df: pd.DataFrame, variables: Optional[List[str]] = None, 
                      threshold: float = 5.0) -> Dict[str, Any]:
    """
    Generate a comprehensive VIF analysis report.
    
    Args:
        df: DataFrame containing predictor variables
        variables: List of variable names to analyze
        threshold: VIF threshold for flagging
        
    Returns:
        Dictionary containing VIF results, flagged variables, and summary statistics
    """
    logger = get_logger("summary_vif_report")
    
    vif_results = calculate_vif(df, variables)
    flagged_vars = flag_high_vif_variables(vif_results, threshold)
    
    # Calculate summary statistics
    valid_vifs = [v for v in vif_results.values() if not np.isinf(v)]
    
    report = {
        "vif_values": vif_results,
        "flagged_variables": flagged_vars,
        "threshold": threshold,
        "summary": {
            "total_variables": len(vif_results),
            "flagged_count": len(flagged_vars),
            "mean_vif": np.mean(valid_vifs) if valid_vifs else None,
            "max_vif": np.max(valid_vifs) if valid_vifs else None,
            "min_vif": np.min(valid_vifs) if valid_vifs else None,
            "perfect_collinearity_count": sum(1 for v in vif_results.values() if np.isinf(v))
        }
    }
    
    logger.info(f"VIF report generated: {len(flagged_vars)} variables flagged out of {len(vif_results)}")
    
    return report

def main():
    """
    Main function to demonstrate VIF calculation.
    
    This can be used for testing or as a standalone diagnostic tool.
    """
    logger = get_logger("main")
    config = get_config()
    
    # Example usage with sample data
    logger.info("VIF Diagnostics Module Ready")
    logger.info("Use calculate_vif() for pairwise or multivariate VIF analysis")
    logger.info("Use flag_high_vif_variables() to identify problematic predictors")
    logger.info("Use summary_vif_report() for comprehensive analysis")
    
    return {
        "status": "ready",
        "functions": [
            "calculate_vif_for_pair",
            "calculate_vif", 
            "flag_high_vif_variables",
            "summary_vif_report"
        ]
    }

if __name__ == "__main__":
    result = main()
    print(result)