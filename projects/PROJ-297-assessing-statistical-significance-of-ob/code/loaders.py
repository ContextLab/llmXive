"""
Data loading and hygiene utilities for UCI dataset ingestion.

This module handles fetching datasets from the UCI repository,
parsing CSVs, and applying data hygiene rules:
- Dropping rows with missing values
- Detecting and excluding constant variables
- Filtering datasets that do not meet the minimum continuous variable threshold (>=20)
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import requests
from io import StringIO
import os

from code.config import DATA_RAW_DIR, DATA_PROCESSED_DIR, MIN_CONTINUOUS_VARS


def fetch_uci_dataset(dataset_url: str) -> pd.DataFrame:
    """
    Fetch a dataset from a UCI repository URL.

    Args:
        dataset_url (str): The direct URL to the CSV data file.

    Returns:
        pd.DataFrame: The loaded dataset.

    Raises:
        ValueError: If the URL is invalid or the request fails.
        FileNotFoundError: If the dataset cannot be retrieved (Constitution VII compliance).
    """
    try:
        response = requests.get(dataset_url, timeout=30)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))
    except requests.exceptions.RequestException as e:
        raise FileNotFoundError(f"Failed to download dataset from {dataset_url}: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing dataset from {dataset_url}: {e}")


def load_dataset_from_path(file_path: str) -> pd.DataFrame:
    """
    Load a dataset from a local file path.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: The loaded dataset.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found at {file_path}")
    return pd.read_csv(file_path)


def drop_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows containing any missing (NaN) values.

    Args:
        df (pd.DataFrame): Input dataframe.

    Returns:
        pd.DataFrame: Cleaned dataframe with no missing values.
    """
    initial_count = len(df)
    cleaned_df = df.dropna()
    final_count = len(cleaned_df)
    if initial_count != final_count:
        print(f"Dropped {initial_count - final_count} rows with missing values.")
    return cleaned_df


def detect_constant_variables(df: pd.DataFrame) -> List[str]:
    """
    Detect columns that have zero variance (constant values).

    Args:
        df (pd.DataFrame): Input dataframe.

    Returns:
        List[str]: List of column names that are constant.
    """
    constant_cols = []
    for col in df.columns:
        if df[col].nunique() <= 1:
            constant_cols.append(col)
    return constant_cols


def exclude_constant_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove columns that have zero variance.

    Args:
        df (pd.DataFrame): Input dataframe.

    Returns:
        pd.DataFrame: Dataframe with constant columns removed.
    """
    constant_cols = detect_constant_variables(df)
    if constant_cols:
        print(f"Excluding constant variables: {constant_cols}")
        return df.drop(columns=constant_cols)
    return df


def filter_continuous_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataframe to keep only continuous (numeric) variables.

    Args:
        df (pd.DataFrame): Input dataframe.

    Returns:
        pd.DataFrame: Dataframe containing only numeric columns.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    return numeric_df


def validate_dataset_dimensions(df: pd.DataFrame, min_vars: int = MIN_CONTINUOUS_VARS) -> bool:
    """
    Validate that the dataset has at least the minimum number of continuous variables.

    Args:
        df (pd.DataFrame): Input dataframe (assumed to be already filtered for numeric).
        min_vars (int): Minimum required continuous variables.

    Returns:
        bool: True if valid, False otherwise.
    """
    if len(df.columns) < min_vars:
        return False
    return True


def apply_hygiene_pipeline(
    df: pd.DataFrame,
    min_vars: int = MIN_CONTINUOUS_VARS
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Apply the full data hygiene pipeline:
    1. Drop rows with missing values.
    2. Filter to continuous variables only.
    3. Exclude constant variables.
    4. Validate the number of continuous variables.

    Args:
        df (pd.DataFrame): Raw input dataframe.
        min_vars (int): Minimum required continuous variables (default from config).

    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: Cleaned dataframe and a metadata dictionary
            describing the hygiene operations performed.

    Raises:
        ValueError: If the dataset fails the minimum variable requirement.
    """
    metadata = {
        "initial_shape": df.shape,
        "missing_dropped": 0,
        "constant_removed": [],
        "final_shape": None,
        "valid": True
    }

    # Step 1: Drop missing values
    df_clean = drop_missing_values(df)
    metadata["missing_dropped"] = df.shape[0] - df_clean.shape[0]

    # Step 2: Filter to numeric only
    df_numeric = filter_continuous_variables(df_clean)
    metadata["numeric_cols_count"] = len(df_numeric.columns)

    # Step 3: Exclude constant variables
    df_no_const = exclude_constant_variables(df_numeric)
    constant_cols = detect_constant_variables(df_numeric)
    metadata["constant_removed"] = constant_cols

    # Step 4: Validate dimensions
    if not validate_dataset_dimensions(df_no_const, min_vars):
        metadata["valid"] = False
        raise ValueError(
            f"Dataset validation failed: only {len(df_no_const.columns)} continuous variables "
            f"found. Minimum required: {min_vars}."
        )

    metadata["final_shape"] = df_no_const.shape
    return df_no_const, metadata


def load_and_hygiene_dataset(
    source: str,
    is_url: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load a dataset from a URL or local path and apply the hygiene pipeline.

    Args:
        source (str): URL or file path.
        is_url (bool): True if source is a URL, False if local path.

    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: Cleaned dataframe and metadata.
    """
    if is_url:
        df = fetch_uci_dataset(source)
    else:
        df = load_dataset_from_path(source)

    return apply_hygiene_pipeline(df)