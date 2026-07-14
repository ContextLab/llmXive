"""
Cleaning strategies for data preprocessing.
Implements outlier removal, imputation, and categorical recoding.
"""
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers using the IQR method with a configurable multiplier k.
    
    Args:
        df: Input DataFrame
        k: Multiplier for IQR (default 1.5). Values outside [Q1 - k*IQR, Q3 + k*IQR] are removed.
    
    Returns:
        DataFrame with outliers removed
    """
    if df.empty:
        return df
    
    # Identify numerical columns
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numerical_cols:
        logger.info("No numerical columns found for outlier removal")
        return df
    
    # Create a mask for non-outliers
    mask = pd.Series([True] * len(df), index=df.index)
    
    for col in numerical_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        
        col_mask = (df[col] >= lower_bound) & (df[col] <= upper_bound)
        mask = mask & col_mask
    
    original_len = len(df)
    cleaned_df = df[mask].reset_index(drop=True)
    removed_count = original_len - len(cleaned_df)
    
    if removed_count > 0:
        logger.info(f"Removed {removed_count} rows ({100 * removed_count / original_len:.2f}%) as outliers using k={k}")
        if removed_count / original_len >= 0.5:
            logger.warning(f"WARNING: >=50% of rows removed ({removed_count}/{original_len}). Potential bias introduced.")
    else:
        logger.info(f"No outliers removed with k={k}")
    
    return cleaned_df

def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Fill missing values with the mean of each column.
    
    Args:
        df: Input DataFrame
        columns: List of columns to impute. If None, all numerical columns are used.
    
    Returns:
        DataFrame with missing values filled
    """
    if df.empty:
        return df
    
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    df_imputed = df.copy()
    
    for col in columns:
        if col in df_imputed.columns and df_imputed[col].isna().any():
            mean_val = df_imputed[col].mean()
            df_imputed[col] = df_imputed[col].fillna(mean_val)
            logger.info(f"Imputed {df[col].isna().sum()} missing values in {col} with mean={mean_val:.4f}")
    
    # Validate zero missing values in target columns
    remaining_na = df_imputed[columns].isna().sum().sum()
    if remaining_na > 0:
        logger.warning(f"Warning: {remaining_na} missing values remain after mean imputation")
    
    # Check for variance reduction
    for col in columns:
        if col in df.columns and df[col].notna().any() and df_imputed[col].notna().any():
            original_var = df[col].var()
            imputed_var = df_imputed[col].var()
            if original_var > 0 and imputed_var < original_var * 0.8:
                logger.warning(f"Variance reduction >=20% detected in {col}: {original_var:.4f} -> {imputed_var:.4f}")
    
    return df_imputed

def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Fill missing values with the median of each column.
    
    Args:
        df: Input DataFrame
        columns: List of columns to impute. If None, all numerical columns are used.
    
    Returns:
        DataFrame with missing values filled
    """
    if df.empty:
        return df
    
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    df_imputed = df.copy()
    
    for col in columns:
        if col in df_imputed.columns and df_imputed[col].isna().any():
            median_val = df_imputed[col].median()
            df_imputed[col] = df_imputed[col].fillna(median_val)
            logger.info(f"Imputed {df[col].isna().sum()} missing values in {col} with median={median_val:.4f}")
    
    # Validate zero missing values in target columns
    remaining_na = df_imputed[columns].isna().sum().sum()
    if remaining_na > 0:
        logger.warning(f"Warning: {remaining_na} missing values remain after median imputation")
    
    # Check for variance reduction
    for col in columns:
        if col in df.columns and df[col].notna().any() and df_imputed[col].notna().any():
            original_var = df[col].var()
            imputed_var = df_imputed[col].var()
            if original_var > 0 and imputed_var < original_var * 0.8:
                logger.warning(f"Variance reduction >=20% detected in {col}: {original_var:.4f} -> {imputed_var:.4f}")
    
    return df_imputed

def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> pd.DataFrame:
    """
    Fill missing values using K-Nearest Neighbors imputation.
    
    Args:
        df: Input DataFrame
        columns: List of columns to impute. If None, all numerical columns are used.
        k: Number of neighbors for KNN imputation (default 5)
    
    Returns:
        DataFrame with missing values filled
    """
    if df.empty:
        return df
    
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not columns:
        logger.info("No numerical columns for KNN imputation")
        return df
    
    # Check if there are any missing values
    if df[columns].isna().sum().sum() == 0:
        logger.info("No missing values to impute")
        return df
    
    df_imputed = df.copy()
    
    # Extract columns to impute
    X = df_imputed[columns].values
    
    # Apply KNN imputation
    imputer = KNNImputer(n_neighbors=k)
    X_imputed = imputer.fit_transform(X)
    
    # Update DataFrame
    for i, col in enumerate(columns):
        df_imputed[col] = X_imputed[:, i]
    
    logger.info(f"KNN imputation completed with k={k}")
    
    # Validate zero missing values in target columns
    remaining_na = df_imputed[columns].isna().sum().sum()
    if remaining_na > 0:
        logger.warning(f"Warning: {remaining_na} missing values remain after KNN imputation")
    
    # Check for variance reduction
    for col in columns:
        if col in df.columns and df[col].notna().any() and df_imputed[col].notna().any():
            original_var = df[col].var()
            imputed_var = df_imputed[col].var()
            if original_var > 0 and imputed_var < original_var * 0.8:
                logger.warning(f"Variance reduction >=20% detected in {col}: {original_var:.4f} -> {imputed_var:.4f}")
    
    return df_imputed

def apply_categorical_recoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply factor encoding to categorical columns for statistical testing.
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with categorical columns encoded
    """
    if df.empty:
        return df
    
    df_encoded = df.copy()
    
    # Identify categorical columns (object or category dtype)
    categorical_cols = df_encoded.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if not categorical_cols:
        logger.info("No categorical columns found for recoding")
        return df_encoded
    
    for col in categorical_cols:
        if df_encoded[col].isna().any():
            # Fill NaN with a placeholder before encoding
            df_encoded[col] = df_encoded[col].fillna('MISSING')
        
        # Apply label encoding
        le = LabelEncoder()
        df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
        logger.info(f"Encoded categorical column {col} with {len(le.classes_)} unique values")
    
    return df_encoded

def main():
    """Main entry point for testing cleaning functions."""
    logger.info("Cleaning module loaded successfully")
    # This is a module, not a script to run standalone
    pass

if __name__ == "__main__":
    main()
