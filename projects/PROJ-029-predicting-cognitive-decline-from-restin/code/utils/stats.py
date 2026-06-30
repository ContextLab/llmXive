"""
Statistical utilities for feature analysis and collinearity checks.
"""
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from typing import Tuple, List, Optional

def check_collinearity(df: pd.DataFrame, threshold: float = 0.95) -> Tuple[pd.DataFrame, List[str]]:
    """
    Identify and remove highly correlated features (Pearson > threshold).
    Keeps the feature with higher variance.
    
    Args:
        df: DataFrame of features (numeric columns only).
        threshold: Correlation threshold for exclusion.
        
    Returns:
        Tuple of (DataFrame with collinear features removed, list of dropped columns).
    """
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        return df, []
    
    final_drop = set()
    columns = list(numeric_df.columns)
    
    # Greedy approach to identify collinear pairs
    for i in range(len(columns)):
        if columns[i] in final_drop:
            continue
        for j in range(i + 1, len(columns)):
            if columns[j] in final_drop:
                continue
            
            corr_val = numeric_df[columns[i]].corr(numeric_df[columns[j]])
            if abs(corr_val) > threshold:
                # Compare variance
                var_i = numeric_df[columns[i]].var()
                var_j = numeric_df[columns[j]].var()
                
                if var_i < var_j:
                    final_drop.add(columns[i])
                else:
                    final_drop.add(columns[j])
    
    dropped_cols = list(final_drop)
    return df.drop(columns=dropped_cols), dropped_cols

def calculate_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the correlation matrix for numeric columns.
    
    Args:
        df: DataFrame with numeric columns.
        
    Returns:
        Correlation matrix as DataFrame.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return pd.DataFrame()
    return numeric_df.corr()

def calculate_feature_variance(df: pd.DataFrame) -> pd.Series:
    """
    Calculate variance for each numeric column.
    
    Args:
        df: DataFrame with numeric columns.
        
    Returns:
        Series of variances indexed by column name.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return pd.Series()
    return numeric_df.var()

def filter_low_variance_features(df: pd.DataFrame, threshold: float = 0.01) -> Tuple[pd.DataFrame, List[str]]:
    """
    Remove features with variance below a threshold.
    
    Args:
        df: DataFrame with numeric columns.
        threshold: Minimum variance threshold.
        
    Returns:
        Tuple of (filtered DataFrame, list of dropped columns).
    """
    if df.empty:
        return df, []
        
    variances = calculate_feature_variance(df)
    low_var_cols = variances[variances <= threshold].index.tolist()
    
    if not low_var_cols:
        return df, []
        
    return df.drop(columns=low_var_cols), low_var_cols

def calculate_pearson_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient and p-value.
    
    Args:
        x: First array.
        y: Second array.
        
    Returns:
        Tuple of (correlation coefficient, p-value).
    """
    return pearsonr(x, y)
