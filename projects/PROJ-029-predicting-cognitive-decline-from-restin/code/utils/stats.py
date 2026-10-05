"""Statistical utilities for collinearity detection, variance thresholding, and analysis."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from typing import Tuple, List, Optional

def check_collinearity(df: pd.DataFrame, threshold: float = 0.95) -> List[Tuple[str, str, float]]:
    """Check for collinearity between features.
    
    Args:
        df: DataFrame containing feature columns.
        threshold: Absolute correlation threshold above which features are considered collinear.
        
    Returns:
        List of tuples (feature_i, feature_j, correlation) where |corr| > threshold.
    """
    correlations = []
    features = df.columns.tolist()
    
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            corr, _ = pearsonr(df[features[i]].to_numpy(), df[features[j]].to_numpy())
            if abs(corr) > threshold:
                correlations.append((features[i], features[j], corr))
    
    return correlations

def calculate_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate correlation matrix for features.
    
    Args:
        df: DataFrame containing feature columns.
        
    Returns:
        Correlation matrix as a DataFrame.
    """
    return df.corr()

def calculate_feature_variance(df: pd.DataFrame) -> pd.Series:
    """Calculate variance for each feature.
    
    Args:
        df: DataFrame containing feature columns.
        
    Returns:
        Series of variances indexed by feature name.
    """
    return df.var()

def filter_low_variance_features(df: pd.DataFrame, threshold: float = 0.01) -> pd.DataFrame:
    """Remove features with variance below threshold.
    
    Args:
        df: DataFrame containing feature columns.
        threshold: Minimum variance threshold.
        
    Returns:
        DataFrame with low-variance features removed.
    """
    variances = calculate_feature_variance(df)
    high_var_features = variances[variances > threshold].index
    return df[high_var_features]

def calculate_pearson_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Calculate Pearson correlation and p-value.
    
    Args:
        x: First array of values.
        y: Second array of values.
        
    Returns:
        Tuple of (correlation coefficient, p-value).
    """
    return pearsonr(x, y)