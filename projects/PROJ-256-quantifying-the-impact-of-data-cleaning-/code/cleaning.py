"""
Cleaning module for data preprocessing.
Implements outlier removal, imputation, and categorical recoding.
"""
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

from utils import setup_logging

logger = setup_logging("INFO")

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers using IQR method.
    
    Args:
        df: Input DataFrame
        k: IQR multiplier (default 1.5)
        
    Returns:
        DataFrame with outliers removed
    """
    df_clean = df.copy()
    numerical_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numerical_cols:
        logger.warning("No numerical columns found for outlier removal")
        return df_clean
    
    rows_removed = 0
    for col in numerical_cols:
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        
        mask = (df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)
        df_clean = df_clean[mask]
    
    initial_rows = len(df)
    rows_removed = initial_rows - len(df_clean)
    
    if rows_removed > 0:
        logger.info(f"Removed {rows_removed} rows ({100*rows_removed/initial_rows:.1f}%) using IQR (k={k})")
        
        if rows_removed >= 0.5 * initial_rows:
            logger.warning(f"⚠️ BIAS ALERT: >=50% rows removed ({100*rows_removed/initial_rows:.1f}%). "
                         "Consider reviewing cleaning strategy.")
    
    return df_clean

def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Apply mean imputation for missing values.
    
    Args:
        df: Input DataFrame
        columns: List of columns to impute (default: all numerical)
        
    Returns:
        DataFrame with imputed values
    """
    df_imputed = df.copy()
    
    if columns is None:
        columns = df_imputed.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col in df_imputed.columns and df_imputed[col].isna().any():
            mean_val = df_imputed[col].mean()
            missing_count = df_imputed[col].isna().sum()
            if missing_count > 0:
                df_imputed[col] = df_imputed[col].fillna(mean_val)
                logger.info(f"Imputed {missing_count} missing values in {col} with mean={mean_val:.4f}")
    
    # Validate zero missing values
    remaining_missing = df_imputed[columns].isna().sum().sum()
    if remaining_missing > 0:
        logger.warning(f"Still {remaining_missing} missing values after imputation")
    
    # Check variance reduction
    for col in columns:
        if col in df_imputed.columns:
            original_var = df[col].var() if df[col].notna().any() else 0
            imputed_var = df_imputed[col].var()
            if original_var > 0 and imputed_var < original_var * 0.8:
                logger.warning(f"⚠️ Variance reduction >=20% in {col}: "
                             f"original={original_var:.4f}, imputed={imputed_var:.4f}")
    
    return df_imputed

def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Apply median imputation for missing values.
    
    Args:
        df: Input DataFrame
        columns: List of columns to impute (default: all numerical)
        
    Returns:
        DataFrame with imputed values
    """
    df_imputed = df.copy()
    
    if columns is None:
        columns = df_imputed.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col in df_imputed.columns and df_imputed[col].isna().any():
            median_val = df_imputed[col].median()
            missing_count = df_imputed[col].isna().sum()
            if missing_count > 0:
                df_imputed[col] = df_imputed[col].fillna(median_val)
                logger.info(f"Imputed {missing_count} missing values in {col} with median={median_val:.4f}")
    
    # Validate zero missing values
    remaining_missing = df_imputed[columns].isna().sum().sum()
    if remaining_missing > 0:
        logger.warning(f"Still {remaining_missing} missing values after imputation")
    
    # Check variance reduction
    for col in columns:
        if col in df_imputed.columns:
            original_var = df[col].var() if df[col].notna().any() else 0
            imputed_var = df_imputed[col].var()
            if original_var > 0 and imputed_var < original_var * 0.8:
                logger.warning(f"⚠️ Variance reduction >=20% in {col}: "
                             f"original={original_var:.4f}, imputed={imputed_var:.4f}")
    
    return df_imputed

def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> pd.DataFrame:
    """
    Apply KNN imputation for missing values.
    
    Args:
        df: Input DataFrame
        columns: List of columns to impute (default: all numerical)
        k: Number of neighbors for KNN imputer
        
    Returns:
        DataFrame with imputed values
    """
    df_imputed = df.copy()
    
    if columns is None:
        columns = df_imputed.select_dtypes(include=[np.number]).columns.tolist()
    
    if not columns:
        logger.warning("No numerical columns for KNN imputation")
        return df_imputed
    
    # Extract columns for imputation
    data_subset = df_imputed[columns].values
    
    # Check if there are any missing values
    if np.isnan(data_subset).sum() == 0:
        logger.info("No missing values to impute")
        return df_imputed
    
    # Apply KNN imputation
    imputer = KNNImputer(n_neighbors=k)
    imputed_data = imputer.fit_transform(data_subset)
    
    # Update DataFrame
    for i, col in enumerate(columns):
        df_imputed[col] = imputed_data[:, i]
    
    logger.info(f"KNN imputation completed with k={k}")
    
    # Validate zero missing values
    remaining_missing = df_imputed[columns].isna().sum().sum()
    if remaining_missing > 0:
        logger.warning(f"Still {remaining_missing} missing values after KNN imputation")
    
    # Check variance reduction
    for col in columns:
        if col in df_imputed.columns:
            original_var = df[col].var() if df[col].notna().any() else 0
            imputed_var = df_imputed[col].var()
            if original_var > 0 and imputed_var < original_var * 0.8:
                logger.warning(f"⚠️ Variance reduction >=20% in {col}: "
                             f"original={original_var:.4f}, imputed={imputed_var:.4f}")
    
    return df_imputed

def apply_categorical_recoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply categorical recoding (label encoding) for statistical testing.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with encoded categorical columns
    """
    df_encoded = df.copy()
    
    # Identify categorical columns (object or category dtype)
    categorical_cols = df_encoded.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if not categorical_cols:
        logger.info("No categorical columns to encode")
        return df_encoded
    
    encoder = LabelEncoder()
    for col in categorical_cols:
        if df_encoded[col].nunique() > 1:  # Only encode if more than one category
            df_encoded[col] = encoder.fit_transform(df_encoded[col].astype(str))
            logger.info(f"Encoded categorical column: {col} ({df[col].nunique()} categories)")
        else:
            logger.warning(f"Column {col} has only one unique value, skipping encoding")
    
    return df_encoded

def main():
    """Main entry point for cleaning module."""
    logger.info("Cleaning module loaded")

if __name__ == "__main__":
    main()
