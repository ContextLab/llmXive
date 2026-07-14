import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Remove outliers based on IQR method.
    Rows where any specified column has a value outside [Q1 - k*IQR, Q3 + k*IQR] are removed.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    df_cleaned = df.copy()
    rows_removed = 0
    
    for col in columns:
        if col not in df_cleaned.columns:
            continue
        
        if not np.issubdtype(df_cleaned[col].dtype, np.number):
            continue
        
        q1 = df_cleaned[col].quantile(0.25)
        q3 = df_cleaned[col].quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - k * iqr
        upper_bound = q3 + k * iqr
        
        mask = (df_cleaned[col] >= lower_bound) & (df_cleaned[col] <= upper_bound)
        df_cleaned = df_cleaned[mask]
    
    rows_removed = len(df) - len(df_cleaned)
    logger.info(f"IQR outlier removal (k={k}): {rows_removed} rows removed from {len(df)}")
    
    if rows_removed >= len(df) * 0.5:
        logger.warning(f"WARNING: >=50% rows removed ({rows_removed}/{len(df)}). Potential bias introduced.")
    
    return df_cleaned

def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Replace missing values with column mean."""
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    df_imputed = df.copy()
    for col in columns:
        if col in df_imputed.columns:
            mean_val = df_imputed[col].mean()
            df_imputed[col] = df_imputed[col].fillna(mean_val)
    
    missing_count = df_imputed[columns].isnull().sum().sum()
    logger.info(f"Mean imputation: {missing_count} missing values remaining")
    
    return df_imputed

def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Replace missing values with column median."""
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    df_imputed = df.copy()
    for col in columns:
        if col in df_imputed.columns:
            median_val = df_imputed[col].median()
            df_imputed[col] = df_imputed[col].fillna(median_val)
    
    missing_count = df_imputed[columns].isnull().sum().sum()
    logger.info(f"Median imputation: {missing_count} missing values remaining")
    
    return df_imputed

def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> pd.DataFrame:
    """Replace missing values using KNN imputation."""
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not columns:
        logger.warning("No numerical columns found for KNN imputation")
        return df
    
    df_imputed = df.copy()
    subset = df_imputed[columns]
    
    if subset.isnull().sum().sum() == 0:
        logger.info("No missing values to impute")
        return df_imputed
    
    imputer = KNNImputer(n_neighbors=k)
    imputed_values = imputer.fit_transform(subset)
    
    for i, col in enumerate(columns):
        df_imputed[col] = imputed_values[:, i]
    
    missing_count = df_imputed[columns].isnull().sum().sum()
    logger.info(f"KNN imputation (k={k}): {missing_count} missing values remaining")
    
    return df_imputed

def apply_categorical_recoding(df: pd.DataFrame) -> pd.DataFrame:
    """Convert categorical columns to numerical using label encoding."""
    df_encoded = df.copy()
    categorical_cols = df_encoded.select_dtypes(include=['object', 'category']).columns.tolist()
    
    encoder = LabelEncoder()
    for col in categorical_cols:
        df_encoded[col] = encoder.fit_transform(df_encoded[col].astype(str))
        logger.info(f"Encoded categorical column: {col} ({df_encoded[col].nunique()} unique values)")
    
    return df_encoded

def main():
    """Main entry point for testing."""
    logger.info("Testing cleaning functions")
    df = pd.DataFrame({
        'A': [1, 2, np.nan, 4, 5, 100],
        'B': ['x', 'y', 'x', 'y', 'x', 'y'],
        'C': [10, 20, 30, 40, 50, 60]
    })
    
    df_clean = apply_iqr_outlier_removal(df, k=1.5)
    logger.info(f"Original: {len(df)} rows, Cleaned: {len(df_clean)} rows")

if __name__ == "__main__":
    main()
