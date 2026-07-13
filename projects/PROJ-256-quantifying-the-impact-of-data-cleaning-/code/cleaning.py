import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers using IQR method.
    Rows with values outside [Q1 - k*IQR, Q3 + k*IQR] are removed.
    """
    df_clean = df.copy()
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        logger.warning("No numeric columns found for outlier removal")
        return df_clean
    
    rows_removed = 0
    for col in numeric_cols:
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        
        mask = (df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)
        df_clean = df_clean[mask]
    
    original_rows = len(df)
    rows_removed = original_rows - len(df_clean)
    
    if rows_removed > 0:
        logger.info(f"Removed {rows_removed} rows ({100*rows_removed/original_rows:.1f}%) using IQR (k={k})")
        if rows_removed >= 0.5 * original_rows:
            logger.warning(f"Removed >= 50% of rows. Potential bias introduced.")
    
    return df_clean

def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Fill missing values with column mean.
    """
    df_filled = df.copy()
    
    if columns is None:
        columns = df_filled.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col in df_filled.columns and df_filled[col].isna().any():
            mean_val = df_filled[col].mean()
            df_filled[col] = df_filled[col].fillna(mean_val)
            logger.debug(f"Filled {df_filled[col].isna().sum()} missing values in {col} with mean")
    
    # Validate zero missing
    if df_filled.isna().any().any():
        logger.warning("Some missing values remain after mean imputation")
    
    return df_filled

def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Fill missing values with column median.
    """
    df_filled = df.copy()
    
    if columns is None:
        columns = df_filled.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in columns:
        if col in df_filled.columns and df_filled[col].isna().any():
            median_val = df_filled[col].median()
            df_filled[col] = df_filled[col].fillna(median_val)
            logger.debug(f"Filled {df_filled[col].isna().sum()} missing values in {col} with median")
    
    # Validate zero missing
    if df_filled.isna().any().any():
        logger.warning("Some missing values remain after median imputation")
    
    return df_filled

def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> pd.DataFrame:
    """
    Fill missing values using KNN imputer.
    """
    df_filled = df.copy()
    
    if columns is None:
        columns = df_filled.select_dtypes(include=[np.number]).columns.tolist()
    
    if not columns:
        logger.warning("No numeric columns for KNN imputation")
        return df_filled
    
    # Extract only numeric columns with missing values
    cols_with_na = [c for c in columns if df_filled[c].isna().any()]
    if not cols_with_na:
        return df_filled
    
    imputer = KNNImputer(n_neighbors=min(k, len(df_filled)))
    df_filled[cols_with_na] = imputer.fit_transform(df_filled[cols_with_na])
    
    # Validate zero missing
    if df_filled.isna().any().any():
        logger.warning("Some missing values remain after KNN imputation")
    
    return df_filled

def apply_categorical_recoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert categorical columns to numeric using label encoding.
    """
    df_encoded = df.copy()
    categorical_cols = df_encoded.select_dtypes(include=['object', 'category']).columns.tolist()
    
    encoder = LabelEncoder()
    for col in categorical_cols:
        if df_encoded[col].nunique() > 1:  # Only encode if more than one category
            df_encoded[col] = encoder.fit_transform(df_encoded[col].astype(str))
            logger.debug(f"Encoded categorical column: {col}")
    
    return df_encoded

def main():
    """Main entry point for cleaning module."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Cleaning module loaded")

if __name__ == "__main__":
    main()