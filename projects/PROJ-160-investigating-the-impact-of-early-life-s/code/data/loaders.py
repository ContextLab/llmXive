"""
Data loading utilities for ABCD Study data.
Handles CSV/TSV parsing with robust error handling and type inference.
"""
import csv
import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

import pandas as pd
import numpy as np

from code.config import DATA_RAW_DIR, DATA_PROCESSED_DIR


def load_csv(
    file_path: Union[str, Path],
    delimiter: str = ',',
    low_memory: bool = False,
    dtype: Optional[Dict[str, Any]] = None,
    na_values: Optional[List[str]] = None,
    usecols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame with robust error handling.

    Args:
        file_path: Path to the CSV file.
        delimiter: Field delimiter character (default: ',').
        low_memory: If True, reads file in chunks to save memory (default: False).
        dtype: Dictionary specifying data types for columns.
        na_values: List of additional strings to recognize as NA/NaN.
        usecols: List of column names to load (subset).

    Returns:
        pd.DataFrame: Loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
        Exception: For other I/O or parsing errors.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Data file is empty: {path}")

    try:
        df = pd.read_csv(
            path,
            delimiter=delimiter,
            low_memory=low_memory,
            dtype=dtype,
            na_values=na_values,
            usecols=usecols,
            keep_default_na=True,
            on_bad_lines='warn'
        )

        if df.empty:
            raise ValueError(f"Data file produced an empty DataFrame: {path}")

        return df

    except csv.Error as e:
        raise ValueError(f"CSV parsing error in {path}: {e}")
    except Exception as e:
        raise Exception(f"Failed to load CSV {path}: {e}")


def load_tsv(
    file_path: Union[str, Path],
    low_memory: bool = False,
    dtype: Optional[Dict[str, Any]] = None,
    na_values: Optional[List[str]] = None,
    usecols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load a TSV file into a pandas DataFrame.

    Args:
        file_path: Path to the TSV file.
        low_memory: If True, reads file in chunks to save memory.
        dtype: Dictionary specifying data types for columns.
        na_values: List of additional strings to recognize as NA/NaN.
        usecols: List of column names to load (subset).

    Returns:
        pd.DataFrame: Loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    return load_csv(
        file_path=file_path,
        delimiter='\t',
        low_memory=low_memory,
        dtype=dtype,
        na_values=na_values,
        usecols=usecols
    )


def load_abc_phenotypic(
    file_name: str = "phenotypic.csv"
) -> pd.DataFrame:
    """
    Load the ABCD phenotypic data file from the raw data directory.

    Args:
        file_name: Name of the phenotypic file (default: "phenotypic.csv").

    Returns:
        pd.DataFrame: Phenotypic data.
    """
    file_path = Path(DATA_RAW_DIR) / file_name
    return load_csv(file_path, na_values=['', 'NA', 'NaN', 'null'])


def load_subcortical_stats(
    file_name: str = "subcorticalSegmentationStats.csv"
) -> pd.DataFrame:
    """
    Load the ABCD subcortical segmentation statistics file.

    Args:
        file_name: Name of the stats file (default: "subcorticalSegmentationStats.csv").

    Returns:
        pd.DataFrame: Subcortical volume data.
    """
    file_path = Path(DATA_RAW_DIR) / file_name
    return load_csv(file_path, na_values=['', 'NA', 'NaN', 'null'])


def load_merged_dataset(
    phenotypic_path: Union[str, Path],
    segmentation_path: Union[str, Path],
    key_col: str = 'subjectkey',
    left_cols: Optional[List[str]] = None,
    right_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load and merge phenotypic and segmentation datasets.

    Args:
        phenotypic_path: Path to the phenotypic CSV/TSV.
        segmentation_path: Path to the segmentation CSV/TSV.
        key_col: The column name to join on (default: 'subjectkey').
        left_cols: List of columns to keep from the left dataframe.
        right_cols: List of columns to keep from the right dataframe.

    Returns:
        pd.DataFrame: Merged dataset.
    """
    df_left = load_csv(phenotypic_path)
    df_right = load_csv(segmentation_path)

    if left_cols:
        # Ensure key_col is kept
        if key_col not in left_cols:
            left_cols = [key_col] + left_cols
        df_left = df_left[[c for c in left_cols if c in df_left.columns]]

    if right_cols:
        if key_col not in right_cols:
            right_cols = [key_col] + right_cols
        df_right = df_right[[c for c in right_cols if c in df_right.columns]]

    if key_col not in df_left.columns or key_col not in df_right.columns:
        raise ValueError(f"Join key '{key_col}' not found in one or both datasets.")

    merged_df = pd.merge(
        df_left,
        df_right,
        on=key_col,
        how='inner'
    )

    return merged_df


def save_dataframe(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    index: bool = False,
    delimiter: str = ','
) -> None:
    """
    Save a DataFrame to a CSV or TSV file.

    Args:
        df: The DataFrame to save.
        output_path: Path to the output file.
        index: Whether to write row indices (default: False).
        delimiter: Delimiter character (default: ',' for CSV, '\t' for TSV).
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix.lower() == '.tsv':
        delimiter = '\t'

    df.to_csv(path, index=index, sep=delimiter)
    
    if not path.exists():
        raise IOError(f"Failed to write output file: {path}")