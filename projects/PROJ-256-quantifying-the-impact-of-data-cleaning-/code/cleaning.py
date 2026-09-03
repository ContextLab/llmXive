"""
cleaning.py
--------------

This module provides a suite of data cleaning utilities used throughout the
project pipeline.  All public cleaning functions now return a tuple:

    (cleaned_dataframe, metadata_dict)

where ``metadata_dict`` always contains the keys:

    * ``rows_removed`` – number of rows dropped from the original DataFrame
    * ``missing_values_remaining`` – total count of missing values after the
      cleaning operation has been applied

The change satisfies task **T1218** and enables downstream reporting steps to
capture detailed cleaning statistics.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

__all__ = [
    "apply_iqr_outlier_removal",
    "apply_mean_imputation",
    "apply_median_imputation",
    "apply_knn_imputation",
    "apply_categorical_recoding",
    "main",
]

###########################################################################
# Helper utilities
###########################################################################

def _count_missing(df: pd.DataFrame) -> int:
    """Return the total number of missing values in a DataFrame."""
    return int(df.isna().sum().sum())

def _numeric_columns(df: pd.DataFrame) -> List[str]:
    """Return a list of column names that have a numeric dtype."""
    return df.select_dtypes(include=[np.number]).columns.tolist()

###########################################################################
# Cleaning functions
###########################################################################

def apply_iqr_outlier_removal(
    df: pd.DataFrame, k: float = 1.5
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Remove rows that contain outliers according to the IQR rule.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    k : float, optional
        Multiplier for the inter‑quartile range.  Default is 1.5 (the classic
        Tukey rule).

    Returns
    -------
    cleaned_df : pd.DataFrame
        DataFrame with outlier rows removed.
    metadata : dict
        Dictionary containing ``rows_removed`` and ``missing_values_remaining``.
    """
    logger.debug("Applying IQR outlier removal (k=%.2f)", k)

    numeric_cols = _numeric_columns(df)
    if not numeric_cols:
        logger.info("No numeric columns found – returning original DataFrame.")
        return df.copy(), {"rows_removed": 0, "missing_values_remaining": _count_missing(df)}

    # Compute Q1, Q3, and IQR for each numeric column
    Q1 = df[numeric_cols].quantile(0.25)
    Q3 = df[numeric_cols].quantile(0.75)
    IQR = Q3 - Q1

    # Determine bounds
    lower_bound = Q1 - k * IQR
    upper_bound = Q3 + k * IQR

    # Build a boolean mask where **all** numeric columns are within bounds
    mask = pd.Series(True, index=df.index)
    for col in numeric_cols:
        mask &= df[col].between(lower_bound[col], upper_bound[col], inclusive="both")

    cleaned_df = df[mask].reset_index(drop=True)
    rows_removed = len(df) - len(cleaned_df)
    missing_after = _count_missing(cleaned_df)

    logger.info(
        "IQR outlier removal removed %d rows; %d missing values remain.",
        rows_removed,
        missing_after,
    )

    metadata = {
        "rows_removed": rows_removed,
        "missing_values_remaining": missing_after,
    }
    return cleaned_df, metadata

def apply_mean_imputation(
    df: pd.DataFrame, columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing values in ``columns`` with the column mean.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    columns : list of str, optional
        Columns to impute.  If ``None``, all numeric columns are considered.

    Returns
    -------
    cleaned_df : pd.DataFrame
        DataFrame with missing values imputed.
    metadata : dict
        Dictionary containing ``rows_removed`` (always 0) and
        ``missing_values_remaining`` (should be 0 after successful imputation).
    """
    logger.debug("Applying mean imputation on columns: %s", columns)

    df_imputed = df.copy()
    target_cols = columns or _numeric_columns(df_imputed)

    for col in target_cols:
        if df_imputed[col].isna().any():
            mean_val = df_imputed[col].mean()
            df_imputed[col].fillna(mean_val, inplace=True)
            logger.debug("Imputed column %s with mean=%.4f", col, mean_val)

    missing_after = _count_missing(df_imputed)
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": missing_after,
    }
    logger.info(
        "Mean imputation completed; %d missing values remain.", missing_after
    )
    return df_imputed, metadata

def apply_median_imputation(
    df: pd.DataFrame, columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing values in ``columns`` with the column median.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    columns : list of str, optional
        Columns to impute.  If ``None``, all numeric columns are considered.

    Returns
    -------
    cleaned_df : pd.DataFrame
        DataFrame with missing values imputed.
    metadata : dict
        Dictionary containing ``rows_removed`` (always 0) and
        ``missing_values_remaining`` (should be 0 after successful imputation).
    """
    logger.debug("Applying median imputation on columns: %s", columns)

    df_imputed = df.copy()
    target_cols = columns or _numeric_columns(df_imputed)

    for col in target_cols:
        if df_imputed[col].isna().any():
            median_val = df_imputed[col].median()
            df_imputed[col].fillna(median_val, inplace=True)
            logger.debug("Imputed column %s with median=%.4f", col, median_val)

    missing_after = _count_missing(df_imputed)
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": missing_after,
    }
    logger.info(
        "Median imputation completed; %d missing values remain.", missing_after
    )
    return df_imputed, metadata

def apply_knn_imputation(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    k: int = 5,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing values using k‑Nearest Neighbours.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    columns : list of str, optional
        Columns to impute.  If ``None``, all numeric columns are considered.
    k : int, optional
        Number of neighbours for KNN.  Default is 5.

    Returns
    -------
    cleaned_df : pd.DataFrame
        DataFrame with missing values imputed.
    metadata : dict
        Dictionary containing ``rows_removed`` (always 0) and
        ``missing_values_remaining`` (should be 0 after successful imputation).
    """
    logger.debug("Applying KNN imputation (k=%d) on columns: %s", k, columns)

    df_imputed = df.copy()
    target_cols = columns or _numeric_columns(df_imputed)

    if not target_cols:
        logger.info("No numeric columns to impute – returning original DataFrame.")
        return df_imputed, {
            "rows_removed": 0,
            "missing_values_remaining": _count_missing(df_imputed),
        }

    imputer = KNNImputer(n_neighbors=k)
    # Fit on the selected columns only
    imputed_array = imputer.fit_transform(df_imputed[target_cols])
    df_imputed[target_cols] = pd.DataFrame(
        imputed_array, columns=target_cols, index=df_imputed.index
    )

    missing_after = _count_missing(df_imputed)
    metadata = {
        "rows_removed": 0,
        "missing_values_remaining": missing_after,
    }
    logger.info(
        "KNN imputation completed; %d missing values remain.", missing_after
    )
    return df_imputed, metadata

def apply_categorical_recoding(
    df: pd.DataFrame,
    ordinal_threshold: int = 10,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Encode categorical variables.

    - Columns with ``<= ordinal_threshold`` distinct values are treated as
      *ordinal* and label‑encoded.
    - Columns with more distinct values are one‑hot encoded.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    ordinal_threshold : int, optional
        Maximum number of unique values for a column to be considered ordinal.
        Default is 10.

    Returns
    -------
    cleaned_df : pd.DataFrame
        DataFrame with categorical columns encoded.
    metadata : dict
        Dictionary containing ``rows_removed`` (always 0) and
        ``missing_values_remaining`` (should be 0 after encoding).
    """
    logger.debug(
        "Applying categorical recoding (ordinal threshold=%d).", ordinal_threshold
    )

    df_encoded = df.copy()
    cat_cols = df_encoded.select_dtypes(include=["object", "category"]).columns.tolist()
    rows_removed = 0  # recoding never drops rows

    for col in cat_cols:
        n_unique = df_encoded[col].nunique(dropna=False)
        if n_unique <= ordinal_threshold:
            # Ordinal – simple label encoding (treat NaN as a separate category)
            le = LabelEncoder()
            # Fill NaN with a placeholder string to keep shape
            fill_val = "__MISSING__"
            col_series = df_encoded[col].fillna(fill_val).astype(str)
            le.fit(col_series)
            df_encoded[col] = le.transform(col_series)
            logger.debug("Label‑encoded ordinal column %s (unique=%d).", col, n_unique)
        else:
            # Nominal – one‑hot encode
            dummies = pd.get_dummies(df_encoded[col], prefix=col, dummy_na=True)
            df_encoded = pd.concat([df_encoded.drop(columns=[col]), dummies], axis=1)
            logger.debug(
                "One‑hot encoded nominal column %s (unique=%d).", col, n_unique
            )

    missing_after = _count_missing(df_encoded)
    metadata = {
        "rows_removed": rows_removed,
        "missing_values_remaining": missing_after,
    }
    logger.info(
        "Categorical recoding completed; %d missing values remain.", missing_after
    )
    return df_encoded, metadata

###########################################################################
# CLI entry point (optional convenience)
###########################################################################

def main() -> None:
    """
    Simple command‑line interface for ad‑hoc cleaning.

    Example
    -------
    >>> python -m cleaning path/to/input.csv path/to/output.csv iqr
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run a single cleaning operation.")
    parser.add_argument("input_csv", help="Path to the input CSV file.")
    parser.add_argument("output_csv", help="Path where the cleaned CSV will be written.")
    parser.add_argument(
        "method",
        choices=["iqr", "mean", "median", "knn", "categorical"],
        help="Cleaning method to apply.",
    )
    parser.add_argument(
        "--columns",
        nargs="+",
        help="Columns to target (default: all numeric for numeric methods).",
    )
    parser.add_argument(
        "--k",
        type=float,
        default=1.5,
        help="Multiplier for IQR or number of neighbours for KNN.",
    )
    args = parser.parse_args()

    try:
        df = pd.read_csv(args.input_csv)
    except Exception as exc:
        logger.error("Failed to read input CSV: %s", exc)
        sys.exit(1)

    method_map = {
        "iqr": lambda d: apply_iqr_outlier_removal(d, k=args.k),
        "mean": lambda d: apply_mean_imputation(d, columns=args.columns),
        "median": lambda d: apply_median_imputation(d, columns=args.columns),
        "knn": lambda d: apply_knn_imputation(d, columns=args.columns, k=int(args.k)),
        "categorical": lambda d: apply_categorical_recoding(d),
    }

    try:
        cleaned_df, metadata = method_map[args.method](df)
    except Exception as exc:
        logger.error("Cleaning operation failed: %s", exc)
        sys.exit(1)

    try:
        cleaned_df.to_csv(args.output_csv, index=False)
        logger.info(
            "Cleaning completed. Metadata: %s. Output written to %s",
            metadata,
            args.output_csv,
        )
    except Exception as exc:
        logger.error("Failed to write output CSV: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()