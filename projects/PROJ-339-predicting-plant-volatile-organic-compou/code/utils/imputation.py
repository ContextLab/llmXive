import pandas as pd
import numpy as np
from typing import Literal

def impute_missing_values(df: pd.DataFrame, strategy: Literal['median', 'knn'] = 'median') -> pd.DataFrame:
    """
    Impute missing values in a DataFrame.
    
    Args:
        df: Input DataFrame
        strategy: 'median' or 'knn'
        
    Returns:
        DataFrame with imputed values
    """
    if df.empty:
        return df
    
    if strategy == 'median':
        return df.fillna(df.median(numeric_only=True))
    elif strategy == 'knn':
        # Simple KNN imputation using sklearn
        from sklearn.impute import KNNImputer
        imputer = KNNImputer(n_neighbors=5)
        imputed_array = imputer.fit_transform(df)
        return pd.DataFrame(imputed_array, columns=df.columns, index=df.index)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

def fit_impute_cv(train_df: pd.DataFrame, val_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fit imputation on training data and apply to both train and validation sets.
    This prevents data leakage in cross-validation.
    
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
