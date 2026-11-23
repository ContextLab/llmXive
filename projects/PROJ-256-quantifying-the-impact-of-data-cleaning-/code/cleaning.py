"""
Cleaning strategies implementation.
Returns (cleaned_df, metadata_dict) for all functions.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Remove outliers using IQR method.
    Returns (cleaned_df, metadata_dict).
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    df_clean = df.copy()
    rows_removed = 0
    total_rows = len(df_clean)
    
    mask = pd.Series([True] * len(df_clean), index=df_clean.index)
    
    for col in columns:
        if col not in df_clean.columns:
            continue
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        col_mask = (df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)
        mask = mask & col_mask
    
    rows_removed = total_rows - mask.sum()
    df_clean = df_clean[mask]
    
    metadata = {
        "rows_removed": int(rows_removed),
        "missing_values_remaining": int(df_clean.isna().sum().sum()),
        "strategy": "iqr_outlier_removal",
        "k": k
    }
    
    if rows_removed > 0:
        logger.info(f"Removed {rows_removed} rows ({100*rows_removed/total_rows:.2f}%) via IQR outlier removal")
        if rows_removed >= 0.5 * total_rows:
            logger.warning(f"High row removal rate ({100*rows_removed/total_rows:.2f}%) for IQR outlier removal")
    
    return df_clean, metadata

def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing values with mean.
    Returns (cleaned_df, metadata_dict).
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    df_clean = df.copy()
    original_missing = df_clean.isna().sum().sum()
    
    for col in columns:
        if col in df_clean.columns and df_clean[col].isna().any():
            mean_val = df_clean[col].mean()
            df_clean[col] = df_clean[col].fillna(mean_val)
    
    remaining_missing = df_clean.isna().sum().sum()
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": int(remaining_missing),
        "strategy": "mean_imputation",
        "original_missing": int(original_missing)
    }
    
    return df_clean, metadata

def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing values with median.
    Returns (cleaned_df, metadata_dict).
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    df_clean = df.copy()
    original_missing = df_clean.isna().sum().sum()
    
    for col in columns:
        if col in df_clean.columns and df_clean[col].isna().any():
            median_val = df_clean[col].median()
            df_clean[col] = df_clean[col].fillna(median_val)
    
    remaining_missing = df_clean.isna().sum().sum()
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": int(remaining_missing),
        "strategy": "median_imputation",
        "original_missing": int(original_missing)
    }
    
    return df_clean, metadata

def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing values using KNN.
    Returns (cleaned_df, metadata_dict).
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not columns:
        return df, {"rows_removed": 0, "missing_values_remaining": 0, "strategy": "knn_imputation"}
    
    df_clean = df.copy()
    original_missing = df_clean[columns].isna().sum().sum()
    
    # Only impute numeric columns
    imputer = KNNImputer(n_neighbors=k)
    try:
        df_clean[columns] = imputer.fit_transform(df_clean[columns])
    except Exception as e:
        logger.warning(f"KNN Imputation failed for columns {columns}: {e}. Skipping.")
        return df_clean, {"rows_removed": 0, "missing_values_remaining": int(df_clean.isna().sum().sum()), "strategy": "knn_imputation"}
    
    remaining_missing = df_clean.isna().sum().sum()
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": int(remaining_missing),
        "strategy": "knn_imputation",
        "k": k,
        "original_missing": int(original_missing)
    }
    
    return df_clean, metadata

def apply_categorical_recoding(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Recode categorical variables.
    Nominal (<=10 categories) -> one-hot
    Ordinal/Large (>10 categories) -> integer label encoding
    Returns (cleaned_df, metadata_dict).
    """
    df_clean = df.copy()
    encoded_cols = []
    
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object' or (df_clean[col].dtype.name == 'category'):
            unique_count = df_clean[col].nunique()
            if unique_count <= 10:
                # One-hot encode
                dummies = pd.get_dummies(df_clean[col], prefix=col, drop_first=False)
                df_clean = pd.concat([df_clean.drop(columns=[col]), dummies], axis=1)
                encoded_cols.append((col, "one-hot"))
            else:
                # Label encode
                le = LabelEncoder()
                df_clean[col] = le.fit_transform(df_clean[col].astype(str))
                encoded_cols.append((col, "label"))
    
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": int(df_clean.isna().sum().sum()),
        "strategy": "categorical_recoding",
        "encoded_columns": encoded_cols
    }
    
    return df_clean, metadata

def run_cleaning_pipeline(df: pd.DataFrame, strategies: List[Dict[str, Any]]) -> Dict[str, Tuple[pd.DataFrame, Dict[str, Any]]]:
    """
    Run a sequence of cleaning strategies and return results for each.
    """
    results = {}
    for strat in strategies:
        func = strat["func"]
        kwargs = strat.get("kwargs", {})
        name = strat.get("name", func.__name__)
        
        logger.info(f"Running {name}...")
        try:
            cleaned_df, metadata = func(df, **kwargs)
            results[name] = (cleaned_df, metadata)
        except Exception as e:
            logger.error(f"Failed to run {name}: {e}")
            results[name] = (df, {"error": str(e), "rows_removed": 0, "missing_values_remaining": 0})
    
    return results
