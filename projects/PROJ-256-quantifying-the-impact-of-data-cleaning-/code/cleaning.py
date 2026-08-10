"""
Cleaning strategies for datasets.
Functions return either a cleaned DataFrame or a tuple (cleaned_df, metadata)
depending on the contract required by downstream code and tests.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger("cleaning")

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """
    Remove rows that are outliers based on the IQR method.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    k : float, optional
        Multiplier for the IQR, by default 1.5.

    Returns
    -------
    pd.DataFrame
        Dataframe with outliers removed.
    """
    if df.empty:
        logger.warning("Received empty dataframe for outlier removal.")
        return df

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        logger.warning("No numeric columns found for outlier detection.")
        return df

    Q1 = df[numeric_cols].quantile(0.25)
    Q3 = df[numeric_cols].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - k * IQR
    upper_bound = Q3 + k * IQR

    mask = ~((df[numeric_cols] < lower_bound) | (df[numeric_cols] > upper_bound)).any(axis=1)
    rows_removed = df.shape[0] - mask.sum()
    logger.info(f"IQR outlier removal: removed {rows_removed} rows.")

    if rows_removed >= df.shape[0] * 0.5:
        logger.warning(
            f"Removed >=50% rows ({rows_removed}/{df.shape[0]}). Potential bias introduced."
        )

    return df[mask]

def _impute_column(series: pd.Series, method: str) -> pd.Series:
    """Helper to impute a single column."""
    if method == "mean":
        fill_value = series.mean()
    elif method == "median":
        fill_value = series.median()
    else:
        raise ValueError(f"Unsupported imputation method: {method}")
    return series.fillna(fill_value)

def _log_variance_reduction(original: pd.Series, imputed: pd.Series, col_name: str) -> None:
    """Log a warning if variance reduction >= 20%."""
    if original.var(ddof=1) == 0:
        return
    reduction = (original.var(ddof=1) - imputed.var(ddof=1)) / original.var(ddof=1)
    if reduction >= 0.20:
        logger.warning(
            f"Variance reduction >= 20% for column '{col_name}' after imputation."
        )

def apply_mean_imputation(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Impute missing values in specified columns using the mean.
    """
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column '{col}' not found for mean imputation.")
            continue
        original = df[col]
        df[col] = _impute_column(df[col], "mean")
        _log_variance_reduction(original, df[col], col)
    return df

def apply_median_imputation(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Impute missing values in specified columns using the median.
    Returns the DataFrame directly (as required by existing tests).
    """
    if not columns:
        # No columns specified – return original dataframe unchanged.
        logger.info("apply_median_imputation called with empty column list; returning original df.")
        return df

    df = df.copy()
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column '{col}' not found for median imputation.")
            continue
        original = df[col]
        df[col] = _impute_column(df[col], "median")
        _log_variance_reduction(original, df[col], col)
    return df

def apply_knn_imputation(df: pd.DataFrame, columns: List[str], k: int = 5) -> pd.DataFrame:
    """
    Impute missing values using K-Nearest Neighbors.
    """
    if not columns:
        logger.info("apply_knn_imputation called with empty column list; returning original df.")
        return df

    imputer = KNNImputer(n_neighbors=k)
    df_subset = df[columns]
    imputed_array = imputer.fit_transform(df_subset)
    df[columns] = imputed_array

    # Simple variance check across all imputed columns
    for col in columns:
        original = df_subset[col]
        imputed = df[col]
        _log_variance_reduction(original, imputed, col)

    return df

def apply_categorical_recoding(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Encode categorical columns as integer factors.

    Returns
    -------
    tuple
        (cleaned_df, metadata_dict) where metadata_dict contains:
        - ``recoded_columns``: list of column names that were encoded.
        - ``rows_processed``: number of rows in the dataframe.
    """
    df = df.copy()
    metadata: Dict[str, Any] = {
        "recoded_columns": [],
        "rows_processed": len(df),
    }

    # Identify categorical columns (object or category dtype)
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    for col in cat_cols:
        le = LabelEncoder()
        # Fill NaNs with a placeholder string to allow encoding
        df[col] = df[col].astype(str).fillna("missing")
        df[col] = le.fit_transform(df[col])
        metadata["recoded_columns"].append(col)

    return df, metadata

def main() -> None:
    """
    Entry point for cleaning module – placeholder for potential CLI use.
    """
    logger.info("Cleaning module executed as script, but no operation defined.")