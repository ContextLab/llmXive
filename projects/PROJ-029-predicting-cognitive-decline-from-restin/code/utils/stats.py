import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from typing import Tuple, List, Optional

def check_collinearity(df: pd.DataFrame, threshold: float = 0.95) -> List[Tuple[str, str, float]]:
    """Check for collinearity between features."""
    correlations = []
    features = df.columns.tolist()
    
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            corr, _ = pearsonr(df[features[i]], df[features[j]])
            if abs(corr) > threshold:
                correlations.append((features[i], features[j], corr))
    
    return correlations

def calculate_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate correlation matrix for features."""
    return df.corr()

def calculate_feature_variance(df: pd.DataFrame) -> pd.Series:
    """Calculate variance for each feature."""
    return df.var()

def filter_low_variance_features(df: pd.DataFrame, threshold: float = 0.01) -> pd.DataFrame:
    """Remove features with variance below threshold."""
    variances = calculate_feature_variance(df)
    high_var_features = variances[variances > threshold].index
    return df[high_var_features]

def calculate_pearson_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Calculate Pearson correlation and p-value."""
    return pearsonr(x, y)
