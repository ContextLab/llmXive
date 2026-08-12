"""
Cleaning strategies for data preprocessing.

Implements IQR outlier removal, mean/median/KNN imputation, and categorical recoding.
All functions return a tuple: (cleaned_df, metadata_dict).
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

def apply_iqr_outlier_removal(df: pd.DataFrame, k: float = 1.5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Remove outliers based on the Interquartile Range (IQR) method.
    
    Args:
        df: Input DataFrame.
        k: Multiplier for IQR (default 1.5).
        
    Returns:
        Tuple of (cleaned DataFrame, metadata dict).
        Metadata includes:
            - rows_removed: int
            - missing_values_remaining: int
            - strategy: "iqr_outlier_removal"
            - k: float
    """
    logger.info(f"Applying IQR outlier removal with k={k}")
    
    if df.empty:
        logger.warning("Input DataFrame is empty.")
        return df.copy(), {
            "rows_removed": 0,
            "missing_values_remaining": 0,
            "strategy": "iqr_outlier_removal",
            "k": k
        }

    # Identify numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        logger.warning("No numeric columns found for IQR outlier removal.")
        return df.copy(), {
            "rows_removed": 0,
            "missing_values_remaining": df.isnull().sum().sum(),
            "strategy": "iqr_outlier_removal",
            "k": k
        }

    original_len = len(df)
    mask = pd.Series(True, index=df.index)
    
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        
        # Handle NaNs in bounds calculation
        if np.isnan(lower_bound) or np.isnan(upper_bound):
            continue
            
        col_mask = (df[col] >= lower_bound) & (df[col] <= upper_bound)
        mask &= col_mask
    
    cleaned_df = df[mask].reset_index(drop=True)
    rows_removed = original_len - len(cleaned_df)
    
    if rows_removed >= 0.5 * original_len and original_len > 0:
        logger.warning(f"High row removal rate: {rows_removed}/{original_len} ({100*rows_removed/original_len:.1f}%)")
    
    missing_remaining = cleaned_df.isnull().sum().sum()
    
    metadata = {
        "rows_removed": rows_removed,
        "missing_values_remaining": int(missing_remaining),
        "strategy": "iqr_outlier_removal",
        "k": k,
        "original_rows": original_len,
        "remaining_rows": len(cleaned_df)
    }
    
    logger.info(f"IQR removal complete: {rows_removed} rows removed. {missing_remaining} missing values remaining.")
    return cleaned_df, metadata

def apply_mean_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing values with the mean of the column.
    
    Args:
        df: Input DataFrame.
        columns: List of columns to impute. If None, all numeric columns are used.
        
    Returns:
        Tuple of (cleaned DataFrame, metadata dict).
    """
    logger.info("Applying mean imputation")
    
    if df.empty:
        return df.copy(), {
            "rows_removed": 0,
            "missing_values_remaining": 0,
            "strategy": "mean_imputation",
            "columns_imputed": []
        }

    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter to existing columns
    cols_to_impute = [c for c in columns if c in df.columns]
    
    if not cols_to_impute:
        logger.warning("No columns found for mean imputation.")
        return df.copy(), {
            "rows_removed": 0,
            "missing_values_remaining": int(df.isnull().sum().sum()),
            "strategy": "mean_imputation",
            "columns_imputed": []
        }

    original_missing = df[cols_to_impute].isnull().sum().sum()
    cleaned_df = df.copy()
    
    for col in cols_to_impute:
        mean_val = cleaned_df[col].mean()
        if np.isnan(mean_val):
            logger.warning(f"Mean of column '{col}' is NaN. Skipping imputation for this column.")
            continue
        cleaned_df[col] = cleaned_df[col].fillna(mean_val)
    
    missing_remaining = cleaned_df[cols_to_impute].isnull().sum().sum()
    
    # Check variance reduction
    variance_reduction = {}
    for col in cols_to_impute:
        if col in df.columns and df[col].var() > 0:
            new_var = cleaned_df[col].var()
            reduction = 1 - (new_var / df[col].var())
            if reduction >= 0.20:
                variance_reduction[col] = reduction
                logger.warning(f"Variance reduction in '{col}' is {reduction:.2%} (>= 20%)")

    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": int(missing_remaining),
        "strategy": "mean_imputation",
        "columns_imputed": cols_to_impute,
        "variance_reduction_alerts": variance_reduction
    }
    
    logger.info(f"Mean imputation complete. {int(original_missing - missing_remaining)} values imputed.")
    return cleaned_df, metadata

def apply_median_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing values with the median of the column.
    
    Args:
        df: Input DataFrame.
        columns: List of columns to impute. If None, all numeric columns are used.
        
    Returns:
        Tuple of (cleaned DataFrame, metadata dict).
    """
    logger.info("Applying median imputation")
    
    if df.empty:
        return df.copy(), {
            "rows_removed": 0,
            "missing_values_remaining": 0,
            "strategy": "median_imputation",
            "columns_imputed": []
        }

    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    cols_to_impute = [c for c in columns if c in df.columns]
    
    if not cols_to_impute:
        logger.warning("No columns found for median imputation.")
        return df.copy(), {
            "rows_removed": 0,
            "missing_values_remaining": int(df.isnull().sum().sum()),
            "strategy": "median_imputation",
            "columns_imputed": []
        }

    original_missing = df[cols_to_impute].isnull().sum().sum()
    cleaned_df = df.copy()
    
    for col in cols_to_impute:
        median_val = cleaned_df[col].median()
        if np.isnan(median_val):
            logger.warning(f"Median of column '{col}' is NaN. Skipping imputation for this column.")
            continue
        cleaned_df[col] = cleaned_df[col].fillna(median_val)
    
    missing_remaining = cleaned_df[cols_to_impute].isnull().sum().sum()
    
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": int(missing_remaining),
        "strategy": "median_imputation",
        "columns_imputed": cols_to_impute
    }
    
    logger.info(f"Median imputation complete. {int(original_missing - missing_remaining)} values imputed.")
    return cleaned_df, metadata

def apply_knn_imputation(df: pd.DataFrame, columns: Optional[List[str]] = None, k: int = 5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing values using K-Nearest Neighbors.
    
    Args:
        df: Input DataFrame.
        columns: List of columns to impute. If None, all numeric columns are used.
        k: Number of neighbors (default 5).
        
    Returns:
        Tuple of (cleaned DataFrame, metadata dict).
    """
    logger.info(f"Applying KNN imputation with k={k}")
    
    if df.empty:
        return df.copy(), {
            "rows_removed": 0,
            "missing_values_remaining": 0,
            "strategy": "knn_imputation",
            "columns_imputed": [],
            "k": k
        }

    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    cols_to_impute = [c for c in columns if c in df.columns]
    
    if not cols_to_impute:
        logger.warning("No numeric columns found for KNN imputation.")
        return df.copy(), {
            "rows_removed": 0,
            "missing_values_remaining": int(df.isnull().sum().sum()),
            "strategy": "knn_imputation",
            "columns_imputed": [],
            "k": k
        }

    # Check if any missing values exist
    if df[cols_to_impute].isnull().sum().sum() == 0:
        logger.info("No missing values found in specified columns.")
        return df.copy(), {
            "rows_removed": 0,
            "missing_values_remaining": 0,
            "strategy": "knn_imputation",
            "columns_imputed": cols_to_impute,
            "k": k
        }

    # Prepare data for KNNImputer
    imputer = KNNImputer(n_neighbors=k)
    try:
        imputed_array = imputer.fit_transform(df[cols_to_impute])
        cleaned_df = df.copy()
        cleaned_df[cols_to_impute] = imputed_array
    except Exception as e:
        logger.error(f"KNN imputation failed: {e}")
        raise

    missing_remaining = cleaned_df[cols_to_impute].isnull().sum().sum()
    
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": int(missing_remaining),
        "strategy": "knn_imputation",
        "columns_imputed": cols_to_impute,
        "k": k
    }
    
    logger.info(f"KNN imputation complete. Missing values remaining: {missing_remaining}.")
    return cleaned_df, metadata

def apply_categorical_recoding(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Apply label encoding to categorical columns.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Tuple of (cleaned DataFrame, metadata dict).
    """
    logger.info("Applying categorical recoding (label encoding)")
    
    if df.empty:
        return df.copy(), {
            "rows_removed": 0,
            "missing_values_remaining": 0,
            "strategy": "categorical_recoding",
            "columns_encoded": []
        }

    # Identify categorical columns (object or category dtype)
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if not cat_cols:
        logger.info("No categorical columns found for recoding.")
        return df.copy(), {
            "rows_removed": 0,
            "missing_values_remaining": int(df.isnull().sum().sum()),
            "strategy": "categorical_recoding",
            "columns_encoded": []
        }

    cleaned_df = df.copy()
    encoded_cols = []
    label_encoders = {}
    
    for col in cat_cols:
        if cleaned_df[col].isnull().any():
            # Fill NaN with a placeholder for encoding, then handle later if needed
            # For now, we'll use 'Missing' as a category
            cleaned_df[col] = cleaned_df[col].fillna('Missing')
        
        le = LabelEncoder()
        try:
            cleaned_df[col] = le.fit_transform(cleaned_df[col].astype(str))
            encoded_cols.append(col)
            label_encoders[col] = le.classes_.tolist()
        except Exception as e:
            logger.warning(f"Failed to encode column '{col}': {e}")
    
    missing_remaining = cleaned_df.isnull().sum().sum()
    
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": int(missing_remaining),
        "strategy": "categorical_recoding",
        "columns_encoded": encoded_cols,
        "label_encoders": label_encoders
    }
    
    logger.info(f"Categorical recoding complete. {len(encoded_cols)} columns encoded.")
    return cleaned_df, metadata

def main():
    """Main entry point for cleaning module (for testing)."""
    import sys
    import json
    
    # Create a dummy dataset for testing
    data = {
        'A': [1.0, 2.0, np.nan, 4.0, 100.0],
        'B': ['cat', 'dog', 'cat', np.nan, 'bird'],
        'C': [10, 20, 30, 40, 50]
    }
    df = pd.DataFrame(data)
    
    print("Original DataFrame:")
    print(df)
    print("\n" + "="*40 + "\n")
    
    # Test IQR
    df_iqr, meta_iqr = apply_iqr_outlier_removal(df, k=1.5)
    print("IQR Metadata:", json.dumps(meta_iqr, indent=2))
    print("IQR Result:\n", df_iqr)
    print("\n" + "="*40 + "\n")
    
    # Test Mean Imputation
    df_mean, meta_mean = apply_mean_imputation(df, columns=['A'])
    print("Mean Imputation Metadata:", json.dumps(meta_mean, indent=2))
    print("Mean Result:\n", df_mean)
    print("\n" + "="*40 + "\n")
    
    # Test Categorical Recoding
    df_cat, meta_cat = apply_categorical_recoding(df)
    print("Categorical Metadata:", json.dumps(meta_cat, indent=2))
    print("Categorical Result:\n", df_cat)

if __name__ == "__main__":
    main()