import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger('llmXive')

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers using IQR method.
    
    Args:
        df: Input DataFrame
        k: Multiplier for IQR (default 1.5)
    
    Returns:
        DataFrame with outliers removed
    """
    if df is None or df.empty:
        return df
    
    df_clean = df.copy()
    numerical_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
    
    rows_removed = 0
    total_rows = len(df_clean)
    
    for col in numerical_cols:
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        
        mask = (df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)
        df_clean = df_clean[mask]
    
    rows_removed = total_rows - len(df_clean)
    removal_pct = (rows_removed / total_rows * 100) if total_rows > 0 else 0
    
    logger.info(f"IQR outlier removal: removed {rows_removed} rows ({removal_pct:.1f}%)")
    
    if removal_pct >= 50:
        logger.warning(f"Bias alert: {removal_pct:.1f}% of rows removed. Results may be biased.")
    
    return df_clean

def apply_mean_imputation(df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
    """
    Apply mean imputation for missing values.
    
    Args:
        df: Input DataFrame
        columns: List of columns to impute (all numerical if None)
    
    Returns:
        DataFrame with imputed values
    """
    if df is None or df.empty:
        return df
    
    df_imputed = df.copy()
    
    if columns is None:
        columns = df_imputed.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col in df_imputed.columns:
            mean_val = df_imputed[col].mean()
            df_imputed[col] = df_imputed[col].fillna(mean_val)
    
    # Validate
    missing_count = df_imputed[columns].isnull().sum().sum()
    if missing_count > 0:
        logger.warning(f"Mean imputation: {missing_count} missing values remain")
    else:
        logger.info(f"Mean imputation: completed successfully for {len(columns)} columns")
    
    return df_imputed

def apply_median_imputation(df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
    """
    Apply median imputation for missing values.
    
    Args:
        df: Input DataFrame
        columns: List of columns to impute (all numerical if None)
    
    Returns:
        DataFrame with imputed values
    """
    if df is None or df.empty:
        return df
    
    df_imputed = df.copy()
    
    if columns is None:
        columns = df_imputed.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col in df_imputed.columns:
            median_val = df_imputed[col].median()
            df_imputed[col] = df_imputed[col].fillna(median_val)
    
    # Validate
    missing_count = df_imputed[columns].isnull().sum().sum()
    if missing_count > 0:
        logger.warning(f"Median imputation: {missing_count} missing values remain")
    else:
        logger.info(f"Median imputation: completed successfully for {len(columns)} columns")
    
    return df_imputed

def apply_knn_imputation(df: pd.DataFrame, columns: List[str] = None, k: int = 5) -> pd.DataFrame:
    """
    Apply KNN imputation for missing values.
    
    Args:
        df: Input DataFrame
        columns: List of columns to impute (all numerical if None)
        k: Number of neighbors for KNN (default 5)
    
    Returns:
        DataFrame with imputed values
    """
    if df is None or df.empty:
        return df
    
    df_imputed = df.copy()
    
    if columns is None:
        columns = df_imputed.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter to columns that exist and have missing values
    cols_to_impute = [c for c in columns if c in df_imputed.columns and df_imputed[c].isnull().any()]
    
    if not cols_to_impute:
        logger.info("KNN imputation: No missing values to impute")
        return df_imputed
    
    try:
        imputer = KNNImputer(n_neighbors=k)
        df_imputed[cols_to_impute] = imputer.fit_transform(df_imputed[cols_to_impute])
    except Exception as e:
        logger.error(f"KNN imputation failed: {e}")
        return df_imputed
    
    # Validate
    missing_count = df_imputed[cols_to_impute].isnull().sum().sum()
    if missing_count > 0:
        logger.warning(f"KNN imputation: {missing_count} missing values remain")
    else:
        logger.info(f"KNN imputation: completed successfully for {len(cols_to_impute)} columns")
    
    return df_imputed

def apply_categorical_recoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply categorical recoding (label encoding) for statistical testing.
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with encoded categorical columns
    """
    if df is None or df.empty:
        return df
    
    df_encoded = df.copy()
    categorical_cols = df_encoded.select_dtypes(include=['object', 'category']).columns.tolist()
    
    encoder = LabelEncoder()
    for col in categorical_cols:
        if df_encoded[col].nunique() > 1:
            df_encoded[col] = encoder.fit_transform(df_encoded[col].astype(str))
            logger.info(f"Categorical recoding: encoded column {col} with {df_encoded[col].nunique()} categories")
    
    return df_encoded

def main():
    """Main entry point for cleaning module."""
    logger.info("Cleaning module loaded")