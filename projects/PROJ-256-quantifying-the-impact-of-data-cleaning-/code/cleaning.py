import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Remove outliers based on IQR method.
    Returns (cleaned_df, metadata)
    """
    original_len = len(df)
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    mask = pd.Series(True, index=df.index)
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        mask &= (df[col] >= lower_bound) & (df[col] <= upper_bound)

    cleaned_df = df[mask].reset_index(drop=True)
    rows_removed = original_len - len(cleaned_df)

    metadata = {
        "rows_removed": rows_removed,
        "missing_values_remaining": cleaned_df.isnull().sum().sum(),
        "strategy": "iqr_outlier_removal",
        "k": k
    }

    if rows_removed >= 0.5 * original_len:
        logger.warning(f"Removed {rows_removed} rows ({100*rows_removed/original_len:.1f}%) via IQR. Potential bias.")

    return cleaned_df, metadata

def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing values with mean.
    Returns (cleaned_df, metadata)
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()

    cleaned_df = df.copy()
    for col in columns:
        if col in cleaned_df.columns:
            mean_val = cleaned_df[col].mean()
            cleaned_df[col].fillna(mean_val, inplace=True)

    missing_remaining = cleaned_df.isnull().sum().sum()
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": missing_remaining,
        "strategy": "mean_imputation",
        "columns_imputed": columns
    }
    return cleaned_df, metadata

def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing values with median.
    Returns (cleaned_df, metadata)
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()

    cleaned_df = df.copy()
    for col in columns:
        if col in cleaned_df.columns:
            median_val = cleaned_df[col].median()
            cleaned_df[col].fillna(median_val, inplace=True)

    missing_remaining = cleaned_df.isnull().sum().sum()
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": missing_remaining,
        "strategy": "median_imputation",
        "columns_imputed": columns
    }
    return cleaned_df, metadata

def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing values using KNN.
    Returns (cleaned_df, metadata)
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()

    if not columns:
        return df, {"rows_removed": 0, "missing_values_remaining": 0, "strategy": "knn_imputation"}

    cleaned_df = df.copy()
    # KNNImputer requires numeric data
    imputer = KNNImputer(n_neighbors=k)
    cleaned_df[columns] = imputer.fit_transform(cleaned_df[columns])

    missing_remaining = cleaned_df.isnull().sum().sum()
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": missing_remaining,
        "strategy": "knn_imputation",
        "k": k
    }
    return cleaned_df, metadata

def apply_categorical_recoding(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Encode categorical columns using LabelEncoder.
    Returns (cleaned_df, metadata)
    """
    cleaned_df = df.copy()
    categorical_cols = cleaned_df.select_dtypes(include=['object', 'category']).columns
    encoders = {}

    for col in categorical_cols:
        le = LabelEncoder()
        # Handle NaNs by filling with a placeholder or ignoring
        if cleaned_df[col].isnull().any():
            cleaned_df[col] = cleaned_df[col].astype(str).fillna("MISSING")
        cleaned_df[col] = le.fit_transform(cleaned_df[col])
        encoders[col] = le

    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": cleaned_df.isnull().sum().sum(),
        "strategy": "categorical_recoding",
        "encoded_columns": list(categorical_cols)
    }
    return cleaned_df, metadata

def main():
    # Placeholder for direct execution
    pass

if __name__ == "__main__":
    main()
