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
    Rows are removed if any numerical value is outside [Q1 - k*IQR, Q3 + k*IQR].
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to apply_iqr_outlier_removal")
        return df
    
    df_clean = df.copy()
    numerical_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numerical_cols:
        logger.warning("No numerical columns found for outlier removal")
        return df_clean
    
    rows_removed = 0
    total_rows = len(df_clean)
    
    rows_removed = 0
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
    
    logger.info(f"IQR outlier removal (k={k}): removed {rows_removed} rows ({removal_pct:.1f}%)")
    
    if removal_pct >= 50:
        logger.warning(f"High outlier removal rate ({removal_pct:.1f}%). Potential bias introduced.")
    
    return df_clean

def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Apply mean imputation to specified columns."""
    if df.empty:
        logger.warning("Empty DataFrame provided to apply_mean_imputation")
        return df
    
    df_imputed = df.copy()
    
    if columns is None:
        columns = df_imputed.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col in df_imputed.columns:
            mean_val = df_imputed[col].mean()
            df_imputed[col] = df_imputed[col].fillna(mean_val)
            logger.debug(f"Mean imputation for {col}: mean={mean_val:.4f}")
    
    # Validate zero missing values
    missing = df_imputed[columns].isnull().sum().sum()
    if missing > 0:
        logger.warning(f"Mean imputation failed: {missing} missing values remain")
    else:
        logger.info(f"Mean imputation completed: 0 missing values in {len(columns)} columns")
    
    return df_imputed

def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Apply median imputation to specified columns."""
    if df.empty:
        logger.warning("Empty DataFrame provided to apply_median_imputation")
        return df
    
    df_imputed = df.copy()
    
    if columns is None:
        columns = df_imputed.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col in df_imputed.columns:
            median_val = df_imputed[col].median()
            df_imputed[col] = df_imputed[col].fillna(median_val)
            logger.debug(f"Median imputation for {col}: median={median_val:.4f}")
    
    # Validate zero missing values
    missing = df_imputed[columns].isnull().sum().sum()
    if missing > 0:
        logger.warning(f"Median imputation failed: {missing} missing values remain")
    else:
        logger.info(f"Median imputation completed: 0 missing values in {len(columns)} columns")
    
    return df_imputed

def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> pd.DataFrame:
    """Apply KNN imputation to specified columns."""
    if df.empty:
        logger.warning("Empty DataFrame provided to apply_knn_imputation")
        return df
    
    df_imputed = df.copy()
    
    if columns is None:
        columns = df_imputed.select_dtypes(include=[np.number]).columns.tolist()
    
    if not columns:
        logger.warning("No numerical columns for KNN imputation")
        return df_imputed
    
    # Check for missing values
    missing_mask = df_imputed[columns].isnull().any(axis=1)
    if not missing_mask.any():
        logger.info("No missing values to impute")
        return df_imputed
    
    try:
        imputer = KNNImputer(n_neighbors=min(k, len(df_imputed)))
        df_imputed[columns] = imputer.fit_transform(df_imputed[columns])
        
        # Validate zero missing values
        remaining_missing = df_imputed[columns].isnull().sum().sum()
        if remaining_missing > 0:
            logger.warning(f"KNN imputation incomplete: {remaining_missing} missing values remain")
        else:
            logger.info(f"KNN imputation (k={k}) completed: 0 missing values in {len(columns)} columns")
    except Exception as e:
        logger.error(f"KNN imputation failed: {e}")
    
    return df_imputed

def apply_categorical_recoding(df: pd.DataFrame) -> pd.DataFrame:
    """Apply factor encoding for categorical columns."""
    if df.empty:
        logger.warning("Empty DataFrame provided to apply_categorical_recoding")
        return df
    
    df_encoded = df.copy()
    categorical_cols = df_encoded.select_dtypes(include=['object', 'category']).columns.tolist()
    
    encoder = LabelEncoder()
    for col in categorical_cols:
        if df_encoded[col].nunique() > 1:  # Only encode if there are multiple categories
            df_encoded[col] = encoder.fit_transform(df_encoded[col].astype(str))
            logger.debug(f"Categorical recoding for {col}: {df_encoded[col].nunique()} unique values")
    
    logger.info(f"Categorical recoding completed: {len(categorical_cols)} columns encoded")
    return df_encoded

def main():
    """Main entry point for cleaning module."""
    logger.info("Cleaning module loaded")

if __name__ == "__main__":
    main()