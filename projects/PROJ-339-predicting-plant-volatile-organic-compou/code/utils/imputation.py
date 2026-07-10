"""
Imputation utilities for handling missing values.
Implements T009.
"""
import pandas as pd
import numpy as np
from typing import Literal

def impute_missing_values(df: pd.DataFrame, strategy: Literal['median', 'mean', 'knn'] = 'median') -> pd.DataFrame:
    """
    Impute missing values in the DataFrame.
    
    Args:
        df: Input DataFrame.
        strategy: Imputation strategy ('median', 'mean', 'knn').
    
    Returns:
        DataFrame with imputed values.
    """
    df_copy = df.copy()
    
    # Identify numeric columns
    numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
    
    if strategy == 'median':
        for col in numeric_cols:
            median_val = df_copy[col].median()
            df_copy[col] = df_copy[col].fillna(median_val)
    elif strategy == 'mean':
        for col in numeric_cols:
            mean_val = df_copy[col].mean()
            df_copy[col] = df_copy[col].fillna(mean_val)
    elif strategy == 'knn':
        # Simple KNN imputation placeholder using sklearn
        # Requires sklearn to be installed
        try:
            from sklearn.impute import KNNImputer
            imputer = KNNImputer(n_neighbors=5)
            # Only impute numeric columns
            df_numeric = df_copy[numeric_cols]
            imputed_array = imputer.fit_transform(df_numeric)
            df_copy[numeric_cols] = imputed_array
        except ImportError:
            raise ImportError("scikit-learn is required for KNN imputation.")
    
    return df_copy
