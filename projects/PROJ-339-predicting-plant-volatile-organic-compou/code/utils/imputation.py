"""
Imputation utilities for handling missing values.
Implements T009a (Median) and T009b (KNN) strategies.
"""
import pandas as pd
import numpy as np
from typing import Literal, Optional

def impute_missing_values(
    df: pd.DataFrame,
    strategy: Literal['median', 'mean', 'knn'] = 'median',
    n_neighbors: int = 5
) -> pd.DataFrame:
    """
    Impute missing values in the DataFrame based on the specified strategy.
    
    Args:
        df: Input DataFrame.
        strategy: Imputation strategy ('median', 'mean', 'knn').
        n_neighbors: Number of neighbors for KNN imputation (default 5).
    
    Returns:
        DataFrame with imputed values.
    
    Raises:
        ImportError: If scikit-learn is not installed for KNN strategy.
        ValueError: If an unsupported strategy is provided.
    """
    if strategy not in ('median', 'mean', 'knn'):
        raise ValueError(f"Unsupported strategy: {strategy}. Use 'median', 'mean', or 'knn'.")
    
    df_copy = df.copy()
    
    # Identify numeric columns only
    numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        return df_copy
    
    if strategy == 'median':
        for col in numeric_cols:
            median_val = df_copy[col].median()
            # If median is NaN (e.g., all values missing), fill with 0 as fallback
            if pd.isna(median_val):
                median_val = 0.0
            df_copy[col] = df_copy[col].fillna(median_val)
            
    elif strategy == 'mean':
        for col in numeric_cols:
            mean_val = df_copy[col].mean()
            if pd.isna(mean_val):
                mean_val = 0.0
            df_copy[col] = df_copy[col].fillna(mean_val)
            
    elif strategy == 'knn':
        try:
            from sklearn.impute import KNNImputer
        except ImportError:
            raise ImportError(
                "scikit-learn is required for KNN imputation. "
                "Please install it via `pip install scikit-learn`."
            )
        
        imputer = KNNImputer(n_neighbors=n_neighbors)
        # Only impute numeric columns
        df_numeric = df_copy[numeric_cols]
        
        # Check if there are any missing values to impute
        if df_numeric.isnull().any().any():
            imputed_array = imputer.fit_transform(df_numeric)
            df_copy[numeric_cols] = imputed_array
        # If no missing values, we just return the copy
    
    Args:
        train_df: Training DataFrame
        val_df: Validation DataFrame
        
    Returns:
        Tuple of (imputed_train_df, imputed_val_df)
    """
    if train_df.empty and val_df.empty:
        return train_df, val_df
    
    # Use median strategy for robustness without external dependencies in CV loop
    # Calculate medians on training data only
    medians = train_df.median(numeric_only=True)
    
    # Apply to both sets
    train_imputed = train_df.fillna(medians)
    val_imputed = val_df.fillna(medians)
    
    return train_imputed, val_imputed

def main():
    # Simple test
    df = pd.DataFrame({
        'A': [1, 2, np.nan, 4],
        'B': [5, np.nan, 7, 8]
    })
    print("Original:")
    print(df)
    print("\nImputed (median):")
    print(impute_missing_values(df, 'median'))

if __name__ == "__main__":
    main()
